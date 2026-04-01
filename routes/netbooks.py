from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Carro, Netbook, Alumno

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

    # Volver a donde vino: si hay 'origen' en el form, ir ahí
    origen = request.form.get('origen', '')
    if origen == 'servicio_tecnico':
        return redirect(url_for('netbooks.servicio_tecnico'))
    return redirect(url_for('carros.netbooks', id=nb.carro_id))


@netbooks_bp.route('/servicio-tecnico')
@login_required
def servicio_tecnico():
    netbooks = Netbook.query.filter_by(estado='servicio_tecnico').all()
    return render_template('netbooks/servicio_tecnico.html', netbooks=netbooks)


@netbooks_bp.route('/<int:id>/guardar-reclamo', methods=['POST'])
@login_required
def guardar_reclamo(id):
    """Guarda el número de reclamo Mi BA en la netbook."""
    nb = Netbook.query.get_or_404(id)
    nb.nro_reclamo = request.form.get('nro_reclamo', '').strip()
    db.session.commit()
    flash(f'N° de reclamo guardado para netbook {nb.numero_interno}.', 'success')
    return redirect(url_for('netbooks.servicio_tecnico'))


# ─────────────────────────────────────────────────────────────────────────────
#  ASIGNACIÓN DE ALUMNOS
# ─────────────────────────────────────────────────────────────────────────────

@netbooks_bp.route('/buscar-alumno')
@login_required
def buscar_alumno():
    """Endpoint AJAX — busca alumnos por nombre, apellido o DNI, filtrado por turno."""
    q     = request.args.get('q', '').strip()
    turno = request.args.get('turno', '')   # 'M' o 'T'
    if len(q) < 2:
        return jsonify([])

    query = Alumno.query.filter(
        db.or_(
            Alumno.apellido.ilike(f'%{q}%'),
            Alumno.nombre.ilike(f'%{q}%'),
            Alumno.dni.ilike(f'%{q}%')
        )
    )
    if turno in ('M', 'T'):
        query = query.filter(Alumno.turno == turno)

    alumnos = query.order_by(Alumno.apellido, Alumno.nombre).limit(15).all()

    turno_label = {'M': 'Mañana', 'T': 'Tarde'}
    return jsonify([
        {
            'id':    a.id,
            'texto': f'{a.apellido}, {a.nombre} — DNI {a.dni} ({a.curso} {turno_label.get(a.turno, a.turno)})',
        }
        for a in alumnos
    ])


@netbooks_bp.route('/<int:netbook_id>/asignar-alumno', methods=['POST'])
@login_required
def asignar_alumno(netbook_id):
    """Asigna un alumno a una netbook según el turno."""
    netbook   = Netbook.query.get_or_404(netbook_id)
    alumno_id = request.form.get('alumno_id', type=int)
    turno     = request.form.get('turno', '')   # 'M' o 'T'

    if not alumno_id or turno not in ('M', 'T'):
        flash('Datos incompletos para asignar.', 'danger')
        return redirect(url_for('carros.netbooks', id=netbook.carro_id))

    alumno = Alumno.query.get_or_404(alumno_id)

    if turno == 'M':
        netbook.alumno_manana_id = alumno.id
        turno_label = 'Mañana'
    else:
        netbook.alumno_tarde_id = alumno.id
        turno_label = 'Tarde'

    db.session.commit()
    flash(f'Netbook {netbook.numero_interno} — Turno {turno_label} asignada a {alumno.apellido}, {alumno.nombre}.', 'success')
    return redirect(url_for('carros.netbooks', id=netbook.carro_id))


@netbooks_bp.route('/<int:netbook_id>/desasignar-alumno', methods=['POST'])
@login_required
def desasignar_alumno(netbook_id):
    """Quita la asignación de alumno de un turno específico."""
    netbook = Netbook.query.get_or_404(netbook_id)
    turno   = request.form.get('turno', '')

    if turno == 'M':
        netbook.alumno_manana_id = None
        turno_label = 'Mañana'
    elif turno == 'T':
        netbook.alumno_tarde_id = None
        turno_label = 'Tarde'
    else:
        netbook.alumno_manana_id = None
        netbook.alumno_tarde_id  = None
        turno_label = 'ambos turnos'

    db.session.commit()
    flash(f'Netbook {netbook.numero_interno} — {turno_label} desasignada.', 'success')
    return redirect(url_for('carros.netbooks', id=netbook.carro_id))


# ─────────────────────────────────────────────────────────────────────────────
#  BAJA DE NETBOOK
# ─────────────────────────────────────────────────────────────────────────────

@netbooks_bp.route('/<int:id>/dar-de-baja', methods=['POST'])
@login_required
def dar_de_baja(id):
    """Da de baja una netbook: genera el PDF y la elimina de la BD."""
    from services.pdf_reportes import generar_pdf_baja_netbook
    from flask import send_file
    from datetime import datetime

    nb     = Netbook.query.get_or_404(id)
    motivo = request.form.get('motivo_baja', '').strip()

    if not motivo:
        flash('El motivo de baja es obligatorio.', 'danger')
        return redirect(url_for('carros.netbooks', id=nb.carro_id))

    # Guardar datos para el PDF antes de borrar
    nb.motivo_baja  = motivo
    nb.fecha_baja   = datetime.utcnow()
    nb.usuario_baja = current_user.nombre_completo

    # Generar PDF con los datos completos
    buffer = generar_pdf_baja_netbook(nb)
    nombre = f'baja_netbook_{nb.numero_interno or nb.id}.pdf'

    carro_id = nb.carro_id

    # Borrar el registro de la BD
    db.session.delete(nb)
    db.session.commit()

    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=nombre)
