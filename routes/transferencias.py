"""
routes/transferencias.py
Transferencia de netbooks entre carros con generación de PDF.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Carro, Netbook

transferencias_bp = Blueprint('transferencias', __name__, url_prefix='/transferencias')


@transferencias_bp.route('/')
@login_required
def index():
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('main.dashboard'))
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    return render_template('transferencias/index.html', carros=carros)


@transferencias_bp.route('/seleccionar', methods=['POST'])
@login_required
def seleccionar():
    """Paso 1 — elegir carro origen y destino, mostrar netbooks disponibles."""
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('transferencias.index'))

    carro_origen_id  = request.form.get('carro_origen_id', type=int)
    carro_destino_id = request.form.get('carro_destino_id', type=int)

    if not carro_origen_id or not carro_destino_id:
        flash('Seleccioná carro origen y destino.', 'danger')
        return redirect(url_for('transferencias.index'))

    if carro_origen_id == carro_destino_id:
        flash('El carro origen y destino no pueden ser el mismo.', 'danger')
        return redirect(url_for('transferencias.index'))

    carro_origen  = Carro.query.get_or_404(carro_origen_id)
    carro_destino = Carro.query.get_or_404(carro_destino_id)
    netbooks      = [nb for nb in carro_origen.netbooks if nb.estado == 'operativa']

    return render_template('transferencias/seleccionar.html',
                           carro_origen=carro_origen,
                           carro_destino=carro_destino,
                           netbooks=netbooks)


@transferencias_bp.route('/ejecutar', methods=['POST'])
@login_required
def ejecutar():
    """Paso 2 — ejecutar la transferencia y generar PDF."""
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('transferencias.index'))

    carro_origen_id  = request.form.get('carro_origen_id', type=int)
    carro_destino_id = request.form.get('carro_destino_id', type=int)
    netbook_ids      = request.form.getlist('netbook_ids', type=int)
    generar_pdf      = request.form.get('generar_pdf') == '1'

    if not netbook_ids:
        flash('Seleccioná al menos una netbook para transferir.', 'danger')
        return redirect(url_for('transferencias.index'))

    carro_origen  = Carro.query.get_or_404(carro_origen_id)
    carro_destino = Carro.query.get_or_404(carro_destino_id)

    netbooks_transferidas = []
    for nb_id in netbook_ids:
        nb = Netbook.query.get(nb_id)
        if nb and nb.carro_id == carro_origen_id:
            nb.carro_id = carro_destino_id
            netbooks_transferidas.append(nb)

    db.session.commit()

    flash(f'✅ {len(netbooks_transferidas)} netbook(s) transferida(s) de '
          f'{carro_origen.display} a {carro_destino.display}.', 'success')

    if generar_pdf and netbooks_transferidas:
        from services.pdf_reportes import pdf_transferencia
        return pdf_transferencia(netbooks_transferidas, carro_origen,
                                 carro_destino, current_user.nombre_completo)

    return redirect(url_for('carros.index'))
