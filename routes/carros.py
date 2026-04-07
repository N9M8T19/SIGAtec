from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Carro, Netbook

carros_bp = Blueprint('carros', __name__, url_prefix='/carros')


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
    from sqlalchemy import func
    cursos_m = db.session.query(Alumno.curso, func.count(Alumno.id)) \
                         .filter(Alumno.turno == 'M') \
                         .group_by(Alumno.curso).order_by(Alumno.curso).all()
    cursos_t = db.session.query(Alumno.curso, func.count(Alumno.id)) \
                         .filter(Alumno.turno == 'T') \
                         .group_by(Alumno.curso).order_by(Alumno.curso).all()
    cursos_manana = [c[0] for c in cursos_m]
    cursos_tarde  = [c[0] for c in cursos_t]
    conteo_cursos = {c[0]: c[1] for c in list(cursos_m) + list(cursos_t)}
    return render_template('carros/netbooks.html', carro=carro,
                           cursos_manana=cursos_manana,
                           cursos_tarde=cursos_tarde,
                           conteo_cursos=conteo_cursos)


# ─────────────────────────────────────────────────────────────────────────────
#  ASIGNACIÓN AUTOMÁTICA DE ALUMNOS A CARRO
# ─────────────────────────────────────────────────────────────────────────────

@carros_bp.route('/<int:id>/asignar-automatico', methods=['POST'])
@login_required
def asignar_automatico(id):
    """
    Asigna automáticamente alumnos de dos cursos (mañana y tarde) a las
    netbooks de un carro, en orden alfabético.
    """
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso para esta acción.', 'danger')
        return redirect(url_for('carros.netbooks', id=id))

    carro        = Carro.query.get_or_404(id)
    curso_manana = request.form.get('curso_manana', '').strip()
    curso_tarde  = request.form.get('curso_tarde', '').strip()

    if not curso_manana and not curso_tarde:
        flash('Seleccioná al menos un curso para asignar.', 'danger')
        return redirect(url_for('carros.netbooks', id=id))

    # Netbooks operativas del carro, ordenadas por numero_interno
    netbooks = sorted(
        [nb for nb in carro.netbooks if nb.estado == 'operativa'],
        key=lambda nb: (nb.numero_interno or '').zfill(10)
    )

    asignados_m = 0
    asignados_t = 0
    sin_netbook_m = 0
    sin_netbook_t = 0

    # ── Asignar turno mañana ──────────────────────────────────────────────────
    if curso_manana:
        alumnos_m = Alumno.query.filter_by(curso=curso_manana, turno='M') \
                                .order_by(Alumno.apellido, Alumno.nombre).all()
        for i, alumno in enumerate(alumnos_m):
            if i < len(netbooks):
                netbooks[i].alumno_manana_id = alumno.id
                asignados_m += 1
            else:
                sin_netbook_m += 1

    # ── Asignar turno tarde ───────────────────────────────────────────────────
    if curso_tarde:
        alumnos_t = Alumno.query.filter_by(curso=curso_tarde, turno='T') \
                                .order_by(Alumno.apellido, Alumno.nombre).all()
        for i, alumno in enumerate(alumnos_t):
            if i < len(netbooks):
                netbooks[i].alumno_tarde_id = alumno.id
                asignados_t += 1
            else:
                sin_netbook_t += 1

    db.session.commit()

    # Mensaje resumen
    msg = []
    if asignados_m:
        msg.append(f'{asignados_m} alumnos de {curso_manana} asignados al turno mañana')
    if asignados_t:
        msg.append(f'{asignados_t} alumnos de {curso_tarde} asignados al turno tarde')
    if sin_netbook_m:
        msg.append(f'⚠️ {sin_netbook_m} alumnos de mañana sin netbook disponible')
    if sin_netbook_t:
        msg.append(f'⚠️ {sin_netbook_t} alumnos de tarde sin netbook disponible')

    if msg:
        flash(' | '.join(msg), 'success' if not sin_netbook_m and not sin_netbook_t else 'warning')
    else:
        flash('No se encontraron alumnos para los cursos seleccionados.', 'warning')

    return redirect(url_for('carros.netbooks', id=id))


@carros_bp.route('/<int:id>/desasignar-todos', methods=['POST'])
@login_required
def desasignar_todos(id):
    """Quita todas las asignaciones de alumnos del carro."""
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
