from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        metodo = request.form.get('metodo', 'password')

        if metodo == 'credencial':
            codigo = request.form.get('codigo', '').strip().upper()
            usuario = Usuario.query.filter_by(codigo_credencial=codigo, activo=True).first()
            if usuario:
                login_user(usuario, remember=False)
                flash(f'Bienvenido, {usuario.nombre_completo}!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('Credencial no reconocida.', 'danger')

        else:  # password
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            usuario  = Usuario.query.filter_by(username=username, activo=True).first()
            if usuario and usuario.check_password(password):
                login_user(usuario, remember=request.form.get('remember'))
                flash(f'Bienvenido, {usuario.nombre_completo}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('main.dashboard'))
            else:
                flash('Usuario o contrasena incorrectos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesion cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
