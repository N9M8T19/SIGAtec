from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Carro, Netbook, Docente, PrestamoCarro, PrestamoNetbook, Usuario, ConfigEspacioDigital
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    total_carros   = Carro.query.filter(Carro.estado != 'baja').count()
    total_netbooks = Netbook.query.count()
    operativas     = Netbook.query.filter_by(estado='operativa').count()
    en_servicio    = Netbook.query.filter_by(estado='servicio_tecnico').count()
    total_docentes = Docente.query.filter_by(activo=True).count()
    prestamos_activos = PrestamoCarro.query.filter_by(estado='activo').count()
    nb_prestadas = PrestamoNetbook.query.filter_by(estado='activo').count()

    from config import Config
    limite  = Config.MINUTOS_ALERTA_PRESTAMO
    ahora   = datetime.utcnow()
    alertas = []

    for p in PrestamoCarro.query.filter_by(estado='activo').all():
        mins = int((ahora - p.hora_retiro).total_seconds() / 60)
        if mins >= limite:
            alertas.append({
                'tipo':    'Carro',
                'docente': p.docente.nombre_completo,
                'item':    p.carro.display,
                'tiempo':  p.tiempo_transcurrido
            })

    for p in PrestamoNetbook.query.filter_by(estado='activo').all():
        mins = int((ahora - p.hora_retiro).total_seconds() / 60)
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
                           stats=stats, alertas=alertas, now=ahora)


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN ESPACIO DIGITAL — asignar carro
# ─────────────────────────────────────────────────────────────────────────────

@main_bp.route('/configuracion/espacio-digital', methods=['GET', 'POST'])
@login_required
def config_espacio_digital():
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('main.dashboard'))

    config = ConfigEspacioDigital.query.first()
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()

    if request.method == 'POST':
        carro_id       = request.form.get('carro_id', type=int)
        nombre         = request.form.get('nombre', 'Carro Espacio Digital').strip()
        minutos_alerta = request.form.get('minutos_alerta', 120, type=int)

        if not config:
            config = ConfigEspacioDigital()
            db.session.add(config)

        config.carro_id       = carro_id
        config.nombre         = nombre
        config.minutos_alerta = minutos_alerta
        db.session.commit()
        flash('Configuración del Espacio Digital actualizada.', 'success')
        return redirect(url_for('prestamos.espacio_digital'))

    return render_template('main/config_espacio_digital.html',
                           config=config, carros=carros)
