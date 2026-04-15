from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Docente, PrestamoCarro, PrestamoNetbook
from models_extra.horarios_notificaciones import MATERIAS

docentes_bp = Blueprint('docentes', __name__, url_prefix='/docentes')

TURNOS = ['Mañana', 'Tarde', 'Noche', 'Mañana y Tarde', 'Tarde y Noche', 'Varios']

MOTIVOS_BAJA = [
    ('jubilacion', 'Jubilación (se elimina del sistema)'),
    ('renuncia',   'Renuncia'),
    ('traslado',   'Traslado'),
    ('otro',       'Otro'),
]


@docentes_bp.route('/')
@login_required
def index():
    filtro   = request.args.get('filtro', 'activos')
    busqueda = request.args.get('q', '').strip()

    query = Docente.query
    if filtro == 'activos':
        query = query.filter_by(activo=True)
    elif filtro == 'inactivos':
        query = query.filter_by(activo=False)

    if busqueda:
        query = query.filter(
            db.or_(Docente.apellido.ilike(f'%{busqueda}%'),
                   Docente.nombre.ilike(f'%{busqueda}%'),
                   Docente.dni.ilike(f'%{busqueda}%')))

    docentes = query.order_by(Docente.apellido).all()
    return render_template('docentes/index.html',
                           docentes=docentes, filtro=filtro,
                           busqueda=busqueda, turnos=TURNOS)


@docentes_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        dni = request.form.get('dni', '').strip()
        if Docente.query.filter_by(dni=dni).first():
            flash(f'Ya existe un docente con DNI {dni}.', 'danger')
            return redirect(url_for('docentes.nuevo'))

        docente = Docente(
            dni      = dni,
            nombre   = request.form.get('nombre', '').strip(),
            apellido = request.form.get('apellido', '').strip(),
            materia  = request.form.get('materia', '').strip(),
            correo   = request.form.get('correo', '').strip(),
            turno    = request.form.get('turno', '').strip(),
        )
        db.session.add(docente)
        db.session.commit()
        flash(f'Docente {docente.nombre_completo} agregado.', 'success')
        return redirect(url_for('docentes.index'))

    return render_template('docentes/form.html',
                           docente=None, turnos=TURNOS, materias=MATERIAS)


@docentes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    docente = Docente.query.get_or_404(id)

    if request.method == 'POST':
        docente.nombre   = request.form.get('nombre', '').strip()
        docente.apellido = request.form.get('apellido', '').strip()
        docente.materia  = request.form.get('materia', '').strip()
        docente.correo   = request.form.get('correo', '').strip()
        docente.turno    = request.form.get('turno', '').strip()
        db.session.commit()
        flash(f'Docente {docente.nombre_completo} actualizado.', 'success')
        return redirect(url_for('docentes.index'))

    return render_template('docentes/form.html',
                           docente=docente, turnos=TURNOS, materias=MATERIAS)


@docentes_bp.route('/<int:id>/baja', methods=['GET', 'POST'])
@login_required
def dar_baja(id):
    if not current_user.tiene_permiso('estadisticas'):
        flash('No tenés permiso para esta acción.', 'danger')
        return redirect(url_for('docentes.index'))

    docente = Docente.query.get_or_404(id)

    if request.method == 'POST':
        motivo = request.form.get('motivo', '').strip()

        if not motivo:
            flash('Tenés que seleccionar un motivo de baja.', 'danger')
            return render_template('docentes/baja.html',
                                   docente=docente, motivos=MOTIVOS_BAJA)

        # Verificar préstamo activo antes de cualquier acción
        prestamo_activo = PrestamoCarro.query.filter_by(
            docente_id=id, estado='activo'
        ).first()
        if prestamo_activo:
            flash(f'{docente.nombre_completo} tiene un préstamo activo. '
                  'Registrá la devolución antes de dar de baja.', 'danger')
            return redirect(url_for('docentes.index'))

        if motivo == 'jubilacion':
            # Guardar nombre ANTES de cualquier operación sobre el objeto
            nombre = docente.nombre_completo

            # Eliminar préstamos históricos de carros (docente_id NOT NULL)
            PrestamoCarro.query.filter_by(docente_id=id).delete()

            # Eliminar préstamos históricos de netbooks (docente_id NOT NULL)
            PrestamoNetbook.query.filter_by(docente_id=id).delete()

            # Ahora sí se puede eliminar el docente sin violar FK
            db.session.delete(docente)
            db.session.commit()
            flash(f'{nombre} eliminado del sistema (jubilación).', 'success')
        else:
            docente.activo = False
            db.session.commit()
            flash(f'{docente.nombre_completo} dado de baja ({motivo}).', 'warning')

        return redirect(url_for('docentes.index'))

    # GET — mostrar página de confirmación con selector de motivo
    return render_template('docentes/baja.html',
                           docente=docente, motivos=MOTIVOS_BAJA)


@docentes_bp.route('/<int:id>/reactivar', methods=['POST'])
@login_required
def reactivar(id):
    if not current_user.tiene_permiso('estadisticas'):
        flash('No tenes permiso para esta accion.', 'danger')
        return redirect(url_for('docentes.index'))
    docente = Docente.query.get_or_404(id)
    docente.activo = True
    db.session.commit()
    flash(f'{docente.nombre_completo} reactivado.', 'success')
    return redirect(url_for('docentes.index'))


@docentes_bp.route('/buscar')
@login_required
def buscar_api():
    """API para búsqueda en tiempo real (AJAX)"""
    from flask import jsonify
    q = request.args.get('q', '').strip()
    docentes = Docente.query.filter(
        Docente.activo == True,
        db.or_(Docente.apellido.ilike(f'%{q}%'),
               Docente.nombre.ilike(f'%{q}%'),
               Docente.dni.ilike(f'%{q}%'))
    ).order_by(Docente.apellido).limit(10).all()

    return jsonify([{
        'id':      d.id,
        'nombre':  d.nombre_completo,
        'dni':     d.dni,
        'materia': d.materia or '',
        'turno':   d.turno or ''
    } for d in docentes])
