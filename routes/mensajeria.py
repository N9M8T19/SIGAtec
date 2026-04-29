"""
routes/mensajeria.py
Mensajería interna — solo Encargado, Directivo y Administrador.
Canales: general | servicio_tecnico | prestamos | avisos
"""
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Usuario
from datetime import datetime, timedelta

mensajeria_bp = Blueprint('mensajeria', __name__, url_prefix='/mensajeria')

ARG_OFFSET = timedelta(hours=-3)

# ── Canales disponibles ────────────────────────────────────────────────────────
CANALES = {
    'general':          {'label': 'General',           'icon': 'fa-comments',       'color': 'blue'},
    'servicio_tecnico': {'label': 'Servicio Técnico',  'icon': 'fa-tools',          'color': 'orange'},
    'prestamos':        {'label': 'Préstamos',         'icon': 'fa-key',            'color': 'green'},
    'avisos':           {'label': 'Avisos',            'icon': 'fa-bullhorn',       'color': 'red'},
}

# Avisos rápidos predefinidos por canal
AVISOS_RAPIDOS = {
    'general':          [],
    'servicio_tecnico': [
        '🔧 Hay un equipo en servicio técnico.',
        '⚠️ Carro enviado a servicio técnico.',
        '✅ Equipo recuperado del servicio técnico.',
        '🛠️ Técnico en el establecimiento.',
    ],
    'prestamos': [
        '⏰ Préstamo con demora — verificar devolución.',
        '🔑 Carro sin devolver pasado el horario.',
        '📋 Recordar registrar la devolución.',
    ],
    'avisos': [
        '📢 Reunión de personal.',
        '🚫 Sistema en mantenimiento.',
        '✅ Sistema restaurado.',
        '⚠️ Atención: novedad importante.',
    ],
}


def _solo_equipo(f):
    """Decorador: solo usuarios autenticados (todos los roles tienen acceso)."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def _arg_now():
    return datetime.utcnow() + ARG_OFFSET


def _fmt_hora(dt_utc):
    if dt_utc is None:
        return '—'
    arg = dt_utc + ARG_OFFSET
    hoy = _arg_now().date()
    if arg.date() == hoy:
        return arg.strftime('%H:%M')
    return arg.strftime('%d/%m %H:%M')


# ── Modelo dinámico (evita import circular con __init__.py) ───────────────────
_Mensaje     = None
_MensajeLeid = None


def _get_models():
    global _Mensaje, _MensajeLeid
    if _Mensaje is None:
        class Mensaje(db.Model):
            __tablename__ = 'mensajes'
            id           = db.Column(db.Integer, primary_key=True)
            canal        = db.Column(db.String(50),  nullable=False, default='general')
            autor_id     = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
            autor_nombre = db.Column(db.String(200))
            autor_rol    = db.Column(db.String(50))
            contenido    = db.Column(db.Text, nullable=False)
            tipo         = db.Column(db.String(30), nullable=False, default='normal')
            creado_en    = db.Column(db.DateTime, default=datetime.utcnow)
            leidos       = db.relationship('MensajeLeid', backref='mensaje',
                                           lazy=True, cascade='all, delete-orphan')
            autor        = db.relationship('Usuario', foreign_keys=[autor_id])

        class MensajeLeid(db.Model):
            __tablename__ = 'mensajes_leidos'
            id         = db.Column(db.Integer, primary_key=True)
            mensaje_id = db.Column(db.Integer, db.ForeignKey('mensajes.id'), nullable=False)
            usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
            leido_en   = db.Column(db.DateTime, default=datetime.utcnow)
            __table_args__ = (db.UniqueConstraint('mensaje_id', 'usuario_id'),)

        _Mensaje     = Mensaje
        _MensajeLeid = MensajeLeid

    return _Mensaje, _MensajeLeid


# ── Vistas ─────────────────────────────────────────────────────────────────────

@mensajeria_bp.route('/')
@login_required
@_solo_equipo
def index():
    Mensaje, MensajeLeid = _get_models()
    canal_activo = request.args.get('canal', 'general')
    if canal_activo not in CANALES:
        canal_activo = 'general'

    # Mensajes del canal — últimos 100
    mensajes = (Mensaje.query
                .filter_by(canal=canal_activo)
                .order_by(Mensaje.creado_en.asc())
                .limit(100)
                .all())

    # Marcar todos como leídos
    for m in mensajes:
        ya = MensajeLeid.query.filter_by(
            mensaje_id=m.id, usuario_id=current_user.id).first()
        if not ya:
            db.session.add(MensajeLeid(
                mensaje_id=m.id, usuario_id=current_user.id))
    db.session.commit()

    # Contar no leídos por canal (para badges)
    badges = {}
    for c in CANALES:
        leidos_ids = db.session.query(MensajeLeid.mensaje_id).filter_by(
            usuario_id=current_user.id).subquery()
        badges[c] = (Mensaje.query
                     .filter_by(canal=c)
                     .filter(Mensaje.id.notin_(leidos_ids))
                     .count())

    return render_template(
        'mensajeria/index.html',
        canal_activo=canal_activo,
        canales=CANALES,
        mensajes=mensajes,
        badges=badges,
        avisos_rapidos=AVISOS_RAPIDOS.get(canal_activo, []),
        fmt_hora=_fmt_hora,
    )


@mensajeria_bp.route('/enviar', methods=['POST'])
@login_required
@_solo_equipo
def enviar():
    Mensaje, _ = _get_models()
    data = request.get_json(silent=True) or {}
    canal    = data.get('canal', 'general')
    contenido = (data.get('contenido') or '').strip()
    tipo     = data.get('tipo', 'normal')  # normal | aviso

    if canal not in CANALES:
        return jsonify({'ok': False, 'error': 'Canal inválido'}), 400
    if not contenido:
        return jsonify({'ok': False, 'error': 'Mensaje vacío'}), 400
    if len(contenido) > 1000:
        return jsonify({'ok': False, 'error': 'Mensaje demasiado largo'}), 400

    m = Mensaje(
        canal=canal,
        autor_id=current_user.id,
        autor_nombre=current_user.nombre_completo,
        autor_rol=current_user.rol,
        contenido=contenido,
        tipo=tipo,
    )
    db.session.add(m)
    db.session.commit()

    return jsonify({
        'ok': True,
        'mensaje': {
            'id':       m.id,
            'autor':    m.autor_nombre,
            'rol':      m.autor_rol,
            'contenido':m.contenido,
            'tipo':     m.tipo,
            'hora':     _fmt_hora(m.creado_en),
            'propio':   True,
        }
    })


@mensajeria_bp.route('/poll')
@login_required
@_solo_equipo
def poll():
    """Devuelve mensajes nuevos desde un ID dado + conteo no leídos por canal."""
    Mensaje, MensajeLeid = _get_models()
    canal    = request.args.get('canal', 'general')
    desde_id = int(request.args.get('desde', 0))

    if canal not in CANALES:
        return jsonify({'mensajes': [], 'badges': {}})

    nuevos = (Mensaje.query
              .filter_by(canal=canal)
              .filter(Mensaje.id > desde_id)
              .order_by(Mensaje.creado_en.asc())
              .all())

    # Marcar como leídos
    for m in nuevos:
        ya = MensajeLeid.query.filter_by(
            mensaje_id=m.id, usuario_id=current_user.id).first()
        if not ya:
            db.session.add(MensajeLeid(
                mensaje_id=m.id, usuario_id=current_user.id))
    db.session.commit()

    # Badges
    badges = {}
    for c in CANALES:
        leidos_ids = db.session.query(MensajeLeid.mensaje_id).filter_by(
            usuario_id=current_user.id).subquery()
        badges[c] = (Mensaje.query
                     .filter_by(canal=c)
                     .filter(Mensaje.id.notin_(leidos_ids))
                     .count())

    return jsonify({
        'mensajes': [{
            'id':       m.id,
            'autor':    m.autor_nombre,
            'rol':      m.autor_rol,
            'contenido':m.contenido,
            'tipo':     m.tipo,
            'hora':     _fmt_hora(m.creado_en),
            'propio':   m.autor_id == current_user.id,
        } for m in nuevos],
        'badges': badges,
    })


@mensajeria_bp.route('/no_leidos')
@login_required
def no_leidos():
    """Endpoint liviano para el badge del sidebar (todas las páginas)."""
    try:
        Mensaje, MensajeLeid = _get_models()
        leidos_ids = db.session.query(MensajeLeid.mensaje_id).filter_by(
            usuario_id=current_user.id).subquery()
        total = Mensaje.query.filter(Mensaje.id.notin_(leidos_ids)).count()
        return jsonify({'total': total})
    except Exception:
        return jsonify({'total': 0})
