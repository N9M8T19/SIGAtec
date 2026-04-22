"""
routes/tickets_ba.py
Módulo de Tickets BA Colaborativa.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required, current_user
from models import db, Netbook, Carro
from datetime import datetime

tickets_ba_bp = Blueprint('tickets_ba', __name__, url_prefix='/tickets-ba')


# ── Modelo inline (se define en models/__init__.py, aquí solo se importa) ────
# Ver instrucciones al pie del archivo para agregar el modelo TicketBA


@tickets_ba_bp.route('/')
@login_required
def index():
    from models import TicketBA
    tickets = TicketBA.query.order_by(TicketBA.fecha_creacion.desc()).all()
    netbooks_en_servicio = Netbook.query.filter_by(estado='servicio_tecnico').all()
    carros_en_servicio = Carro.query.filter_by(estado='en_servicio').order_by(Carro.numero_fisico).all()
    return render_template('tickets_ba/index.html',
                           tickets=tickets,
                           netbooks_en_servicio=netbooks_en_servicio,
                           carros_en_servicio=carros_en_servicio)


@tickets_ba_bp.route('/nuevo', methods=['POST'])
@login_required
def nuevo():
    from models import TicketBA, TicketBANetbook
    nro_reclamo   = request.form.get('nro_reclamo', '').strip()
    observaciones = request.form.get('observaciones', '').strip()
    netbook_ids   = request.form.getlist('netbook_ids', type=int)
    carro_ids     = request.form.getlist('carro_ids',   type=int)

    if not nro_reclamo:
        flash('El N° de reclamo es obligatorio.', 'danger')
        return redirect(url_for('tickets_ba.index'))

    if not netbook_ids and not carro_ids:
        flash('Seleccioná al menos una netbook o un carro.', 'danger')
        return redirect(url_for('tickets_ba.index'))

    ticket = TicketBA(
        nro_reclamo   = nro_reclamo,
        observaciones = observaciones,
        usuario       = current_user.nombre_completo,
        fecha_creacion= datetime.utcnow(),
    )
    db.session.add(ticket)
    db.session.flush()

    for nb_id in netbook_ids:
        item = TicketBANetbook(ticket_id=ticket.id, netbook_id=nb_id)
        db.session.add(item)

    for c_id in carro_ids:
        item = TicketBANetbook(ticket_id=ticket.id, carro_id=c_id)
        db.session.add(item)

    db.session.commit()
    flash(f'Ticket #{ticket.id} creado correctamente.', 'success')
    return redirect(url_for('tickets_ba.index'))


@tickets_ba_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    from models import TicketBA
    ticket = TicketBA.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket eliminado.', 'success')
    return redirect(url_for('tickets_ba.index'))


@tickets_ba_bp.route('/pdf')
@login_required
def pdf():
    from models import TicketBA
    from services.pdf_reportes import pdf_tickets_ba
    tickets = TicketBA.query.order_by(TicketBA.fecha_creacion.desc()).all()
    buffer = pdf_tickets_ba(tickets)
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name='tickets_ba_colaborativa.pdf')


@tickets_ba_bp.route('/<int:id>/pdf')
@login_required
def pdf_ticket(id):
    from models import TicketBA
    from services.pdf_reportes import pdf_tickets_ba
    ticket = TicketBA.query.get_or_404(id)
    buffer = pdf_tickets_ba([ticket])
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'ticket_ba_{ticket.id}.pdf')
