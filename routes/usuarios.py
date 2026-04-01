from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Usuario

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')


@usuarios_bp.route('/')
@login_required
def index():
    if not current_user.tiene_permiso('estadisticas'):
        flash('Credenciales no válidas para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))
    usuarios = Usuario.query.order_by(Usuario.apellido).all()
    return render_template('usuarios/index.html', usuarios=usuarios)


@usuarios_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas para esta acción.', 'danger')
        return redirect(url_for('usuarios.index'))

    if request.method == 'POST':
        dni      = request.form.get('dni', '').strip()
        username = request.form.get('username', '').strip()
        correo   = request.form.get('correo', '').strip().lower()

        if Usuario.query.filter_by(dni=dni).first():
            flash(f'Ya existe un usuario con DNI {dni}.', 'danger')
            return redirect(url_for('usuarios.nuevo'))
        if Usuario.query.filter_by(username=username).first():
            flash(f'El nombre de usuario {username} ya está en uso.', 'danger')
            return redirect(url_for('usuarios.nuevo'))
        if correo and Usuario.query.filter_by(correo=correo).first():
            flash(f'El correo {correo} ya está en uso por otro usuario.', 'danger')
            return redirect(url_for('usuarios.nuevo'))

        usuario = Usuario(
            dni               = dni,
            nombre            = request.form.get('nombre', '').strip(),
            apellido          = request.form.get('apellido', '').strip(),
            username          = username,
            correo            = correo,
            rol               = request.form.get('rol', 'Encargado'),
            activo            = True,
            codigo_credencial = Usuario.generar_codigo()
        )
        db.session.add(usuario)
        db.session.commit()
        flash(f'Usuario {usuario.nombre_completo} creado correctamente.', 'success')
        return redirect(url_for('usuarios.index'))

    return render_template('usuarios/form.html', usuario=None)


@usuarios_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas para esta acción.', 'danger')
        return redirect(url_for('usuarios.index'))

    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        nuevo_username = request.form.get('username', '').strip()
        correo_nuevo   = request.form.get('correo', '').strip().lower()

        # Validar username único
        if nuevo_username and nuevo_username != usuario.username:
            otro = Usuario.query.filter_by(username=nuevo_username).first()
            if otro and otro.id != usuario.id:
                flash(f'El nombre de usuario "{nuevo_username}" ya está en uso.', 'danger')
                return redirect(url_for('usuarios.editar', id=id))

        # Validar correo único
        if correo_nuevo:
            otro = Usuario.query.filter_by(correo=correo_nuevo).first()
            if otro and otro.id != usuario.id:
                flash(f'El correo {correo_nuevo} ya está en uso por otro usuario.', 'danger')
                return redirect(url_for('usuarios.editar', id=id))

        usuario.nombre   = request.form.get('nombre', '').strip()
        usuario.apellido = request.form.get('apellido', '').strip()
        usuario.correo   = correo_nuevo
        usuario.rol      = request.form.get('rol', usuario.rol)

        if nuevo_username:
            usuario.username = nuevo_username

        db.session.commit()
        flash(f'Usuario {usuario.nombre_completo} actualizado correctamente.', 'success')
        return redirect(url_for('usuarios.index'))

    return render_template('usuarios/form.html', usuario=usuario)


@usuarios_bp.route('/mi-perfil', methods=['GET', 'POST'])
@login_required
def mi_perfil():
    usuario = current_user

    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        username = request.form.get('username', '').strip()

        if nombre:
            usuario.nombre = nombre
        if apellido:
            usuario.apellido = apellido

        if username and username != usuario.username:
            existe = Usuario.query.filter_by(username=username).first()
            if existe:
                flash(f'El nombre de usuario "{username}" ya está en uso.', 'danger')
                return redirect(url_for('usuarios.mi_perfil'))
            usuario.username = username

        db.session.commit()
        flash('Tu perfil fue actualizado correctamente.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('usuarios/mi_perfil.html', usuario=usuario)


@usuarios_bp.route('/<int:id>/baja', methods=['POST'])
@login_required
def dar_baja(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('usuarios.index'))
    usuario = Usuario.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('No podés darte de baja a vos mismo.', 'danger')
        return redirect(url_for('usuarios.index'))
    usuario.activo = False
    db.session.commit()
    flash(f'{usuario.nombre_completo} dado de baja.', 'warning')
    return redirect(url_for('usuarios.index'))


@usuarios_bp.route('/<int:id>/reactivar', methods=['POST'])
@login_required
def reactivar(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('usuarios.index'))
    usuario = Usuario.query.get_or_404(id)
    usuario.activo = True
    db.session.commit()
    flash(f'{usuario.nombre_completo} reactivado.', 'success')
    return redirect(url_for('usuarios.index'))
