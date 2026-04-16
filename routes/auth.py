from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from models import db, Usuario
from models.sesion import SesionEncargado
from datetime import datetime
import os

auth_bp = Blueprint('auth', __name__)

# ── Blueprint de Google OAuth ─────────────────────────────────────────────────
google_bp = make_google_blueprint(
    client_id     = os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET'),
    scope         = ['openid', 'https://www.googleapis.com/auth/userinfo.email',
                     'https://www.googleapis.com/auth/userinfo.profile'],
    redirect_url  = '/auth/google/callback'
)


@auth_bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/login.html')


@auth_bp.route('/auth/google/callback')
def google_callback():
    if not google.authorized:
        flash('No se pudo autenticar con Google.', 'danger')
        return redirect(url_for('auth.login'))

    # Obtener info del usuario de Google
    resp = google.get('/oauth2/v2/userinfo')
    if not resp.ok:
        flash('Error al obtener información de Google.', 'danger')
        return redirect(url_for('auth.login'))

    info   = resp.json()
    correo = info.get('email', '').lower().strip()

    # Buscar usuario en el sistema por correo
    usuario = Usuario.query.filter_by(correo=correo, activo=True).first()

    if not usuario:
        flash(f'El correo {correo} no tiene acceso al sistema. '
              f'Contactá al administrador.', 'danger')
        return redirect(url_for('auth.login'))

    login_user(usuario, remember=True)

    # ── Registrar inicio de sesión si es Encargado ────────────────────────
    if usuario.rol == 'Encargado':
        s = SesionEncargado(
            usuario_id = usuario.id,
            ip         = request.remote_addr,
            user_agent = request.user_agent.string[:300],
        )
        db.session.add(s)
        db.session.commit()
        session['sesion_id'] = s.id

    flash(f'Bienvenido, {usuario.nombre_completo}!', 'success')
    return redirect(url_for('main.dashboard'))


@auth_bp.route('/logout')
@login_required
def logout():
    # Limpiar token de Google
    if google.authorized:
        try:
            token = google_bp.token
            if token:
                google.post('/o/oauth2/revoke',
                            params={'token': token['access_token']},
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        except Exception:
            pass
        del google_bp.token

    logout_user()

    # ── Cerrar sesión registrada si existía ──────────────────────────────
    sid = session.pop('sesion_id', None)
    if sid:
        s = SesionEncargado.query.get(sid)
        if s and s.activa:
            s.activa = False
            s.fin    = datetime.utcnow()
            db.session.commit()

    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
