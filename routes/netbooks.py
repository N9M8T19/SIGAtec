from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Carro, Netbook

netbooks_bp = Blueprint('netbooks', __name__, url_prefix='/netbooks')


@netbooks_bp.route('/carro/<int:carro_id>/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo(carro_id):
    carro = Carro.query.get_or_404(carro_id)

    if request.method == 'POST':
        nb = Netbook(
            carro_id       = carro_id,
            numero_interno = request.form.get('numero_interno', '').strip(),
            numero_serie   = request.form.get('numero_serie', '').strip(),
            alumno         = request.form.get('alumno', '').strip(),
        )
        db.session.add(nb)
        db.session.commit()
        flash('Netbook agregada.', 'success')
        return redirect(url_for('carros.netbooks', id=carro_id))

    return render_template('netbooks/form.html', carro=carro, netbook=None)


@netbooks_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    nb = Netbook.query.get_or_404(id)

    if request.method == 'POST':
        nb.numero_interno = request.form.get('numero_interno', '').strip()
        nb.numero_serie   = request.form.get('numero_serie', '').strip()
        nb.alumno         = request.form.get('alumno', '').strip()
        db.session.commit()
        flash('Netbook actualizada.', 'success')
        return redirect(url_for('carros.netbooks', id=nb.carro_id))

    return render_template('netbooks/form.html', carro=nb.carro, netbook=nb)


@netbooks_bp.route('/<int:id>/servicio', methods=['POST'])
@login_required
def marcar_servicio(id):
    nb = Netbook.query.get_or_404(id)
    nb.estado   = 'servicio_tecnico'
    nb.problema = request.form.get('problema', '').strip()
    db.session.commit()
    flash(f'Netbook {nb.numero_interno} enviada a servicio tecnico.', 'warning')
    return redirect(url_for('carros.netbooks', id=nb.carro_id))


@netbooks_bp.route('/<int:id>/reparada', methods=['POST'])
@login_required
def marcar_reparada(id):
    nb = Netbook.query.get_or_404(id)
    nb.estado   = 'operativa'
    nb.problema = ''
    db.session.commit()
    flash(f'Netbook {nb.numero_interno} marcada como operativa.', 'success')
    return redirect(url_for('carros.netbooks', id=nb.carro_id))


@netbooks_bp.route('/servicio-tecnico')
@login_required
def servicio_tecnico():
    netbooks = Netbook.query.filter_by(estado='servicio_tecnico').all()
    return render_template('netbooks/servicio_tecnico.html', netbooks=netbooks)
