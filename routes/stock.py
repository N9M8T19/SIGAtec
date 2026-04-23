"""
routes/stock.py
Control de stock de netbooks por carro.
Compara el inventario físico (escaneado) contra el sistema.
Incluye control masivo: subir Excel o Google Sheets con todos los números de serie.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from models import db, Carro, Netbook, AsignacionInterna
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

def _procesar_control_masivo(series_input):
    """
    Recibe una lista de strings (números de serie en mayúscula)
    y devuelve un dict con el resultado completo del control masivo.
    """
    # Eliminar duplicados conservando orden
    seen = set()
    series_unicas = []
    for s in series_input:
        if s not in seen:
            seen.add(s)
            series_unicas.append(s)

    # Índice de TODAS las netbooks del sistema (en carros)
    todas_netbooks = Netbook.query.filter(
        Netbook.numero_serie != None,
        Netbook.numero_serie != ''
    ).all()
    indice_sistema = {nb.numero_serie.strip().upper(): nb for nb in todas_netbooks}

    # Índice de asignaciones internas activas (netbooks fuera de carros)
    todas_asignaciones = AsignacionInterna.query.filter(
        AsignacionInterna.activa == True,
        AsignacionInterna.numero_serie != None,
        AsignacionInterna.numero_serie != ''
    ).all()
    indice_asignaciones = {a.numero_serie.strip().upper(): a for a in todas_asignaciones}

    # Índice unificado: carros + asignaciones internas
    indice_total = {}
    indice_total.update(indice_sistema)       # primero carros
    indice_total.update(indice_asignaciones)  # asignaciones sobreescriben si hay colisión de serie

    series_total_set   = set(indice_total.keys())
    series_listado_set = set(series_unicas)

    encontradas_series    = series_listado_set & series_total_set
    no_encontradas_series = series_listado_set - series_total_set
    no_en_listado_series  = series_total_set   - series_listado_set

    def _nb_dict(obj):
        """Convierte una Netbook o AsignacionInterna a dict uniforme."""
        if isinstance(obj, Netbook):
            return {
                'numero_serie':   obj.numero_serie,
                'numero_interno': obj.numero_interno or '—',
                'carro':          obj.carro.display if obj.carro else '—',
                'aula':           obj.carro.aula if obj.carro else '—',
                'alumno':         obj.alumno or '—',
                'estado':         obj.estado,
            }
        else:  # AsignacionInterna
            return {
                'numero_serie':   obj.numero_serie,
                'numero_interno': obj.numero_interno or '—',
                'carro':          'Asignación interna',
                'aula':           obj.destinatario,
                'alumno':         obj.modelo or '—',
                'estado':         'asignada',
            }

    encontradas = sorted(
        [_nb_dict(indice_total[s]) for s in encontradas_series],
        key=lambda x: (x['carro'], x['numero_interno'])
    )
    no_encontradas = sorted(list(no_encontradas_series))
    no_en_listado  = sorted(
        [_nb_dict(indice_total[s]) for s in no_en_listado_series],
        key=lambda x: (x['carro'], x['numero_interno'])
    )

    return {
        'fecha':          datetime.now().strftime('%d/%m/%Y %H:%M'),
        'usuario':        current_user.nombre_completo,
        'total_listado':  len(series_unicas),
        'total_sistema':  len(indice_total),
        'encontradas':    encontradas,
        'no_encontradas': no_encontradas,
        'no_en_listado':  no_en_listado,
    }


def _leer_series_desde_request():
    """
    Lee las series del formulario según el método elegido.
    Devuelve (lista_de_series_en_mayuscula, mensaje_de_error_o_None).
    """
    metodo = request.form.get('metodo', 'excel')
    CABECERAS = {'NONE', 'NÚMERO DE SERIE', 'N° SERIE',
                 'NUMERO DE SERIE', 'SERIE', 'N°SERIE'}
    series_input = []

    if metodo == 'excel':
        archivo = request.files.get('archivo_excel')
        if not archivo or archivo.filename == '':
            return [], 'Seleccioná un archivo Excel.'
        try:
            import openpyxl
            from io import BytesIO as _BytesIO
            wb = openpyxl.load_workbook(_BytesIO(archivo.read()), data_only=True)
            ws = wb.active
            for row in ws.iter_rows(values_only=True):
                for cell in row:
                    val = str(cell).strip().upper() if cell is not None else ''
                    if val and val not in CABECERAS:
                        series_input.append(val)
        except Exception as e:
            return [], f'Error al leer el archivo Excel: {e}'

    elif metodo == 'sheets':
        url_sheet   = request.form.get('url_sheet', '').strip()
        nombre_hoja = request.form.get('nombre_hoja', '').strip() or 'Hoja1'
        if not url_sheet:
            return [], 'Ingresá la URL de la planilla de Google Sheets.'
        try:
            from services.importar_drive import _get_service, _extraer_sheet_id, _leer_hoja
            sheet_id = _extraer_sheet_id(url_sheet)
            filas    = _leer_hoja(_get_service(), sheet_id, nombre_hoja)
            for fila in filas:
                for celda in fila:
                    val = str(celda).strip().upper() if celda else ''
                    if val and val not in CABECERAS:
                        series_input.append(val)
        except Exception as e:
            return [], f'Error al leer Google Sheets: {e}'

    elif metodo == 'manual':
        texto        = request.form.get('series_manuales', '')
        series_input = [s.strip().upper() for s in texto.splitlines() if s.strip()]

    else:
        return [], 'Método no válido.'

    if not series_input:
        return [], 'No se encontraron números de serie en el listado.'

    return series_input, None


@stock_bp.route('/control-masivo', methods=['GET', 'POST'])
@login_required
def control_masivo():
    """
    Pantalla de control masivo.
    En POST procesa el listado, guarda SOLO las series en session
    (strings livianos) y renderiza el resultado completo en el template.
    El PDF se genera reprocesando las series desde session, sin depender
    de datos pesados — esto evita el límite de ~4 KB de la session de Flask.
    """
    if request.method == 'GET':
        return render_template('stock/control_masivo.html', resultado=None)

    series_input, error = _leer_series_desde_request()
    if error:
        flash(error, 'danger')
        return redirect(url_for('stock.control_masivo'))

    resultado = _procesar_control_masivo(series_input)

    # Guardar SOLO las series en session (liviano: solo strings)
    # El PDF las reprocesa haciendo las mismas queries a la BD.
    session['stock_masivo_series'] = series_input

    return render_template('stock/control_masivo.html',
                           resultado=resultado,
                           fecha=resultado['fecha'],
                           usuario=resultado['usuario'])


@stock_bp.route('/control-masivo/pdf')
@login_required
def control_masivo_pdf():
    """
    Genera el PDF del control masivo reprocesando las series guardadas
    en session. Si la session no tiene datos, redirige con aviso claro.
    """
    series_input = session.get('stock_masivo_series')
    if not series_input:
        flash(
            'No se encontraron datos del control. '
            'Esto puede pasar si cerraste la pestaña o la sesión expiró. '
            'Ejecutá el control masivo nuevamente y descargá el PDF desde esa misma pantalla.',
            'warning'
        )
        return redirect(url_for('stock.control_masivo'))

    resultado = _procesar_control_masivo(series_input)

    from services.pdf_reportes import pdf_control_masivo_stock
    return pdf_control_masivo_stock(resultado)
