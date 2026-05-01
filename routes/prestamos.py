from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Carro, Docente, PrestamoCarro, PrestamoNetbook, PrestamoNetbookItem, Netbook, ConfigEspacioDigital, PrestamoTV
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


def _umbral_alerta_netbooks(prestamo):
    """
    Determina si un préstamo de netbooks del Espacio Digital está en demora,
    según el turno del docente y los horarios reales de la escuela.

    Reglas:
      - Turno Mañana     → alerta si ya pasaron las 12:40 (fin de M7)
      - Turno Tarde      → alerta si ya pasaron las 18:20 (fin de T8)
      - Turno Mañana y Tarde / doble turno → usar umbral Tarde (18:20)
      - Sin turno / indeterminado          → fallback: MINUTOS_ALERTA_PRESTAMO (260 min)

    Devuelve True si el préstamo está en demora.
    """
    from flask import current_app
    ARG_OFFSET = timedelta(hours=-3)
    ahora_arg  = datetime.utcnow() + ARG_OFFSET
    retiro_arg = prestamo.hora_retiro + ARG_OFFSET

    docente = prestamo.docente
    turno   = (docente.turno or '').strip().lower() if docente else ''

    # Detectar turno
    es_manana = any(p in turno for p in ['mañana', 'manana', 'morning'])
    es_tarde  = any(p in turno for p in ['tarde', 'afternoon'])
    es_ambos  = ('y' in turno) or ('ambos' in turno) or ('varios' in turno) \
                or (es_manana and es_tarde)

    # Hora de corte según turno — en hora Argentina del día del retiro
    if es_ambos or (es_manana and es_tarde):
        # Turno doble → usar corte de tarde
        corte = retiro_arg.replace(hour=18, minute=20, second=0, microsecond=0)
        return ahora_arg >= corte
    elif es_tarde:
        corte = retiro_arg.replace(hour=18, minute=20, second=0, microsecond=0)
        return ahora_arg >= corte
    elif es_manana:
        corte = retiro_arg.replace(hour=12, minute=40, second=0, microsecond=0)
        return ahora_arg >= corte
    else:
        # Sin turno definido → fallback por minutos
        mins_alerta = current_app.config.get('MINUTOS_ALERTA_PRESTAMO', 260)
        delta_mins  = int((datetime.utcnow() - prestamo.hora_retiro).total_seconds() / 60)
        return delta_mins >= mins_alerta


def _materia_modulo_actual(docente_id):
    """
    Detecta qué materia está dando el docente en el módulo actual.
    Cruza la hora y día actuales (Argentina) con HorarioDocente.
    Devuelve el nombre de la materia o None si no se puede determinar.
    """
    from models_extra.horarios_notificaciones import HorarioDocente, MODULOS

    ARG_OFFSET = timedelta(hours=-3)
    ahora_arg  = datetime.utcnow() + ARG_OFFSET

    # Día de la semana en español
    dias = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    dia_actual = dias[ahora_arg.weekday()]

    # Hora actual como minutos desde medianoche
    minutos_ahora = ahora_arg.hour * 60 + ahora_arg.minute

    # Buscar qué módulo corresponde a la hora actual
    # MODULOS es un dict {numero: {'inicio': 'HH:MM', 'fin': 'HH:MM', 'codigo': 'M1', ...}}
    modulo_actual = None
    for num, datos in MODULOS.items():
        try:
            h_ini, m_ini = map(int, datos['inicio'].split(':'))
            h_fin, m_fin = map(int, datos['fin'].split(':'))
            min_ini = h_ini * 60 + m_ini
            min_fin = h_fin * 60 + m_fin
            if min_ini <= minutos_ahora <= min_fin:
                modulo_actual = num
                break
        except Exception:
            continue

    if modulo_actual is None:
        return None

    # Buscar en HorarioDocente
    horario = HorarioDocente.query.filter_by(
        docente_id=docente_id,
        dia=dia_actual,
        modulo=modulo_actual,
    ).first()

    if horario and horario.materia:
        return horario.materia.strip()

    return None


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
    prestamos     = PrestamoCarro.query.filter_by(estado='activo').all()
    carros        = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    tvs_prestadas = PrestamoTV.query.filter_by(estado='activo').order_by(PrestamoTV.fecha_retiro).all()
    now           = datetime.utcnow()
    return render_template('prestamos/carros.html',
                           prestamos=prestamos, carros=carros,
                           tvs_prestadas=tvs_prestadas, now=now)


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
            encargado_retiro = current_user.nombre_completo,
            materia_prestamo = _materia_modulo_actual(docente.id),
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
    carro_2   = config.carro_2 if config else None
    prestamos = PrestamoNetbook.query.filter_by(estado='activo').all()
    now       = datetime.utcnow()
    # IDs de prestamos que superaron el umbral de alerta segun el turno del docente
    alerta_ids = {p.id for p in prestamos if _umbral_alerta_netbooks(p)}
    return render_template('prestamos/espacio_digital.html',
                           prestamos=prestamos, carro=carro, carro_2=carro_2,
                           config=config, now=now, alerta_ids=alerta_ids)


@prestamos_bp.route('/espacio-digital/retiro', methods=['GET', 'POST'])
@login_required
def retiro_netbooks():
    config = ConfigEspacioDigital.query.first()
    carro  = config.carro if config else None
    carro_2 = config.carro_2 if config else None

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

    def _sort_num(nb_list):
        """Ordena netbooks por numero_interno numérico."""
        return sorted(nb_list,
                      key=lambda nb: int(nb.numero_interno) if nb.numero_interno and nb.numero_interno.isdigit() else 9999)

    # Carro 1 — disponibles y prestadas (solo operativas)
    nb_carro1_disponibles = _sort_num([nb for nb in carro.netbooks
                                       if nb.estado == 'operativa' and nb.id not in prestadas_ids])
    nb_carro1_prestadas   = _sort_num([nb for nb in carro.netbooks
                                       if nb.estado == 'operativa' and nb.id in prestadas_ids])

    # Carro 2 — disponibles y prestadas (solo operativas)
    nb_carro2_disponibles = _sort_num([nb for nb in carro_2.netbooks
                                       if nb.estado == 'operativa' and nb.id not in prestadas_ids]) if carro_2 else []
    nb_carro2_prestadas   = _sort_num([nb for nb in carro_2.netbooks
                                       if nb.estado == 'operativa' and nb.id in prestadas_ids]) if carro_2 else []

    # disponibles combinadas (para compatibilidad con cualquier referencia anterior)
    disponibles = nb_carro1_disponibles + nb_carro2_disponibles

    docentes = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()

    return render_template('prestamos/retiro_netbooks.html',
                           docentes=docentes, disponibles=disponibles,
                           carro=carro, carro_2=carro_2,
                           nb_carro1_disponibles=nb_carro1_disponibles,
                           nb_carro1_prestadas=nb_carro1_prestadas,
                           nb_carro2_disponibles=nb_carro2_disponibles,
                           nb_carro2_prestadas=nb_carro2_prestadas)


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
    ARG_OFFSET  = timedelta(hours=-3)
    periodo     = request.args.get('periodo', 'hoy')
    busqueda    = request.args.get('q', '').strip()
    tipo        = request.args.get('tipo', 'carros')
    fecha_desde = request.args.get('fecha_desde', '').strip()
    fecha_hasta = request.args.get('fecha_hasta', '').strip()
    hora_desde  = request.args.get('hora_desde', '').strip()
    hora_hasta  = request.args.get('hora_hasta', '').strip()

    ahora = datetime.utcnow()

    def _aplicar_filtro_fecha(query, campo_fecha):
        """Aplica filtros de fecha y, opcionalmente, de hora (rango horario en UTC)."""
        if fecha_desde or fecha_hasta:
            try:
                # Fecha base desde/hasta (hora Argentina → UTC para comparar con la BD)
                if fecha_desde:
                    d_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
                    if hora_desde:
                        h, m = map(int, hora_desde.split(':'))
                        d_desde = d_desde.replace(hour=h, minute=m, second=0)
                    else:
                        d_desde = d_desde.replace(hour=0, minute=0, second=0)
                    d_desde = d_desde - ARG_OFFSET   # Argentina → UTC
                else:
                    d_desde = None

                if fecha_hasta:
                    d_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                    if hora_hasta:
                        h, m = map(int, hora_hasta.split(':'))
                        d_hasta = d_hasta.replace(hour=h, minute=m, second=59)
                    else:
                        d_hasta = d_hasta.replace(hour=23, minute=59, second=59)
                    d_hasta = d_hasta - ARG_OFFSET   # Argentina → UTC
                else:
                    d_hasta = None

                if d_desde:
                    query = query.filter(campo_fecha >= d_desde)
                if d_hasta:
                    query = query.filter(campo_fecha <= d_hasta)
                return query
            except ValueError:
                pass
        else:
            # Filtros rápidos (Hoy / Semana / Mes) — también aplica filtro de hora si está presente
            if periodo == 'hoy':
                base = ahora.replace(hour=0, minute=0, second=0)
                query = query.filter(campo_fecha >= base)
            elif periodo == 'semana':
                query = query.filter(campo_fecha >= ahora - timedelta(days=7))
            elif periodo == 'mes':
                query = query.filter(campo_fecha >= ahora - timedelta(days=30))

            # Filtro de hora sobre el resultado del período (como franja horaria diaria en UTC)
            if hora_desde:
                try:
                    h, m = map(int, hora_desde.split(':'))
                    minutos_desde = (h * 60 + m) - (-3 * 60)   # Argentina → UTC minutos
                    # Extraer la hora UTC equivalente para el filtro
                    hora_utc_desde = timedelta(minutes=minutos_desde)
                    from sqlalchemy import func, extract
                    h_utc_d = (h * 60 + m + 180) // 60 % 24
                    m_utc_d = (h * 60 + m + 180) % 60
                    query = query.filter(
                        extract('hour', campo_fecha) * 60 + extract('minute', campo_fecha)
                        >= h_utc_d * 60 + m_utc_d
                    )
                except (ValueError, TypeError):
                    pass
            if hora_hasta:
                try:
                    h, m = map(int, hora_hasta.split(':'))
                    h_utc_h = (h * 60 + m + 180) // 60 % 24
                    m_utc_h = (h * 60 + m + 180) % 60
                    from sqlalchemy import extract
                    query = query.filter(
                        extract('hour', campo_fecha) * 60 + extract('minute', campo_fecha)
                        <= h_utc_h * 60 + m_utc_h
                    )
                except (ValueError, TypeError):
                    pass

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
                           fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
                           hora_desde=hora_desde, hora_hasta=hora_hasta)


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


# ─────────────────────────────────────────────────────────────────────────────
#  PLANILLA DE MOVIMIENTOS ACTIVOS
# ─────────────────────────────────────────────────────────────────────────────

@prestamos_bp.route('/movimientos-activos/pdf')
@login_required
def movimientos_activos_pdf():
    """Descarga la Planilla de Movimientos Activos en PDF. Accesible para todos los roles."""
    from services.pdf_reportes import pdf_movimientos_activos
    return pdf_movimientos_activos()


@prestamos_bp.route('/movimientos-activos/destinatarios')
@login_required
def movimientos_activos_destinatarios():
    """Devuelve JSON con la lista de posibles destinatarios (Directivos + Admins + et7de5)."""
    from models import Usuario
    MAIL_DET = 'et7de5@bue.edu.ar'
    usuarios = Usuario.query.filter(
        Usuario.rol.in_(['Directivo', 'Administrador']),
        Usuario.activo == True,
        Usuario.correo != None,
        Usuario.correo != ''
    ).order_by(Usuario.apellido).all()
    lista = [{'nombre': u.nombre_completo, 'correo': u.correo} for u in usuarios]
    # Agregar mail DET si no está ya en la lista
    correos_existentes = {u['correo'] for u in lista}
    if MAIL_DET not in correos_existentes:
        lista.append({'nombre': 'DET 5 (institucional)', 'correo': MAIL_DET})
    return jsonify(lista)


@prestamos_bp.route('/movimientos-activos/mail', methods=['POST'])
@login_required
def movimientos_activos_mail():
    """
    Envía la Planilla de Movimientos Activos a los destinatarios seleccionados en el modal.
    Recibe lista 'destinatarios[]' via POST form.
    """
    destinatarios = request.form.getlist('destinatarios[]')
    destinatarios = [d.strip() for d in destinatarios if d.strip()]

    if not destinatarios:
        flash('Seleccioná al menos un destinatario.', 'danger')
        return redirect(url_for('prestamos.carros'))

    try:
        from services.pdf_reportes import pdf_movimientos_activos
        from services.mail import enviar_planilla_movimientos
        buffer = pdf_movimientos_activos(como_buffer=True)
        errores = []
        for correo in destinatarios:
            try:
                buffer.seek(0)
                enviar_planilla_movimientos(correo, buffer, current_user.nombre_completo)
            except Exception as e:
                current_app.logger.error(f'Error enviando planilla a {correo}: {e}')
                errores.append(correo)

        if errores:
            flash(
                f'Planilla enviada con errores. No se pudo enviar a: {", ".join(errores)}.',
                'warning'
            )
        else:
            flash(
                f'Planilla enviada correctamente a {len(destinatarios)} destinatario(s).',
                'success'
            )
    except Exception as e:
        current_app.logger.error(f'Error generando planilla movimientos: {e}')
        flash('Error al generar el PDF. Revisá los logs.', 'danger')

    return redirect(url_for('prestamos.carros'))
