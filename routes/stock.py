"""
routes/stock.py
Control de stock de netbooks por carro.
Compara el inventario físico (escaneado) contra el sistema.
Incluye control masivo: subir Excel o Google Sheets con todos los números de serie.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from models import db, Carro, Netbook
from datetime import datetime

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')


@stock_bp.route('/')
@login_required
def index():
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    return render_template('stock/index.html', carros=carros)


@stock_bp.route('/relevar/<int:carro_id>', methods=['GET', 'POST'])
@login_required
def relevar(carro_id):
    """Pantalla de escaneo/ingreso de series para un carro."""
    carro = Carro.query.get_or_404(carro_id)

    if request.method == 'POST':
        series_raw = request.form.get('series_escaneadas', '')
        series_lista = [s.strip().upper() for s in series_raw.splitlines() if s.strip()]

        if not series_lista:
            flash('No ingresaste ningún número de serie.', 'danger')
            return redirect(url_for('stock.relevar', carro_id=carro_id))

        series_sistema = {nb.numero_serie.upper(): nb
                          for nb in carro.netbooks
                          if nb.numero_serie}

        series_escaneadas_set = set(series_lista)
        series_sistema_set    = set(series_sistema.keys())

        encontradas    = [series_sistema[s] for s in series_escaneadas_set & series_sistema_set]
        faltantes      = [series_sistema[s] for s in series_sistema_set - series_escaneadas_set]
        no_registradas = list(series_escaneadas_set - series_sistema_set)

        session['stock_resultado'] = {
            'carro_id':         carro_id,
            'carro_display':    carro.display,
            'fecha':            datetime.now().strftime('%d/%m/%Y %H:%M'),
            'total_sistema':    len(series_sistema_set),
            'total_escaneadas': len(series_escaneadas_set),
            'encontradas':      len(encontradas),
            'faltantes': [{
                'numero_interno': nb.numero_interno or '—',
                'numero_serie':   nb.numero_serie or '—',
                'alumno':         nb.alumno or '—',
                'estado':         nb.estado
            } for nb in faltantes],
            'no_registradas': no_registradas,
            'usuario':  current_user.nombre_completo,
        }

        return render_template('stock/resultado.html',
                               carro=carro,
                               encontradas=encontradas,
                               faltantes=faltantes,
                               no_registradas=no_registradas,
                               fecha=datetime.now().strftime('%d/%m/%Y %H:%M'),
                               usuario=current_user.nombre_completo)

    return render_template('stock/relevar.html', carro=carro)


@stock_bp.route('/pdf/<int:carro_id>')
@login_required
def pdf(carro_id):
    """Genera el PDF del último resultado de stock."""
    resultado = session.get('stock_resultado')

    if not resultado or resultado.get('carro_id') != carro_id:
        flash('No hay resultado de stock disponible. Realizá el relevamiento primero.', 'warning')
        return redirect(url_for('stock.relevar', carro_id=carro_id))

    from services.pdf_stock import pdf_control_stock
    carro = Carro.query.get_or_404(carro_id)
    return pdf_control_stock(carro, resultado)


# ─────────────────────────────────────────────────────────────────────────────
#  CONTROL MASIVO DE STOCK
# ─────────────────────────────────────────────────────────────────────────────

@stock_bp.route('/control-masivo', methods=['GET', 'POST'])
@login_required
def control_masivo():
    """
    Control masivo: el usuario sube un listado de números de serie
    (Excel directo, Google Sheets o texto manual) y el sistema compara
    contra TODAS las netbooks registradas en todos los carros.
    Genera dos listados: encontradas y no encontradas en el sistema.
    """
    if request.method == 'GET':
        return render_template('stock/control_masivo.html', resultado=None)

    metodo = request.form.get('metodo', 'excel')
    series_input = []

    # ── 1. Obtener las series según el método ──────────────────────────────
    if metodo == 'excel':
        archivo = request.files.get('archivo_excel')
        if not archivo or archivo.filename == '':
            flash('Seleccioná un archivo Excel.', 'danger')
            return redirect(url_for('stock.control_masivo'))
        try:
            import openpyxl
            from io import BytesIO as _BytesIO
            wb = openpyxl.load_workbook(_BytesIO(archivo.read()), data_only=True)
            ws = wb.active
            for row in ws.iter_rows(values_only=True):
                for cell in row:
                    val = str(cell).strip().upper() if cell is not None else ''
                    # Ignorar celdas vacías, "None" y cabeceras típicas
                    if val and val not in ('NONE', 'NÚMERO DE SERIE', 'N° SERIE',
                                           'NUMERO DE SERIE', 'SERIE', 'N°SERIE'):
                        series_input.append(val)
        except Exception as e:
            flash(f'Error al leer el archivo Excel: {e}', 'danger')
            return redirect(url_for('stock.control_masivo'))

    elif metodo == 'sheets':
        url_sheet   = request.form.get('url_sheet', '').strip()
        nombre_hoja = request.form.get('nombre_hoja', '').strip() or 'Hoja1'
        if not url_sheet:
            flash('Ingresá la URL de la planilla de Google Sheets.', 'danger')
            return redirect(url_for('stock.control_masivo'))
        try:
            from services.importar_drive import _get_service, _extraer_sheet_id, _leer_hoja
            sheet_id = _extraer_sheet_id(url_sheet)
            filas    = _leer_hoja(_get_service(), sheet_id, nombre_hoja)
            CABECERAS = {'NONE', 'NÚMERO DE SERIE', 'N° SERIE',
                         'NUMERO DE SERIE', 'SERIE', 'N°SERIE'}
            for fila in filas:
                for celda in fila:
                    val = str(celda).strip().upper() if celda else ''
                    if val and val not in CABECERAS:
                        series_input.append(val)
        except Exception as e:
            flash(f'Error al leer Google Sheets: {e}', 'danger')
            return redirect(url_for('stock.control_masivo'))

    elif metodo == 'manual':
        texto        = request.form.get('series_manuales', '')
        series_input = [s.strip().upper() for s in texto.splitlines() if s.strip()]

    else:
        flash('Método no válido.', 'danger')
        return redirect(url_for('stock.control_masivo'))

    if not series_input:
        flash('No se encontraron números de serie en el listado.', 'danger')
        return redirect(url_for('stock.control_masivo'))

    # Eliminar duplicados del listado conservando el orden original
    seen = set()
    series_unicas = []
    for s in series_input:
        if s not in seen:
            seen.add(s)
            series_unicas.append(s)

    # ── 2. Índice de TODAS las netbooks del sistema ────────────────────────
    todas_netbooks = Netbook.query.filter(
        Netbook.numero_serie != None,
        Netbook.numero_serie != ''
    ).all()
    indice_sistema = {nb.numero_serie.strip().upper(): nb for nb in todas_netbooks}

    series_sistema_set = set(indice_sistema.keys())
    series_listado_set = set(series_unicas)

    # Encontradas: en el listado Y en el sistema
    encontradas_series    = series_listado_set & series_sistema_set
    # No encontradas: en el listado pero NO en el sistema
    no_encontradas_series = series_listado_set - series_sistema_set
    # En el sistema pero ausentes del listado (faltantes del relevamiento)
    no_en_listado_series  = series_sistema_set - series_listado_set

    # ── 3. Armar listas con datos completos ───────────────────────────────
    def _nb_dict(nb):
        return {
            'numero_serie':   nb.numero_serie,
            'numero_interno': nb.numero_interno or '—',
            'carro':          nb.carro.display if nb.carro else '—',
            'aula':           nb.carro.aula if nb.carro else '—',
            'alumno':         nb.alumno or '—',
            'estado':         nb.estado,
        }

    encontradas = sorted(
        [_nb_dict(indice_sistema[s]) for s in encontradas_series],
        key=lambda x: (x['carro'], x['numero_interno'])
    )

    no_encontradas = sorted(list(no_encontradas_series))

    no_en_listado = sorted(
        [_nb_dict(indice_sistema[s]) for s in no_en_listado_series],
        key=lambda x: (x['carro'], x['numero_interno'])
    )

    fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')

    # Guardar en session para PDF
    session['stock_masivo_resultado'] = {
        'fecha':          fecha_str,
        'usuario':        current_user.nombre_completo,
        'total_listado':  len(series_unicas),
        'total_sistema':  len(indice_sistema),
        'encontradas':    encontradas,
        'no_encontradas': no_encontradas,
        'no_en_listado':  no_en_listado,
    }

    return render_template('stock/control_masivo.html',
                           resultado=session['stock_masivo_resultado'],
                           fecha=fecha_str,
                           usuario=current_user.nombre_completo)


@stock_bp.route('/control-masivo/pdf')
@login_required
def control_masivo_pdf():
    """Genera el PDF del control masivo de stock."""
    resultado = session.get('stock_masivo_resultado')
    if not resultado:
        flash('No hay resultado disponible. Ejecutá el control masivo primero.', 'warning')
        return redirect(url_for('stock.control_masivo'))

    from services.pdf_reportes import pdf_control_masivo_stock
    return pdf_control_masivo_stock(resultado)
