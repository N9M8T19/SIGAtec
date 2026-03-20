from flask import Blueprint, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, PrestamoCarro, PrestamoNetbook, Docente, Carro
from datetime import datetime

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')


@reportes_bp.route('/')
@login_required
def index():
    if not current_user.tiene_permiso('reportes'):
        flash('No tenes permiso para acceder a reportes.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('reportes/index.html')


@reportes_bp.route('/estadisticas')
@login_required
def estadisticas():
    if not current_user.tiene_permiso('estadisticas'):
        flash('No tenes permiso para ver estadisticas.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Top docentes por cantidad de prestamos
    from sqlalchemy import func
    top_docentes = db.session.query(
        Docente, func.count(PrestamoCarro.id).label('total')
    ).join(PrestamoCarro).group_by(Docente.id).order_by(func.count(PrestamoCarro.id).desc()).limit(10).all()

    # Top por materia
    top_materias = db.session.query(
        Docente.materia, func.count(PrestamoCarro.id).label('total')
    ).join(PrestamoCarro).group_by(Docente.materia).order_by(
        func.count(PrestamoCarro.id).desc()).limit(10).all()

    return render_template('reportes/estadisticas.html',
                           top_docentes=top_docentes,
                           top_materias=top_materias)
