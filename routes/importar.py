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
