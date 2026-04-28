from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Carro, Netbook, PrestamoCarro
from datetime import datetime

carros_bp = Blueprint('carros', __name__, url_prefix='/carros')

MOTIVOS_SERVICIO_CARRO = [
    ('termica',    'Térmica quemada'),
    ('cerradura',  'Cerradura rota'),
    ('rueda',      'Rueda rota'),
    ('estructura', 'Estructura / chasis dañado'),
    ('electrico',  'Problema eléctrico'),
    ('otro',       'Otro'),
]


@carros_bp.route('/')
@login_required
def index():
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    return render_template('carros/index.html', carros=carros)


@carros_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenes permiso para esta accion.', 'danger')
        return redirect(url_for('carros.index'))

    if request.method == 'POST':
        carro = Carro(
            numero_fisico = request.form.get('numero_fisico', '').strip(),
            numero_serie  = request.form.get('numero_serie', '').strip(),
            division      = request.form.get('division', '').strip(),
            aula          = request.form.get('aula', '').strip(),
            sheet_url     = request.form.get('sheet_url', '').strip(),
        )
        db.session.add(carro)
        db.session.commit()
        flash(f'Carro {carro.display} creado correctamente.', 'success')
        return redirect(url_for('carros.index'))

    return render_template('carros/form.html', carro=None)


@carros_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    carro = Carro.query.get_or_404(id)

    if request.method == 'POST':
        carro.numero_fisico = request.form.get('numero_fisico', '').strip()
        carro.numero_serie  = request.form.get('numero_serie', '').strip()
        carro.division      = request.form.get('division', '').strip()
        carro.aula          = request.form.get('aula', '').strip()
        carro.sheet_url     = request.form.get('sheet_url', '').strip()
        db.session.commit()
        flash(f'Carro {carro.display} actualizado.', 'success')
        return redirect(url_for('carros.index'))

    return render_template('carros/form.html', carro=carro)


@carros_bp.route('/<int:id>/baja', methods=['POST'])
@login_required
def dar_baja(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenes permiso para esta accion.', 'danger')
        return redirect(url_for('carros.index'))

    carro = Carro.query.get_or_404(id)
    carro.estado = 'baja'
    db.session.commit()
    flash(f'Carro {carro.display} dado de baja.', 'warning')
    return redirect(url_for('carros.index'))


@carros_bp.route('/<int:id>/netbooks')
@login_required
def netbooks(id):
    carro = Carro.query.get_or_404(id)
    from models import Alumno
    from sqlalchemy import func, cast, Integer
    cursos_m = db.session.query(Alumno.curso, func.count(Alumno.id)) \
                         .filter(Alumno.turno == 'M') \
                         .group_by(Alumno.curso).order_by(Alumno.curso).all()
    cursos_t = db.session.query(Alumno.curso, func.count(Alumno.id)) \
                         .filter(Alumno.turno == 'T') \
                         .group_by(Alumno.curso).order_by(Alumno.curso).all()
    cursos_manana = [c[0] for c in cursos_m]
    cursos_tarde  = [c[0] for c in cursos_t]
    conteo_cursos = {c[0]: c[1] for c in list(cursos_m) + list(cursos_t)}
    # Ordenar netbooks numericamente por numero_interno
    carro.netbooks.sort(key=lambda nb: int(nb.numero_interno) if nb.numero_interno and nb.numero_interno.isdigit() else 9999)
    return render_template('carros/netbooks.html', carro=carro,
                           cursos_manana=cursos_manana,
                           cursos_tarde=cursos_tarde,
                           conteo_cursos=conteo_cursos)


@carros_bp.route('/<int:id>/asignar-automatico', methods=['POST'])
@login_required
def asignar_automatico(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso para esta acción.', 'danger')
        return redirect(url_for('carros.netbooks', id=id))

    carro        = Carro.query.get_or_404(id)
    curso_manana = request.form.get('curso_manana', '').strip()
    curso_tarde  = request.form.get('curso_tarde', '').strip()

    from models import Alumno

    if not curso_manana and not curso_tarde:
        flash('Seleccioná al menos un curso para asignar.', 'danger')
        return redirect(url_for('carros.netbooks', id=id))

    netbooks = sorted(
        [nb for nb in carro.netbooks if nb.estado == 'operativa'],
        key=lambda nb: int(nb.numero_interno) if nb.numero_interno and nb.numero_interno.isdigit() else 9999
    )

    if not netbooks:
        flash('Este carro no tiene netbooks operativas.', 'warning')
        return redirect(url_for('carros.netbooks', id=id))

    for nb in netbooks:
        nb.alumno_manana_id = None
        nb.alumno_tarde_id  = None

    asignados_m = sin_netbook_m = asignados_t = sin_netbook_t = 0

    if curso_manana:
        Alumno.query.filter_by(curso=curso_manana, turno='M').update({'netbook_id': None})
        alumnos_m = Alumno.query.filter_by(curso=curso_manana, turno='M')\
                                .order_by(Alumno.apellido, Alumno.nombre).all()
        for i, alumno in enumerate(alumnos_m):
            if i < len(netbooks):
                netbooks[i].alumno_manana_id = alumno.id
                alumno.netbook_id = netbooks[i].id
                asignados_m += 1
            else:
                alumno.netbook_id = None
                sin_netbook_m += 1

    if curso_tarde:
        Alumno.query.filter_by(curso=curso_tarde, turno='T').update({'netbook_id': None})
        alumnos_t = Alumno.query.filter_by(curso=curso_tarde, turno='T')\
                                .order_by(Alumno.apellido, Alumno.nombre).all()
        for i, alumno in enumerate(alumnos_t):
            if i < len(netbooks):
                netbooks[i].alumno_tarde_id = alumno.id
                alumno.netbook_id = netbooks[i].id
                asignados_t += 1
            else:
                alumno.netbook_id = None
                sin_netbook_t += 1

    db.session.commit()

    partes = []
    if asignados_m:
        partes.append(f'{asignados_m} alumnos de {curso_manana} asignados (mañana)')
    if asignados_t:
        partes.append(f'{asignados_t} alumnos de {curso_tarde} asignados (tarde)')
    if sin_netbook_m:
        partes.append(f'⚠️ {sin_netbook_m} alumnos de mañana sin netbook disponible')
    if sin_netbook_t:
        partes.append(f'⚠️ {sin_netbook_t} alumnos de tarde sin netbook disponible')

    categoria = 'warning' if (sin_netbook_m or sin_netbook_t) else 'success'
    flash(' | '.join(partes) if partes else 'No se encontraron alumnos.', categoria)
    return redirect(url_for('carros.netbooks', id=id))


@carros_bp.route('/<int:id>/desasignar-todos', methods=['POST'])
@login_required
def desasignar_todos(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso para esta acción.', 'danger')
        return redirect(url_for('carros.netbooks', id=id))

    carro = Carro.query.get_or_404(id)
    for nb in carro.netbooks:
        nb.alumno_manana_id = None
        nb.alumno_tarde_id  = None
    db.session.commit()
    flash(f'Todas las asignaciones del Carro {carro.display} fueron eliminadas.', 'success')
    return redirect(url_for('carros.netbooks', id=id))

# ─────────────────────────────────────────────────────────────────────────────
#  SERVICIO TÉCNICO DEL CARRO FÍSICO
# ─────────────────────────────────────────────────────────────────────────────

@carros_bp.route('/<int:id>/enviar-servicio', methods=['POST'])
@login_required
def enviar_servicio(id):
    """
    Marca el carro físico como en_servicio con el motivo indicado.
    Bloquea el carro para nuevos préstamos.
    Redirige a transferencias con el carro origen precargado para
    mover las netbooks al carro de reemplazo.
    """
    carro = Carro.query.get_or_404(id)

    if carro.estado == 'en_servicio':
        flash(f'El carro {carro.display} ya está en servicio técnico.', 'warning')
        return redirect(url_for('carros.index'))

    # Bloquear si tiene préstamo activo
    prestamo_activo = PrestamoCarro.query.filter_by(carro_id=id, estado='activo').first()
    if prestamo_activo:
        flash(
            f'El carro {carro.display} tiene un préstamo activo. '
            'Registrá la devolución antes de enviarlo a servicio.',
            'danger'
        )
        return redirect(url_for('carros.index'))

    motivo_clave  = request.form.get('motivo', 'otro')
    motivo_label  = dict(MOTIVOS_SERVICIO_CARRO).get(motivo_clave, 'Otro')

    carro.estado          = 'en_servicio'
    carro.motivo_servicio = motivo_label
    carro.fecha_servicio  = datetime.utcnow()
    db.session.commit()

    flash(
        f'Carro {carro.display} enviado a servicio técnico ({motivo_label}). '
        'Transferí las netbooks al carro de reemplazo.',
        'warning'
    )
    return redirect(url_for('transferencias.index', carro_origen_id=id))


@carros_bp.route('/<int:id>/recuperar', methods=['POST'])
@login_required
def recuperar_carro(id):
    """Marca el carro como operativo y limpia el motivo de servicio."""
    carro = Carro.query.get_or_404(id)

    if carro.estado != 'en_servicio':
        flash(f'El carro {carro.display} no está en servicio técnico.', 'warning')
        return redirect(url_for('carros.index'))

    carro.estado          = 'operativo'
    carro.motivo_servicio = None
    carro.fecha_servicio  = None
    db.session.commit()

    flash(f'Carro {carro.display} recuperado y marcado como operativo.', 'success')
    return redirect(url_for('carros.index'))
