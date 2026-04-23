from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Docente, AsignacionInterna
from datetime import datetime

asignaciones_bp = Blueprint('asignaciones', __name__, url_prefix='/asignaciones')


def _solo_directivo():
    return current_user.rol in ('Directivo', 'Administrador')


@asignaciones_bp.route('/')
@login_required
def index():
    if not _solo_directivo():
        flash('No tenés permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))

    filtro = request.args.get('filtro', 'activas')

    query = AsignacionInterna.query
    if filtro == 'activas':
        query = query.filter_by(activa=True)
    elif filtro == 'bajas':
        query = query.filter_by(activa=False)

    asignaciones = query.order_by(AsignacionInterna.fecha_asignacion.desc()).all()

    return render_template('asignaciones/index.html',
                           asignaciones=asignaciones, filtro=filtro)


@asignaciones_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if not _solo_directivo():
        flash('No tenés permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))

    docentes = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()

    if request.method == 'POST':
        numero_serie   = request.form.get('numero_serie', '').strip() or None
        numero_interno = request.form.get('numero_interno', '').strip() or None
        modelo         = request.form.get('modelo', '').strip() or None
        docente_id     = request.form.get('docente_id', type=int) or None
        area           = request.form.get('area', '').strip() or None
        motivo         = request.form.get('motivo', '').strip() or None

        if not numero_serie and not numero_interno:
            flash('Debés ingresar al menos el número de serie o el número interno.', 'danger')
            return render_template('asignaciones/form.html',
                                   docentes=docentes, asignacion=None)

        if not docente_id and not area:
            flash('Debés indicar un docente o un área de destino.', 'danger')
            return render_template('asignaciones/form.html',
                                   docentes=docentes, asignacion=None)

        nueva_asig = AsignacionInterna(
            numero_serie   = numero_serie,
            numero_interno = numero_interno,
            modelo         = modelo,
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
                           docentes=docentes, asignacion=None)


@asignaciones_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not _solo_directivo():
        flash('No tenés permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))

    asig = AsignacionInterna.query.get_or_404(id)
    docentes = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()

    if request.method == 'POST':
        asig.numero_serie   = request.form.get('numero_serie', '').strip() or None
        asig.numero_interno = request.form.get('numero_interno', '').strip() or None
        asig.modelo         = request.form.get('modelo', '').strip() or None
        asig.docente_id     = request.form.get('docente_id', type=int) or None
        asig.area           = request.form.get('area', '').strip() or None
        asig.motivo         = request.form.get('motivo', '').strip() or None

        if not asig.docente_id and not asig.area:
            flash('Debés indicar un docente o un área de destino.', 'danger')
            return render_template('asignaciones/form.html',
                                   docentes=docentes, asignacion=asig)

        db.session.commit()
        flash('Asignación actualizada.', 'success')
        return redirect(url_for('asignaciones.index'))

    return render_template('asignaciones/form.html',
                           docentes=docentes, asignacion=asig)


@asignaciones_bp.route('/<int:id>/dar-baja', methods=['POST'])
@login_required
def dar_baja(id):
    if not _solo_directivo():
        flash('No tenés permisos para realizar esta acción.', 'danger')
        return redirect(url_for('main.dashboard'))

    asig = AsignacionInterna.query.get_or_404(id)
    asig.activa      = False
    asig.fecha_baja  = datetime.utcnow()
    asig.motivo_baja = request.form.get('motivo_baja', '').strip() or 'Sin motivo especificado'
    db.session.commit()
    flash('Asignación dada de baja correctamente.', 'success')
    return redirect(url_for('asignaciones.index'))
