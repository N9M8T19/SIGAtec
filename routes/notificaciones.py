"""
routes/notificaciones.py
Configuración de destinatarios de notificaciones y gestión de backups.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db
from models_extra.horarios_notificaciones import ConfigNotificacion, LogNotificacion

notificaciones_bp = Blueprint('notificaciones', __name__, url_prefix='/notificaciones')

EVENTOS_DISPONIBLES = [
    ('retiro_carro',       'Retiro de carro'),
    ('devolucion_carro',   'Devolución de carro'),
    ('retiro_netbook',     'Retiro de netbooks'),
    ('devolucion_netbook', 'Devolución de netbooks'),
    ('alerta_demora',      'Alerta por demora'),
    ('alerta_horario',     'Alerta por fin de módulo'),
]


@notificaciones_bp.route('/')
@login_required
def index():
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso para acceder.', 'danger')
        return redirect(url_for('main.dashboard'))

    configs = ConfigNotificacion.query.order_by(ConfigNotificacion.nombre).all()
    logs    = LogNotificacion.query.order_by(LogNotificacion.created_at.desc()).limit(50).all()
    return render_template('notificaciones/index.html',
                           configs=configs, logs=logs,
                           eventos=EVENTOS_DISPONIBLES)


@notificaciones_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso.', 'danger')
        return redirect(url_for('notificaciones.index'))

    if request.method == 'POST':
        nombre  = request.form.get('nombre', '').strip()
        correo  = request.form.get('correo', '').strip()
        eventos = request.form.getlist('eventos')

        if not nombre or not correo:
            flash('Nombre y correo son obligatorios.', 'danger')
            return redirect(url_for('notificaciones.nuevo'))

        config = ConfigNotificacion(
            nombre=nombre,
            correo=correo,
            eventos=','.join(eventos)
        )
        db.session.add(config)
        db.session.commit()
        flash(f'Destinatario {nombre} agregado.', 'success')
        return redirect(url_for('notificaciones.index'))

    return render_template('notificaciones/form.html',
                           config=None, eventos=EVENTOS_DISPONIBLES)


@notificaciones_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso.', 'danger')
        return redirect(url_for('notificaciones.index'))

    config = ConfigNotificacion.query.get_or_404(id)

    if request.method == 'POST':
        config.nombre  = request.form.get('nombre', '').strip()
        config.correo  = request.form.get('correo', '').strip()
        config.activo  = 'activo' in request.form
        eventos        = request.form.getlist('eventos')
        config.eventos = ','.join(eventos)
        db.session.commit()
        flash(f'Destinatario {config.nombre} actualizado.', 'success')
        return redirect(url_for('notificaciones.index'))

    return render_template('notificaciones/form.html',
                           config=config, eventos=EVENTOS_DISPONIBLES)


@notificaciones_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso.', 'danger')
        return redirect(url_for('notificaciones.index'))

    config = ConfigNotificacion.query.get_or_404(id)
    db.session.delete(config)
    db.session.commit()
    flash('Destinatario eliminado.', 'warning')
    return redirect(url_for('notificaciones.index'))


# ─────────────────────────────────────────────────────────────────────────────
#  BACKUP
# ─────────────────────────────────────────────────────────────────────────────

@notificaciones_bp.route('/backup')
@login_required
def backup_index():
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso.', 'danger')
        return redirect(url_for('main.dashboard'))

    from services.backup import listar_backups
    backups = listar_backups()
    return render_template('backup/index.html', backups=backups)


@notificaciones_bp.route('/backup/descargar')
@login_required
def backup_descargar():
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso.', 'danger')
        return redirect(url_for('main.dashboard'))

    from services.backup import descargar_backup_actual
    response = descargar_backup_actual()
    if response is None:
        flash('No se pudo generar el backup. ¿Estás usando SQLite?', 'danger')
        return redirect(url_for('notificaciones.backup_index'))
    return response


@notificaciones_bp.route('/backup/descargar/<nombre>')
@login_required
def backup_descargar_archivo(nombre):
    """Descarga un backup específico ya guardado."""
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso.', 'danger')
        return redirect(url_for('main.dashboard'))

    import os
    from flask import send_file, abort
    ruta = os.path.join('backups', nombre)
    if not os.path.exists(ruta) or not nombre.startswith('sigartec_backup_'):
        abort(404)
    return send_file(ruta, as_attachment=True, download_name=nombre,
                     mimetype='application/octet-stream')
