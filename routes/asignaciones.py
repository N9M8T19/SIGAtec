from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Netbook, Docente, AsignacionInterna
from datetime import datetime

asignaciones_bp = Blueprint('asignaciones', __name__, url_prefix='/asignaciones')


def _solo_directivo():
    """Devuelve True si el usuario actual puede acceder a este módulo."""
    return current_user.rol in ('Directivo', 'Administrador')


@asignaciones_bp.route('/')
@login_required
def index():
    if not _solo_directivo():
        flash('No tenés permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))

    filtro = request.args.get('filtro', 'activas')  # activas | todas | bajas

    query = AsignacionInterna.query
    if filtro == 'activas':
        query = query.filter_by(activa=True)
    elif filtro == 'bajas':
        query = query.filter_by(activa=False)
    # 'todas' no filtra

    asignaciones = query.order_by(AsignacionInterna.fecha_asignacion.desc()).all()

    return render_template('asignaciones/index.html',
                           asignaciones=asignaciones,
                           filtro=filtro)


@asignaciones_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if not _solo_directivo():
        flash('No tenés permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))

    netbooks = Netbook.query.order_by(Netbook.numero_interno).all()
    docentes = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()

    if request.method == 'POST':
        netbook_id = request.form.get('netbook_id', type=int)
        docente_id = request.form.get('docente_id', type=int) or None
        area       = request.form.get('area', '').strip() or None
        motivo     = request.form.get('motivo', '').strip() or None

        if not netbook_id:
            flash('Debés seleccionar una netbook.', 'danger')
            return render_template('asignaciones/form.html',
                                   netbooks=netbooks, docentes=docentes, asignacion=None)

        if not docente_id and not area:
            flash('Debés indicar un docente o un área de destino.', 'danger')
            return render_template('asignaciones/form.html',
                                   netbooks=netbooks, docentes=docentes, asignacion=None)

        # Verificar que la netbook no tenga ya una asignación activa
        existente = AsignacionInterna.query.filter_by(
            netbook_id=netbook_id, activa=True).first()
        if existente:
            flash(f'Esa netbook ya tiene una asignación activa '
                  f'(destinatario: {existente.destinatario}).', 'warning')
            return render_template('asignaciones/form.html',
                                   netbooks=netbooks, docentes=docentes, asignacion=None)

        nueva_asig = AsignacionInterna(
            netbook_id     = netbook_id,
            docente_id     = docente_id,
            area           = area,
            motivo         = motivo,
            registrado_por = current_user.nombre_completo,
        )
        db.session.add(nueva_asig)
        db.session.commit()
        flash('Asignación registrada correctamente.', 'success')
        return redirect(url_for('asignaciones.index'))

    return render_template('asignaciones/form.html',
                           netbooks=netbooks, docentes=docentes, asignacion=None)


@asignaciones_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not _solo_directivo():
        flash('No tenés permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))

    asig = AsignacionInterna.query.get_or_404(id)
    netbooks = Netbook.query.order_by(Netbook.numero_interno).all()
    docentes = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()

    if request.method == 'POST':
        docente_id = request.form.get('docente_id', type=int) or None
        area       = request.form.get('area', '').strip() or None
        motivo     = request.form.get('motivo', '').strip() or None

        if not docente_id and not area:
            flash('Debés indicar un docente o un área de destino.', 'danger')
            return render_template('asignaciones/form.html',
                                   netbooks=netbooks, docentes=docentes, asignacion=asig)

        asig.docente_id = docente_id
        asig.area       = area
        asig.motivo     = motivo
        db.session.commit()
        flash('Asignación actualizada.', 'success')
        return redirect(url_for('asignaciones.index'))

    return render_template('asignaciones/form.html',
                           netbooks=netbooks, docentes=docentes, asignacion=asig)


@asignaciones_bp.route('/<int:id>/dar-baja', methods=['POST'])
@login_required
def dar_baja(id):
    if not _solo_directivo():
        flash('No tenés permisos para realizar esta acción.', 'danger')
        return redirect(url_for('main.dashboard'))

    asig = AsignacionInterna.query.get_or_404(id)
    motivo_baja = request.form.get('motivo_baja', '').strip()

    asig.activa      = False
    asig.fecha_baja  = datetime.utcnow()
    asig.motivo_baja = motivo_baja or 'Sin motivo especificado'
    db.session.commit()
    flash('Asignación dada de baja correctamente.', 'success')
    return redirect(url_for('asignaciones.index'))
