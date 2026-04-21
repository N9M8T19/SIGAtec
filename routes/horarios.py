"""
routes/horarios.py
ABM de horarios de docentes por módulo.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Docente
from models_extra.horarios_notificaciones import HorarioDocente, DIAS_SEMANA, MODULOS

horarios_bp = Blueprint('horarios', __name__, url_prefix='/horarios')


@horarios_bp.route('/docente/<int:docente_id>')
@login_required
def ver_docente(docente_id):
    docente  = Docente.query.get_or_404(docente_id)
    horarios = HorarioDocente.query.filter_by(docente_id=docente_id)\
                .order_by(HorarioDocente.dia, HorarioDocente.modulo).all()

    # Organizar por día para la vista
    por_dia = {dia: [] for dia in DIAS_SEMANA}
    for h in horarios:
        if h.dia in por_dia:
            por_dia[h.dia].append(h)

    return render_template('horarios/ver_docente.html',
                           docente=docente, por_dia=por_dia,
                           dias=DIAS_SEMANA, modulos=MODULOS)


@horarios_bp.route('/docente/<int:docente_id>/agregar', methods=['GET', 'POST'])
@login_required
def agregar(docente_id):
    if not current_user.tiene_permiso('estadisticas'):
        flash('No tenés permiso para esta acción.', 'danger')
        return redirect(url_for('docentes.index'))

    docente = Docente.query.get_or_404(docente_id)

    if request.method == 'POST':
        dia     = request.form.get('dia')
        modulo  = request.form.get('modulo', type=int)
        materia = request.form.get('materia', '').strip() or docente.materia
        aula    = request.form.get('aula', '').strip()

        # Verificar que no exista ya ese módulo ese día para ese docente
        existe = HorarioDocente.query.filter_by(
            docente_id=docente_id, dia=dia, modulo=modulo
        ).first()
        if existe:
            flash(f'Ya existe ese módulo el {dia}.', 'warning')
            return redirect(url_for('horarios.ver_docente', docente_id=docente_id))

        h = HorarioDocente(
            docente_id=docente_id,
            dia=dia,
            modulo=modulo,
            materia=materia,
            aula=aula
        )
        db.session.add(h)
        db.session.commit()
        flash(f'Módulo {modulo} del {dia} agregado.', 'success')
        return redirect(url_for('horarios.ver_docente', docente_id=docente_id))

    return render_template('horarios/form.html',
                           docente=docente, dias=DIAS_SEMANA,
                           modulos=MODULOS, horario=None)


@horarios_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    if not current_user.tiene_permiso('estadisticas'):
        flash('No tenés permiso.', 'danger')
        return redirect(url_for('docentes.index'))

    h = HorarioDocente.query.get_or_404(id)
    docente_id = h.docente_id
    db.session.delete(h)
    db.session.commit()
    flash('Módulo eliminado.', 'warning')
    return redirect(url_for('horarios.ver_docente', docente_id=docente_id))


@horarios_bp.route('/docente/<int:docente_id>/pdf')
@login_required
def pdf_docente(docente_id):
    """Genera el PDF de horarios del docente con el carro asignado por curso."""
    docente = Docente.query.get_or_404(docente_id)
    from services.pdf_reportes import pdf_horario_docente
    return pdf_horario_docente(docente)
