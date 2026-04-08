from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Carro, Netbook, Docente, PrestamoCarro, PrestamoNetbook, Usuario, ConfigEspacioDigital, Alumno
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
#  BÚSQUEDA GLOBAL — carros, netbooks, alumnos
# ─────────────────────────────────────────────────────────────────────────────

@main_bp.route('/api/buscar')
@login_required
def buscar():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'carros': [], 'netbooks': [], 'alumnos': []})

    carros = Carro.query.filter(
        Carro.estado != 'baja',
        db.or_(
            Carro.numero_serie.ilike(f'%{q}%'),
            Carro.numero_fisico.ilike(f'%{q}%'),
            Carro.aula.ilike(f'%{q}%'),
            Carro.division.ilike(f'%{q}%'),
        )
    ).limit(5).all()

    netbooks = Netbook.query.filter(
        db.or_(
            Netbook.numero_serie.ilike(f'%{q}%'),
            Netbook.numero_interno.ilike(f'%{q}%'),
            Netbook.alumno.ilike(f'%{q}%'),
        )
    ).limit(5).all()

    alumnos = Alumno.query.filter(
        db.or_(
            Alumno.nombre.ilike(f'%{q}%'),
            Alumno.apellido.ilike(f'%{q}%'),
            Alumno.curso.ilike(f'%{q}%'),
            Alumno.dni.ilike(f'%{q}%'),
        )
    ).limit(5).all()

    def alumno_nb(n):
        # Intentar alumno mañana o tarde, fallback al campo legacy
        if n.alumno_manana:
            return f'{n.alumno_manana.apellido}, {n.alumno_manana.nombre}'
        if n.alumno_tarde:
            return f'{n.alumno_tarde.apellido}, {n.alumno_tarde.nombre}'
        return n.alumno or 'Sin asignar'

    def carro_display(c):
        partes = []
        if c.numero_fisico:
            partes.append(f'Carro {c.numero_fisico}')
        if c.division:
            partes.append(c.division)
        return ' — '.join(partes) if partes else f'ID {c.id}'

    return jsonify({
        'carros': [{
            'id':      c.id,
            'nombre':  carro_display(c),
            'serie':   c.numero_serie or '—',
            'netbooks': len(c.netbooks),
            'estado':  c.estado,
            'url':     url_for('carros.netbooks', id=c.id),
        } for c in carros],
        'netbooks': [{
            'id':      n.id,
            'serie':   n.numero_serie or '—',
            'interno': n.numero_interno or '—',
            'alumno':  alumno_nb(n),
            'carro':   f'Carro {n.carro.numero_fisico}' if n.carro and n.carro.numero_fisico else '—',
            'estado':  n.estado,
            'url':     url_for('carros.netbooks', id=n.carro_id),
        } for n in netbooks],
        'alumnos': [{
            'id':      a.id,
            'nombre':  f'{a.apellido}, {a.nombre}',
            'curso':   a.curso or '—',
            'turno':   'Mañana' if a.turno == 'M' else 'Tarde',
            'netbook': a.netbook_asignada.numero_serie if a.netbook_asignada else 'Sin netbook',
            'url':     url_for('carros.index'),
        } for a in alumnos],
    })


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
