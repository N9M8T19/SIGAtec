"""
routes/sesiones.py
──────────────────
Blueprint: sesiones_bp
Prefijo: /sesiones

Endpoints:
  GET  /sesiones/               → listado para Directivo/Admin
  POST /sesiones/<id>/cerrar    → fuerza cierre de una sesión activa
  POST /sesiones/cerrar-todas   → cierra todas las sesiones activas de un usuario

Cómo registrar sesiones al hacer login (en routes/auth.py):
    from models.sesion import SesionEncargado
    from extensions import db
    from flask import request

    sesion = SesionEncargado(
        usuario_id = usuario.id,
        ip         = request.remote_addr,
        user_agent = request.user_agent.string[:300],
    )
    db.session.add(sesion)
    db.session.commit()
    session['sesion_id'] = sesion.id   # guardar en la Flask session

Para cerrar al hacer logout:
    from models.sesion import SesionEncargado
    from datetime import datetime

    sid = session.pop('sesion_id', None)
    if sid:
        s = SesionEncargado.query.get(sid)
        if s and s.activa:
            s.activa = False
            s.fin = datetime.utcnow()
            db.session.commit()
"""

from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, jsonify)
from flask_login import login_required, current_user

from models import db, Usuario
from models.sesion import SesionEncargado

ARG_OFFSET = timedelta(hours=-3)

sesiones_bp = Blueprint('sesiones', __name__, url_prefix='/sesiones')


# ─── Decorador de permiso ────────────────────────────────────────────────────

def solo_admin_directivo(f):
    """Restringe el acceso a roles Administrador y Directivo."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.rol not in ('Administrador', 'Directivo'):
            flash('No tenés permiso para acceder a esta sección.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _arg_now():
    return datetime.utcnow() + ARG_OFFSET


def _duracion(inicio: datetime, fin: datetime | None) -> str:
    fin_real = fin or (datetime.utcnow())
    delta = fin_real - inicio
    total = int(delta.total_seconds())
    if total < 0:
        return '—'
    h, rem = divmod(total, 3600)
    m = rem // 60
    if h:
        return f'{h}h {m:02d}m'
    return f'{m}m'


# ─── Rutas ───────────────────────────────────────────────────────────────────

@sesiones_bp.route('/')
@login_required
@solo_admin_directivo
def index():
    """
    Lista todas las sesiones (activas primero, luego historial).
    Filtros opcionales: ?usuario_id=N  ?solo_activas=1  ?fecha=YYYY-MM-DD
    """
    # Filtros
    filtro_usuario = request.args.get('usuario_id', type=int)
    solo_activas   = request.args.get('solo_activas', '0') == '1'
    filtro_fecha   = request.args.get('fecha', '')          # 'YYYY-MM-DD'

    q = (SesionEncargado.query
         .join(Usuario, SesionEncargado.usuario_id == Usuario.id)
         .order_by(SesionEncargado.activa.desc(),
                   SesionEncargado.inicio.desc()))

    if filtro_usuario:
        q = q.filter(SesionEncargado.usuario_id == filtro_usuario)

    if solo_activas:
        q = q.filter(SesionEncargado.activa == True)

    if filtro_fecha:
        try:
            d = datetime.strptime(filtro_fecha, '%Y-%m-%d')
            # El inicio se guarda en UTC; ajustamos para comparar
            inicio_utc = d - ARG_OFFSET                  # UTC equivalente del día ARG
            fin_utc    = inicio_utc + timedelta(days=1)
            q = q.filter(SesionEncargado.inicio >= inicio_utc,
                          SesionEncargado.inicio < fin_utc)
        except ValueError:
            pass

    sesiones = q.limit(200).all()  # máximo 200 registros por vista

    # Lista de encargados para el filtro de usuario
    encargados = (Usuario.query
                  .filter(Usuario.rol == 'Encargado')
                  .order_by(Usuario.apellido, Usuario.nombre)
                  .all())

    # Contadores rápidos
    total_activas = SesionEncargado.query.filter_by(activa=True).count()

    return render_template(
        'sesiones/index.html',
        sesiones        = sesiones,
        encargados      = encargados,
        total_activas   = total_activas,
        filtro_usuario  = filtro_usuario,
        solo_activas    = solo_activas,
        filtro_fecha    = filtro_fecha,
        duracion        = _duracion,
        arg_offset      = ARG_OFFSET,
    )


@sesiones_bp.route('/<int:sesion_id>/cerrar', methods=['POST'])
@login_required
@solo_admin_directivo
def cerrar_sesion(sesion_id):
    """Fuerza el cierre de una sesión activa específica."""
    s = SesionEncargado.query.get_or_404(sesion_id)

    if not s.activa:
        flash('Esa sesión ya estaba cerrada.', 'warning')
        return redirect(url_for('sesiones.index'))

    s.activa      = False
    s.fin         = datetime.utcnow()
    s.cerrada_por = current_user.id
    db.session.commit()

    flash(
        f'Sesión de {s.usuario.nombre} {s.usuario.apellido} cerrada correctamente.',
        'success'
    )
    return redirect(request.referrer or url_for('sesiones.index'))


@sesiones_bp.route('/cerrar-todas', methods=['POST'])
@login_required
@solo_admin_directivo
def cerrar_todas():
    """
    Cierra todas las sesiones activas de un usuario.
    Espera: ?usuario_id=N en el formulario o query string.
    """
    uid = request.form.get('usuario_id', type=int) \
       or request.args.get('usuario_id', type=int)

    if not uid:
        flash('No se indicó ningún usuario.', 'danger')
        return redirect(url_for('sesiones.index'))

    usuario = Usuario.query.get_or_404(uid)
    ahora   = datetime.utcnow()

    activas = SesionEncargado.query.filter_by(usuario_id=uid, activa=True).all()
    for s in activas:
        s.activa      = False
        s.fin         = ahora
        s.cerrada_por = current_user.id

    db.session.commit()

    flash(
        f'{len(activas)} sesión(es) de {usuario.nombre} {usuario.apellido} '
        'cerradas correctamente.',
        'success'
    )
    return redirect(url_for('sesiones.index'))


# ─── API JSON (opcional, para polling en tiempo real) ────────────────────────

@sesiones_bp.route('/api/activas')
@login_required
@solo_admin_directivo
def api_activas():
    """Devuelve JSON con las sesiones activas. Útil para polling/AJAX."""
    sesiones = (SesionEncargado.query
                .filter_by(activa=True)
                .join(Usuario)
                .order_by(SesionEncargado.inicio.desc())
                .all())

    resultado = []
    for s in sesiones:
        inicio_arg = s.inicio + ARG_OFFSET
        resultado.append({
            'id'         : s.id,
            'usuario_id' : s.usuario_id,
            'nombre'     : f'{s.usuario.nombre} {s.usuario.apellido}',
            'username'   : s.usuario.username,
            'ip'         : s.ip,
            'inicio'     : inicio_arg.strftime('%d/%m/%Y %H:%M'),
            'duracion'   : _duracion(s.inicio, None),
        })

    return jsonify(resultado)
