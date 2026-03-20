from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Carro, Netbook

carros_bp = Blueprint('carros', __name__, url_prefix='/carros')


@carros_bp.route('/')
@login_required
def index():
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    return render_template('carros/index.html', carros=carros)


@carros_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenes permiso para esta accion.', 'danger')
        return redirect(url_for('carros.index'))

    if request.method == 'POST':
        carro = Carro(
            numero_fisico = request.form.get('numero_fisico', '').strip(),
            numero_serie  = request.form.get('numero_serie', '').strip(),
            division      = request.form.get('division', '').strip(),
            aula          = request.form.get('aula', '').strip(),
            sheet_url     = request.form.get('sheet_url', '').strip(),
        )
        db.session.add(carro)
        db.session.commit()
        flash(f'Carro {carro.display} creado correctamente.', 'success')
        return redirect(url_for('carros.index'))

    return render_template('carros/form.html', carro=None)


@carros_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    carro = Carro.query.get_or_404(id)

    if request.method == 'POST':
        carro.numero_fisico = request.form.get('numero_fisico', '').strip()
        carro.numero_serie  = request.form.get('numero_serie', '').strip()
        carro.division      = request.form.get('division', '').strip()
        carro.aula          = request.form.get('aula', '').strip()
        carro.sheet_url     = request.form.get('sheet_url', '').strip()
        db.session.commit()
        flash(f'Carro {carro.display} actualizado.', 'success')
        return redirect(url_for('carros.index'))

    return render_template('carros/form.html', carro=carro)


@carros_bp.route('/<int:id>/baja', methods=['POST'])
@login_required
def dar_baja(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenes permiso para esta accion.', 'danger')
        return redirect(url_for('carros.index'))

    carro = Carro.query.get_or_404(id)
    carro.estado = 'baja'
    db.session.commit()
    flash(f'Carro {carro.display} dado de baja.', 'warning')
    return redirect(url_for('carros.index'))


@carros_bp.route('/<int:id>/netbooks')
@login_required
def netbooks(id):
    carro = Carro.query.get_or_404(id)
    return render_template('carros/netbooks.html', carro=carro)
