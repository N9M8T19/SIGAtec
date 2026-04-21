"""
routes/importar.py
Módulo de importación desde Google Sheets con selección de pestañas.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user

importar_bp = Blueprint('importar', __name__, url_prefix='/importar')


@importar_bp.route('/')
@login_required
def index():
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas para acceder.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('importar/index.html')


# ─────────────────────────────────────────────────────────────────────────────
#  PASO 1 — Cargar planilla y mostrar pestañas
# ─────────────────────────────────────────────────────────────────────────────

@importar_bp.route('/cargar-pestanas', methods=['POST'])
@login_required
def cargar_pestanas():
    """Recibe la URL, obtiene las pestañas y las muestra para seleccionar."""
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('importar.index'))

    url  = request.form.get('url', '').strip()
    tipo = request.form.get('tipo', '')  # carros / docentes / pantallas

    if not url:
        flash('Ingresá la URL de la planilla.', 'danger')
        return redirect(url_for('importar.index'))

    try:
        from services.importar_drive import obtener_pestanas
        pestanas, sheet_id = obtener_pestanas(url)

        # Guardar en session para el paso 2
        session['importar_sheet_id'] = sheet_id
        session['importar_url']      = url
        session['importar_tipo']     = tipo

        return render_template('importar/seleccionar_pestanas.html',
                               pestanas=pestanas, tipo=tipo, url=url)
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al acceder a la planilla: {str(e)}', 'danger')
        return redirect(url_for('importar.index'))

# ─────────────────────────────────────────────────────────────────────────────
#  PASO 2 — Importar las pestañas seleccionadas
# ─────────────────────────────────────────────────────────────────────────────

@importar_bp.route('/ejecutar', methods=['POST'])
@login_required
def ejecutar():
    """Ejecuta la importación de las pestañas seleccionadas."""
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('importar.index'))

    sheet_id  = session.get('importar_sheet_id')
    tipo      = session.get('importar_tipo')
    pestanas  = request.form.getlist('pestanas')

    if not sheet_id or not pestanas:
        flash('Seleccioná al menos una pestaña.', 'danger')
        return redirect(url_for('importar.index'))

    resultados_totales = []

    try:
        if tipo == 'carros':
            from services.importar_drive import importar_carro_desde_hoja
            for p in pestanas:
                res = importar_carro_desde_hoja(sheet_id, p)
                resultados_totales.append(res)

        elif tipo == 'docentes':
            from services.importar_drive import importar_docentes
            for p in pestanas:
                res = importar_docentes(sheet_id, p)
                resultados_totales.append(res)

        elif tipo == 'pantallas':
            from services.importar_drive import importar_pantallas
            for p in pestanas:
                res = importar_pantallas(sheet_id, p)
                resultados_totales.append(res)

        elif tipo == 'alumnos':
            from services.importar_drive import importar_alumnos
            for p in pestanas:
                res = importar_alumnos(sheet_id, p)
                resultados_totales.append(res)

        return render_template('importar/resultado.html',
                               resultados=resultados_totales, tipo=tipo)

    except Exception as e:
        flash(f'Error durante la importación: {str(e)}', 'danger')
        return redirect(url_for('importar.index'))


# ─────────────────────────────────────────────────────────────────────────────
#  IMPORTAR HORARIOS DE DOCENTES
# ─────────────────────────────────────────────────────────────────────────────

@importar_bp.route('/horarios-docentes', methods=['GET', 'POST'])
@login_required
def horarios_docentes():
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas para acceder.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        url         = request.form.get('url_sheet', '').strip()
        nombre_hoja = request.form.get('nombre_hoja', 'IMPORTAR').strip() or 'IMPORTAR'

        if not url:
            flash('Ingresá la URL de la planilla de Google Sheets.', 'danger')
            return redirect(url_for('importar.horarios_docentes'))

        try:
            from services.importar_drive import importar_horarios_docentes, _extraer_sheet_id
            resultados = importar_horarios_docentes(_extraer_sheet_id(url), nombre_hoja)
        except Exception as e:
            flash(f'Error al conectar con Google Sheets: {e}', 'danger')
            return redirect(url_for('importar.horarios_docentes'))

        return render_template('importar/horarios_docentes.html',
                               resultados=resultados,
                               url_sheet=url,
                               nombre_hoja=nombre_hoja)

    return render_template('importar/horarios_docentes.html', resultados=None)


@importar_bp.route('/horarios-docentes/preview', methods=['POST'])
@login_required
def horarios_docentes_preview():
    """AJAX — devuelve una muestra de las primeras filas de la pestaña IMPORTAR."""
    if not current_user.tiene_permiso('configuracion'):
        return {'ok': False, 'error': 'Sin permiso.'}, 403

    url         = request.form.get('url_sheet', '').strip()
    nombre_hoja = request.form.get('nombre_hoja', 'IMPORTAR').strip() or 'IMPORTAR'

    if not url:
        return {'ok': False, 'error': 'URL vacía.'}, 400

    try:
        from services.importar_drive import _get_service, _extraer_sheet_id, _leer_hoja
        filas = _leer_hoja(_get_service(), _extraer_sheet_id(url), nombre_hoja)

        if not filas or len(filas) < 4:
            return {'ok': False, 'error': 'La pestaña no tiene datos suficientes.'}, 200

        encabezados = filas[2]
        muestra     = filas[3:13]

        try:
            idx = [str(h).strip().lower() for h in encabezados].index('apellido_nombre')
            docentes_unicos = len({
                str(f[idx]).strip().upper()
                for f in muestra
                if len(f) > idx and f[idx]
            })
        except (ValueError, IndexError):
            docentes_unicos = 0

        return {
            'ok':             True,
            'encabezados':    encabezados,
            'muestra':        muestra,
            'total_filas':    len(filas) - 3,
            'docentes_aprox': docentes_unicos,
        }, 200

    except Exception as e:
        return {'ok': False, 'error': str(e)}, 200
