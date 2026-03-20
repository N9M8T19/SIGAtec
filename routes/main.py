from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Carro, Netbook, Docente, PrestamoCarro, PrestamoNetbook, Usuario
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Estadisticas generales
    total_carros    = Carro.query.filter(Carro.estado != 'baja').count()
    total_netbooks  = Netbook.query.count()
    operativas      = Netbook.query.filter_by(estado='operativa').count()
    en_servicio     = Netbook.query.filter_by(estado='servicio_tecnico').count()
    total_docentes  = Docente.query.filter_by(activo=True).count()

    prestamos_activos = PrestamoCarro.query.filter_by(estado='activo').count()
    nb_prestadas      = db.session.query(db.func.count()).select_from(
        PrestamoNetbook).filter_by(estado='activo').scalar()

    # Alertas — préstamos con más de 2 horas
    from config import Config
    limite = Config.MINUTOS_ALERTA_PRESTAMO
    alertas = []
    for p in PrestamoCarro.query.filter_by(estado='activo').all():
        mins = int((datetime.utcnow() - p.hora_retiro).total_seconds() / 60)
        if mins >= limite:
            alertas.append({
                'tipo':    'Carro',
                'docente': p.docente.nombre_completo,
                'item':    p.carro.display,
                'tiempo':  p.tiempo_transcurrido
            })
    for p in PrestamoNetbook.query.filter_by(estado='activo').all():
        mins = int((datetime.utcnow() - p.hora_retiro).total_seconds() / 60)
        if mins >= limite:
            alertas.append({
                'tipo':    'Netbooks',
                'docente': p.docente.nombre_completo,
                'item':    f"{len(p.items)} netbook(s)",
                'tiempo':  p.tiempo_transcurrido
            })

    stats = {
        'total_carros':      total_carros,
        'total_netbooks':    total_netbooks,
        'operativas':        operativas,
        'en_servicio':       en_servicio,
        'total_docentes':    total_docentes,
        'prestamos_activos': prestamos_activos,
        'nb_prestadas':      nb_prestadas,
    }

    return render_template('main/dashboard.html',
                           stats=stats,
                           alertas=alertas)
