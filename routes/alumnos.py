"""
routes/alumnos.py
Gestión de alumnos — listado paginado, búsqueda y eliminación.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Alumno, Netbook

alumnos_bp = Blueprint('alumnos', __name__, url_prefix='/alumnos')

POR_PAGINA = 20


@alumnos_bp.route('/')
@login_required
def index():
    q      = request.args.get('q', '').strip()
    turno  = request.args.get('turno', '')   # 'M', 'T' o ''
    curso  = request.args.get('curso', '').strip()
    page   = request.args.get('page', 1, type=int)

    query = Alumno.query

    if q:
        query = query.filter(
            db.or_(
                Alumno.apellido.ilike(f'%{q}%'),
                Alumno.nombre.ilike(f'%{q}%'),
                Alumno.dni.ilike(f'%{q}%'),
            )
        )
    if turno in ('M', 'T'):
        query = query.filter(Alumno.turno == turno)
    if curso:
        query = query.filter(Alumno.curso.ilike(f'%{curso}%'))

    query = query.order_by(Alumno.curso, Alumno.turno, Alumno.apellido, Alumno.nombre)
    paginacion = query.paginate(page=page, per_page=POR_PAGINA, error_out=False)

    # Obtener lista de cursos únicos para el filtro desplegable
    cursos_unicos = db.session.query(Alumno.curso).distinct().order_by(Alumno.curso).all()
    cursos_unicos = [c[0] for c in cursos_unicos]

    total = Alumno.query.count()

    return render_template('alumnos/index.html',
                           alumnos=paginacion.items,
                           paginacion=paginacion,
                           busqueda=q,
                           turno=turno,
                           curso_filtro=curso,
                           cursos_unicos=cursos_unicos,
                           total=total)


@alumnos_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permiso para eliminar alumnos.', 'danger')
        return redirect(url_for('alumnos.index'))

    alumno = Alumno.query.get_or_404(id)

    # Desasignar de netbooks antes de borrar
    Netbook.query.filter_by(alumno_manana_id=id).update({'alumno_manana_id': None})
    Netbook.query.filter_by(alumno_tarde_id=id).update({'alumno_tarde_id': None})

    db.session.delete(alumno)
    db.session.commit()
    flash(f'Alumno {alumno.nombre_completo} eliminado.', 'success')
    return redirect(url_for('alumnos.index'))


@alumnos_bp.route('/eliminar-todos', methods=['POST'])
@login_required
def eliminar_todos():
    """Borra todos los alumnos y desasigna las netbooks. Solo Administrador."""
    if not current_user.tiene_permiso('todo'):
        flash('Solo el Administrador puede borrar todos los alumnos.', 'danger')
        return redirect(url_for('alumnos.index'))

    Netbook.query.update({'alumno_manana_id': None, 'alumno_tarde_id': None})
    Alumno.query.delete()
    db.session.commit()
    flash('Todos los alumnos fueron eliminados y las netbooks desasignadas.', 'success')
    return redirect(url_for('alumnos.index'))


@alumnos_bp.route('/conteo-por-curso')
@login_required
def conteo_por_curso():
    """AJAX — devuelve cuántos alumnos tiene un curso/turno específico."""
    curso = request.args.get('curso', '').strip()
    turno = request.args.get('turno', '').strip()  # 'M' o 'T'
    if not curso or turno not in ('M', 'T'):
        return jsonify({'count': 0})
    count = Alumno.query.filter_by(curso=curso, turno=turno).count()
    return jsonify({'count': count})
