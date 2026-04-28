from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Carro, Netbook, Alumno

netbooks_bp = Blueprint('netbooks', __name__, url_prefix='/netbooks')


@netbooks_bp.route('/carro/<int:carro_id>/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo(carro_id):
    carro = Carro.query.get_or_404(carro_id)

    if request.method == 'POST':
        numero_serie   = request.form.get('numero_serie', '').strip()
        numero_interno = request.form.get('numero_interno', '').strip()

        # Validación: número interno duplicado dentro del mismo carro
        if numero_interno:
            dup_interno = Netbook.query.filter_by(
                carro_id=carro_id,
                numero_interno=numero_interno
            ).first()
            if dup_interno:
                flash(
                    f'El número interno <strong>{numero_interno}</strong> ya existe '
                    f'en el carro <strong>{carro.display}</strong>.',
                    'danger'
                )
                return render_template('netbooks/form.html', carro=carro, netbook=None)

        # Validación: número de serie duplicado
        existente = Netbook.query.filter_by(numero_serie=numero_serie).first()
        if existente and numero_serie:
            flash(
                f'El número de serie <strong>{numero_serie}</strong> ya está registrado '
                f'en el carro <strong>{existente.carro.display}</strong> '
                f'(N° interno {existente.numero_interno}).',
                'danger'
            )
            return render_template('netbooks/form.html', carro=carro, netbook=None)

        nb = Netbook(
            carro_id       = carro_id,
            numero_interno = numero_interno,
            numero_serie   = numero_serie,
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
        numero_serie   = request.form.get('numero_serie', '').strip()
        numero_interno = request.form.get('numero_interno', '').strip()

        # Validación: número interno duplicado dentro del mismo carro (excluyendo la netbook actual)
        if numero_interno:
            dup_interno = Netbook.query.filter(
                Netbook.carro_id       == nb.carro_id,
                Netbook.numero_interno == numero_interno,
                Netbook.id             != id
            ).first()
            if dup_interno:
                flash(
                    f'El número interno <strong>{numero_interno}</strong> ya existe '
                    f'en el carro <strong>{nb.carro.display}</strong>.',
                    'danger'
                )
                return render_template('netbooks/form.html', carro=nb.carro, netbook=nb)

        # Validación: número de serie duplicado (excluyendo la netbook actual)
        existente = Netbook.query.filter(
            Netbook.numero_serie == numero_serie,
            Netbook.id != id
        ).first()
        if existente and numero_serie:
            flash(
                f'El número de serie <strong>{numero_serie}</strong> ya está registrado '
                f'en el carro <strong>{existente.carro.display}</strong> '
                f'(N° interno {existente.numero_interno}).',
                'danger'
            )
            return render_template('netbooks/form.html', carro=nb.carro, netbook=nb)

        nb.numero_interno = numero_interno
        nb.numero_serie   = numero_serie
        nb.alumno         = request.form.get('alumno', '').strip()
        db.session.commit()
        flash('Netbook actualizada.', 'success')
        return redirect(url_for('carros.netbooks', id=nb.carro_id))

    return render_template('netbooks/form.html', carro=nb.carro, netbook=nb)


@netbooks_bp.route('/verificar-serie')
@login_required
def verificar_serie():
    """AJAX — verifica si un número de serie ya existe. excluir_id se usa en edición."""
    numero_serie = request.args.get('numero_serie', '').strip()
    excluir_id   = request.args.get('excluir_id', type=int)

    if not numero_serie:
        return jsonify({'duplicado': False})

    query = Netbook.query.filter_by(numero_serie=numero_serie)
    if excluir_id:
        query = query.filter(Netbook.id != excluir_id)

    existente = query.first()
    if existente:
        return jsonify({
            'duplicado':       True,
            'carro':           existente.carro.display,
            'numero_interno':  existente.numero_interno,
        })
    return jsonify({'duplicado': False})


@netbooks_bp.route('/verificar-numero-interno')
@login_required
def verificar_numero_interno():
    """AJAX — verifica si un número interno ya existe en el mismo carro. excluir_id se usa en edición."""
    numero_interno = request.args.get('numero_interno', '').strip()
    carro_id       = request.args.get('carro_id', type=int)
    excluir_id     = request.args.get('excluir_id', type=int)

    if not numero_interno or not carro_id:
        return jsonify({'duplicado': False})

    query = Netbook.query.filter_by(carro_id=carro_id, numero_interno=numero_interno)
    if excluir_id:
        query = query.filter(Netbook.id != excluir_id)

    existente = query.first()
    if existente:
        return jsonify({'duplicado': True})
    return jsonify({'duplicado': False})


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
    netbooks = Netbook.query.filter_by(estado='servicio_tecnico').order_by(db.func.cast(Netbook.numero_interno, db.Integer)).all()
    carros_servicio = Carro.query.filter_by(estado='en_servicio').order_by(Carro.numero_fisico).all()
    return render_template('netbooks/servicio_tecnico.html',
                           netbooks=netbooks,
                           carros_servicio=carros_servicio)


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
    """Da de baja una netbook: guarda el PDF en sesion, elimina la BD y redirige."""
    from datetime import datetime
    import base64
    from flask import session
    from services.pdf_reportes import generar_pdf_baja_netbook

    nb     = Netbook.query.get_or_404(id)
    motivo = request.form.get('motivo_baja', '').strip()

    if not motivo:
        flash('El motivo de baja es obligatorio.', 'danger')
        return redirect(url_for('carros.netbooks', id=nb.carro_id))

    nb.motivo_baja  = motivo
    nb.fecha_baja   = datetime.utcnow()
    nb.usuario_baja = current_user.nombre_completo

    # Generar PDF antes de borrar
    buffer = generar_pdf_baja_netbook(nb)
    nombre = f'baja_netbook_{nb.numero_interno or nb.id}.pdf'

    carro_id = nb.carro_id

    # Guardar PDF en sesion (base64) para descargarlo luego
    session['pdf_baja'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
    session['pdf_baja_nombre'] = nombre

    db.session.delete(nb)
    db.session.commit()

    flash('Netbook dada de baja correctamente.', 'success')
    return redirect(url_for('carros.netbooks', id=carro_id) + '?descargar_baja=1')


@netbooks_bp.route('/baja-masiva', methods=['POST'])
@login_required
def baja_masiva():
    """Da de baja múltiples netbooks de una vez."""
    ids      = request.form.getlist('netbook_ids')
    carro_id = request.form.get('carro_id', type=int)

    if not ids:
        flash('No seleccionaste ninguna netbook.', 'warning')
        return redirect(url_for('carros.netbooks', id=carro_id))

    eliminadas = 0
    for nid in ids:
        nb = Netbook.query.get(int(nid))
        if nb:
            if not carro_id:
                carro_id = nb.carro_id
            db.session.delete(nb)
            eliminadas += 1

    db.session.commit()
    flash(f'{eliminadas} netbook{"s" if eliminadas != 1 else ""} dadas de baja.', 'success')
    return redirect(url_for('carros.netbooks', id=carro_id))


@netbooks_bp.route('/descargar-baja-pdf')
@login_required
def descargar_baja_pdf():
    """Descarga el PDF de baja guardado en sesion."""
    import base64
    from io import BytesIO
    from flask import session, send_file

    pdf_b64 = session.pop('pdf_baja', None)
    nombre  = session.pop('pdf_baja_nombre', 'baja_netbook.pdf')

    if not pdf_b64:
        flash('No hay PDF de baja disponible.', 'warning')
        return redirect(url_for('carros.index'))

    buffer = BytesIO(base64.b64decode(pdf_b64))
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=nombre)
