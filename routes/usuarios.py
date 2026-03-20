from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Usuario

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')


@usuarios_bp.route('/')
@login_required
def index():
    if not current_user.tiene_permiso('estadisticas'):
        flash('No tenes permiso para acceder.', 'danger')
        return redirect(url_for('main.dashboard'))
    usuarios = Usuario.query.order_by(Usuario.apellido).all()
    return render_template('usuarios/index.html', usuarios=usuarios)


@usuarios_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenes permiso para esta accion.', 'danger')
        return redirect(url_for('usuarios.index'))

    if request.method == 'POST':
        dni      = request.form.get('dni', '').strip()
        username = request.form.get('username', '').strip()

        if Usuario.query.filter_by(dni=dni).first():
            flash(f'Ya existe un usuario con DNI {dni}.', 'danger')
            return redirect(url_for('usuarios.nuevo'))
        if Usuario.query.filter_by(username=username).first():
            flash(f'El nombre de usuario {username} ya esta en uso.', 'danger')
            return redirect(url_for('usuarios.nuevo'))

        usuario = Usuario(
            dni      = dni,
            nombre   = request.form.get('nombre', '').strip(),
            apellido = request.form.get('apellido', '').strip(),
            username = username,
            rol      = request.form.get('rol', 'Encargado'),
            codigo_credencial = Usuario.generar_codigo()
        )
        password = request.form.get('password', '').strip()
        if password:
            usuario.set_password(password)

        db.session.add(usuario)
        db.session.commit()
        flash(f'Usuario {usuario.nombre_completo} creado. Codigo: {usuario.codigo_credencial}', 'success')
        return redirect(url_for('usuarios.index'))

    return render_template('usuarios/form.html', usuario=None)


@usuarios_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenes permiso para esta accion.', 'danger')
        return redirect(url_for('usuarios.index'))

    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        usuario.nombre   = request.form.get('nombre', '').strip()
        usuario.apellido = request.form.get('apellido', '').strip()
        usuario.rol      = request.form.get('rol', usuario.rol)
        password = request.form.get('password', '').strip()
        if password:
            usuario.set_password(password)
        db.session.commit()
        flash(f'Usuario {usuario.nombre_completo} actualizado.', 'success')
        return redirect(url_for('usuarios.index'))

    return render_template('usuarios/form.html', usuario=usuario)


@usuarios_bp.route('/<int:id>/baja', methods=['POST'])
@login_required
def dar_baja(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenes permiso.', 'danger')
        return redirect(url_for('usuarios.index'))
    usuario = Usuario.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('No podes darte de baja a vos mismo.', 'danger')
        return redirect(url_for('usuarios.index'))
    usuario.activo = False
    db.session.commit()
    flash(f'{usuario.nombre_completo} dado de baja.', 'warning')
    return redirect(url_for('usuarios.index'))


@usuarios_bp.route('/<int:id>/reactivar', methods=['POST'])
@login_required
def reactivar(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenes permiso.', 'danger')
        return redirect(url_for('usuarios.index'))
    usuario = Usuario.query.get_or_404(id)
    usuario.activo = True
    db.session.commit()
    flash(f'{usuario.nombre_completo} reactivado.', 'success')
    return redirect(url_for('usuarios.index'))
