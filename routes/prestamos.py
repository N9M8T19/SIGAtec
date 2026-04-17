from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Carro, Docente, PrestamoCarro, PrestamoNetbook, PrestamoNetbookItem, Netbook, ConfigEspacioDigital
from datetime import datetime, timedelta
import random, string

prestamos_bp = Blueprint('prestamos', __name__, url_prefix='/prestamos')

# Mapeo de hora actual a turno
TURNO_MANANA = 'Manana'
TURNO_TARDE  = 'Tarde'
TURNO_NOCHE  = 'Noche'

def _turno_actual():
    """Retorna el turno según la hora actual (Argentina UTC-3)."""
    ARG_OFFSET = timedelta(hours=-3)
    hora = (datetime.utcnow() + ARG_OFFSET).hour
    if 7 <= hora < 13:
        return TURNO_MANANA
    elif 13 <= hora < 18:
        return TURNO_TARDE
    else:
        return TURNO_NOCHE


def _docente_puede_pedir(docente):
    """
    Verifica si el docente puede pedir en el turno actual.
    Retorna (puede, mensaje)
    """
    if not docente.turno:
        return True, ''

    turno_actual = _turno_actual()
    turno_doc    = docente.turno.strip()

    # Turnos que abarcan múltiples
    if 'y' in turno_doc.lower() or turno_doc.lower() == 'varios':
        return True, ''

    # Turno único — verificar coincidencia
    turnos_validos = {
        TURNO_MANANA: ['manana', 'mañana', 'morning'],
        TURNO_TARDE:  ['tarde', 'afternoon'],
        TURNO_NOCHE:  ['noche', 'night', 'vespertino'],
    }

    turno_doc_lower = turno_doc.lower()
    for turno, palabras in turnos_validos.items():
        if any(p in turno_doc_lower for p in palabras):
            if turno == turno_actual:
                return True, ''
            else:
                return False, (f'{docente.nombre_completo} es docente del turno '
                               f'{turno_doc} y actualmente es turno {turno_actual}. '
                               f'No se puede registrar el préstamo.')

    return True, ''


def _gen_codigo(prefijo='P'):
    while True:
        codigo = prefijo + ''.join(random.choices(string.digits, k=4))
        if prefijo == 'P':
            if not PrestamoCarro.query.filter_by(codigo=codigo).first():
                return codigo
        else:
            if not PrestamoNetbook.query.filter_by(codigo=codigo).first():
                return codigo


# ─────────────────────────────────────────────────────────────────────────────
#  PRÉSTAMOS DE CARROS
# ─────────────────────────────────────────────────────────────────────────────

@prestamos_bp.route('/carros')
@login_required
def carros():
    prestamos = PrestamoCarro.query.filter_by(estado='activo').all()
    carros    = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    now       = datetime.utcnow()
    return render_template('prestamos/carros.html',
                           prestamos=prestamos, carros=carros, now=now)


@prestamos_bp.route('/carros/retiro', methods=['GET', 'POST'])
@login_required
def retiro_carro():
    if request.method == 'POST':
        carro_id   = request.form.get('carro_id')
        docente_id = request.form.get('docente_id')

        carro   = Carro.query.get_or_404(carro_id)
        docente = Docente.query.get_or_404(docente_id)

        # Verificar turno
        puede, msg = _docente_puede_pedir(docente)
        if not puede:
            flash(msg, 'danger')
            return redirect(url_for('prestamos.retiro_carro'))

        # Verificar que no esté prestado
        activo = PrestamoCarro.query.filter_by(carro_id=carro_id, estado='activo').first()
        if activo:
            flash(f'El carro {carro.display} ya está prestado.', 'danger')
            return redirect(url_for('prestamos.retiro_carro'))

        prestamo = PrestamoCarro(
            codigo           = _gen_codigo('P'),
            docente_id       = docente.id,
            carro_id         = carro.id,
            aula             = carro.aula,
            encargado_retiro = current_user.nombre_completo
        )
        db.session.add(prestamo)
        db.session.commit()

        try:
            from services.mail import enviar_notificacion_retiro_carro
            enviar_notificacion_retiro_carro(prestamo)
        except Exception as e:
            current_app.logger.error(f'Error notificando retiro de carro: {e}')

        flash(f'Retiro registrado: {docente.nombre_completo} — {carro.display}', 'success')
        return redirect(url_for('prestamos.carros'))

    carros    = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    docentes  = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()
    # IDs de carros con préstamo activo
    carros_prestados_ids  = [p.carro_id for p in PrestamoCarro.query.filter_by(estado='activo').all()]
    # IDs de carros en servicio técnico (carro físico roto)
    carros_servicio       = Carro.query.filter_by(estado='en_servicio').all()
    carros_servicio_ids   = [c.id for c in carros_servicio]
    carros_servicio_info  = {c.id: c.motivo_servicio for c in carros_servicio}
    # Unión — estos carros aparecen en rojo y deshabilitados
    prestamos_activos_ids = carros_prestados_ids + carros_servicio_ids
    return render_template('prestamos/retiro_carro.html',
                           carros=carros, docentes=docentes,
                           prestamos_activos_ids=prestamos_activos_ids,
                           carros_servicio_ids=carros_servicio_ids,
                           carros_servicio_info=carros_servicio_info)


@prestamos_bp.route('/carros/<int:id>/devolucion', methods=['POST'])
@login_required
def devolucion_carro(id):
    prestamo = PrestamoCarro.query.get_or_404(id)
    prestamo.hora_devolucion      = datetime.utcnow()
    prestamo.estado               = 'devuelto'
    prestamo.encargado_devolucion = current_user.nombre_completo
    db.session.commit()

    try:
        from services.mail import enviar_notificacion_devolucion_carro
        enviar_notificacion_devolucion_carro(prestamo)
    except Exception as e:
        current_app.logger.error(f'Error notificando devolucion de carro: {e}')

    flash(f'Devolucion registrada: {prestamo.docente.nombre_completo} — {prestamo.carro.display}', 'success')
    return redirect(url_for('prestamos.carros'))


# ─────────────────────────────────────────────────────────────────────────────
#  ESPACIO DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

@prestamos_bp.route('/espacio-digital')
@login_required
def espacio_digital():
    config    = ConfigEspacioDigital.query.first()
    carro     = config.carro if config else None
    prestamos = PrestamoNetbook.query.filter_by(estado='activo').all()
    now       = datetime.utcnow()
    return render_template('prestamos/espacio_digital.html',
                           prestamos=prestamos, carro=carro, config=config, now=now)


@prestamos_bp.route('/espacio-digital/retiro', methods=['GET', 'POST'])
@login_required
def retiro_netbooks():
    config = ConfigEspacioDigital.query.first()
    carro  = config.carro if config else None

    if not carro:
        flash('El carro del Espacio Digital no está configurado.', 'danger')
        return redirect(url_for('prestamos.espacio_digital'))

    if request.method == 'POST':
        docente_id  = request.form.get('docente_id')
        netbook_ids = request.form.getlist('netbook_ids')

        if not docente_id or not netbook_ids:
            flash('Seleccioná un docente y al menos una netbook.', 'danger')
            return redirect(url_for('prestamos.retiro_netbooks'))

        docente = Docente.query.get_or_404(docente_id)

        # Verificar turno
        puede, msg = _docente_puede_pedir(docente)
        if not puede:
            flash(msg, 'danger')
            return redirect(url_for('prestamos.retiro_netbooks'))

        prestamo = PrestamoNetbook(
            codigo           = _gen_codigo('NB'),
            docente_id       = docente.id,
            encargado_retiro = current_user.nombre_completo
        )
        db.session.add(prestamo)
        db.session.flush()

        for nb_id in netbook_ids:
            nb   = Netbook.query.get(nb_id)
            item = PrestamoNetbookItem(
                prestamo_id    = prestamo.id,
                netbook_id     = nb.id,
                numero_interno = nb.numero_interno,
                numero_serie   = nb.numero_serie,
                alumno         = nb.alumno
            )
            db.session.add(item)

        db.session.commit()

        try:
            from services.mail import enviar_notificacion_retiro_netbook
            enviar_notificacion_retiro_netbook(prestamo)
        except Exception as e:
            current_app.logger.error(f'Error notificando retiro de netbooks: {e}')

        flash(f'Prestamo registrado: {docente.nombre_completo} — {len(netbook_ids)} netbook(s)', 'success')
        return redirect(url_for('prestamos.espacio_digital'))

    prestadas_ids = {item.netbook_id for p in PrestamoNetbook.query.filter_by(estado='activo').all()
                     for item in p.items}
    disponibles   = [nb for nb in carro.netbooks
                     if nb.estado == 'operativa' and nb.id not in prestadas_ids]
    docentes      = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()

    return render_template('prestamos/retiro_netbooks.html',
                           docentes=docentes, disponibles=disponibles, carro=carro)


@prestamos_bp.route('/espacio-digital/<int:prestamo_id>/devolucion-item/<int:item_id>', methods=['POST'])
@login_required
def devolucion_netbook_individual(prestamo_id, item_id):
    from models import PrestamoNetbookItem
    prestamo = PrestamoNetbook.query.get_or_404(prestamo_id)
    item     = PrestamoNetbookItem.query.get_or_404(item_id)
    numero   = item.numero_interno

    # Eliminar el ítem del préstamo
    db.session.delete(item)
    db.session.flush()

    # Recargar ítems restantes
    items_restantes = PrestamoNetbookItem.query.filter_by(prestamo_id=prestamo.id).count()

    if items_restantes == 0:
        # Último ítem — cerrar el préstamo
        prestamo.hora_devolucion      = datetime.utcnow()
        prestamo.estado               = 'devuelto'
        prestamo.encargado_devolucion = current_user.nombre_completo
        db.session.commit()
        try:
            from services.mail import enviar_notificacion_devolucion_netbook
            enviar_notificacion_devolucion_netbook(prestamo)
        except Exception as e:
            current_app.logger.error(f'Error notificando devolucion netbook: {e}')
        flash(f'Todas las netbooks devueltas — {prestamo.docente.nombre_completo}', 'success')
    else:
        db.session.commit()
        flash(f'Netbook N°{numero} devuelta. Quedan {items_restantes} pendiente(s).', 'success')

    return redirect(url_for('prestamos.espacio_digital'))


@prestamos_bp.route('/espacio-digital/<int:id>/devolucion', methods=['POST'])
@login_required
def devolucion_netbooks(id):
    prestamo = PrestamoNetbook.query.get_or_404(id)
    prestamo.hora_devolucion      = datetime.utcnow()
    prestamo.estado               = 'devuelto'
    prestamo.encargado_devolucion = current_user.nombre_completo
    db.session.commit()

    try:
        from services.mail import enviar_notificacion_devolucion_netbook
        enviar_notificacion_devolucion_netbook(prestamo)
    except Exception as e:
        current_app.logger.error(f'Error notificando devolucion de netbooks: {e}')

    flash(f'Devolucion registrada: {prestamo.docente.nombre_completo} — {len(prestamo.items)} netbook(s)', 'success')
    return redirect(url_for('prestamos.espacio_digital'))


# ─────────────────────────────────────────────────────────────────────────────
#  HISTORIAL CON FECHAS PERSONALIZADAS
# ─────────────────────────────────────────────────────────────────────────────

@prestamos_bp.route('/historial')
@login_required
def historial():
    periodo     = request.args.get('periodo', 'hoy')
    busqueda    = request.args.get('q', '').strip()
    tipo        = request.args.get('tipo', 'carros')
    fecha_desde = request.args.get('fecha_desde', '').strip()
    fecha_hasta = request.args.get('fecha_hasta', '').strip()

    ahora = datetime.utcnow()

    def _aplicar_filtro_fecha(query, campo_fecha):
        if fecha_desde and fecha_hasta:
            try:
                d_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
                d_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                return query.filter(campo_fecha >= d_desde, campo_fecha <= d_hasta)
            except ValueError:
                pass
        elif fecha_desde:
            try:
                d_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
                return query.filter(campo_fecha >= d_desde)
            except ValueError:
                pass
        else:
            if periodo == 'hoy':
                return query.filter(campo_fecha >= ahora.replace(hour=0, minute=0, second=0))
            elif periodo == 'semana':
                return query.filter(campo_fecha >= ahora - timedelta(days=7))
            elif periodo == 'mes':
                return query.filter(campo_fecha >= ahora - timedelta(days=30))
        return query

    if tipo == 'carros':
        query = PrestamoCarro.query
        query = _aplicar_filtro_fecha(query, PrestamoCarro.hora_retiro)
        if busqueda:
            query = query.join(Docente).filter(
                db.or_(Docente.apellido.ilike(f'%{busqueda}%'),
                       Docente.nombre.ilike(f'%{busqueda}%'),
                       Docente.dni.ilike(f'%{busqueda}%')))
        prestamos = query.order_by(PrestamoCarro.hora_retiro.desc()).all()
    else:
        query = PrestamoNetbook.query
        query = _aplicar_filtro_fecha(query, PrestamoNetbook.hora_retiro)
        if busqueda:
            query = query.join(Docente).filter(
                db.or_(Docente.apellido.ilike(f'%{busqueda}%'),
                       Docente.nombre.ilike(f'%{busqueda}%')))
        prestamos = query.order_by(PrestamoNetbook.hora_retiro.desc()).all()

    return render_template('prestamos/historial.html',
                           prestamos=prestamos, periodo=periodo,
                           busqueda=busqueda, tipo=tipo,
                           fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)


# ─────────────────────────────────────────────────────────────────────────────
#  PDF PARTE DE ALERTA — PRÉSTAMO EN DEMORA
# ─────────────────────────────────────────────────────────────────────────────

@prestamos_bp.route('/carros/<int:id>/alerta-pdf')
@login_required
def alerta_pdf_carro(id):
    """Genera el Parte de Alerta en PDF para un préstamo de carro en demora."""
    from services.pdf_reportes import pdf_alerta_demora_carro
    return pdf_alerta_demora_carro(id)


@prestamos_bp.route('/espacio-digital/<int:id>/alerta-pdf')
@login_required
def alerta_pdf_netbooks(id):
    """Genera el Parte de Alerta en PDF para un préstamo de netbooks en demora."""
    from services.pdf_reportes import pdf_alerta_demora_netbooks
    return pdf_alerta_demora_netbooks(id)
