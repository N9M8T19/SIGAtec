"""
services/mail.py
Envío de mails usando SMTP con Gmail App Password.
No requiere token.json ni credenciales OAuth de escritorio.
Funciona en Render con variables de entorno GMAIL_USER y GMAIL_APP_PASSWORD.
"""

import os
import smtplib
import traceback
from datetime import timezone, timedelta
from email.mime.text import MIMEText
from flask import current_app
from models import db

# ── Configuración ──────────────────────────────────────────────────────────────
GMAIL_USER     = os.environ.get('GMAIL_USER', 'aulamagnaespaciodigital@gmail.com')
GMAIL_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GMAIL_FROM     = GMAIL_USER

AR = timezone(timedelta(hours=-3))

def _hora_ar(dt):
    """Convierte datetime UTC a hora Argentina formateada."""
    return dt.replace(tzinfo=timezone.utc).astimezone(AR).strftime('%d/%m/%Y %H:%M')


def _get_template_mail(campo):
    """Devuelve el template de mail desde ConfigSistema o None si no está configurado."""
    try:
        from models.config_sistema import ConfigSistema
        cfg = ConfigSistema.query.first()
        if cfg:
            return getattr(cfg, campo, None) or None
    except Exception:
        pass
    return None


def _enviar_mail(destinatario, asunto, cuerpo):
    if not GMAIL_PASSWORD:
        raise RuntimeError(
            'GMAIL_APP_PASSWORD no está configurada. '
            'Agregala como variable de entorno en Render.'
        )
    mensaje = MIMEText(cuerpo, 'plain', 'utf-8')
    mensaje['To']      = destinatario
    mensaje['From']    = GMAIL_FROM
    mensaje['Subject'] = asunto
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        smtp.sendmail(GMAIL_FROM, destinatario, mensaje.as_bytes())


def _destinatarios_por_evento(evento):
    from models_extra.horarios_notificaciones import ConfigNotificacion
    configs = ConfigNotificacion.query.filter_by(activo=True).all()
    return [c.correo for c in configs if c.recibe(evento)]


def _log(evento, destinatario, asunto, enviado, error=None):
    from models_extra.horarios_notificaciones import LogNotificacion
    log = LogNotificacion(
        evento=evento,
        destinatario=destinatario,
        asunto=asunto,
        enviado=enviado,
        error=str(error) if error else None
    )
    db.session.add(log)
    db.session.commit()


def _enviar_a_todos(evento, asunto, cuerpo, correo_docente=None):
    destinatarios = _destinatarios_por_evento(evento)
    if correo_docente and correo_docente not in destinatarios:
        destinatarios.append(correo_docente)
    if not destinatarios:
        current_app.logger.warning(
            f'[mail] No hay destinatarios para el evento "{evento}".'
        )
        return
    for correo in destinatarios:
        try:
            _enviar_mail(correo, asunto, cuerpo)
            _log(evento, correo, asunto, enviado=True)
            current_app.logger.info(f'[mail] Enviado a {correo} — {asunto}')
        except Exception as e:
            _log(evento, correo, asunto, enviado=False, error=traceback.format_exc())
            current_app.logger.error(f'[mail] Error enviando a {correo}: {e}')


def _cantidad_netbooks_carro(carro):
    """Cuenta las netbooks operativas del carro (excluye en_servicio y de_baja)."""
    return sum(
        1 for nb in carro.netbooks
        if getattr(nb, 'estado', 'operativa') not in ('en_servicio', 'de_baja', 'baja')
    )


# ── Notificaciones de carros ───────────────────────────────────────────────────

def enviar_notificacion_retiro_carro(prestamo):
    correo = prestamo.docente.correo
    if not correo:
        current_app.logger.warning(
            f'[mail] Docente {prestamo.docente.nombre_completo} sin correo — retiro carro omitido.'
        )
        return
    cantidad_nb = _cantidad_netbooks_carro(prestamo.carro)
    asunto = f'Retiro de carro {prestamo.carro.display}'
    _tpl = _get_template_mail('mail_retiro_carro')
    if _tpl:
        cuerpo = _tpl.format(
            docente=prestamo.docente.nombre_completo,
            carro=prestamo.carro.display,
            aula=prestamo.aula or '—',
            hora=_hora_ar(prestamo.hora_retiro),
            encargado=prestamo.encargado_retiro or '—',
            cantidad_netbooks=cantidad_nb,
        )
    else:
        cuerpo = (
            f"Retiro de carro\n\n"
            f"Docente:    {prestamo.docente.nombre_completo}\n"
            f"Carro:      {prestamo.carro.display}\n"
            f"Netbooks:   {cantidad_nb} equipos operativos\n"
            f"Aula:       {prestamo.aula or '—'}\n"
            f"Hora:       {_hora_ar(prestamo.hora_retiro)}\n"
            f"Registró:   {prestamo.encargado_retiro}\n"
        )
    try:
        _enviar_mail(correo, asunto, cuerpo)
        _log('retiro_carro', correo, asunto, enviado=True)
        current_app.logger.info(f'[mail] Enviado a {correo} — {asunto}')
    except Exception as e:
        _log('retiro_carro', correo, asunto, enviado=False, error=traceback.format_exc())
        current_app.logger.error(f'[mail] Error enviando a {correo}: {e}')


def enviar_notificacion_devolucion_carro(prestamo):
    correo = prestamo.docente.correo
    if not correo:
        current_app.logger.warning(
            f'[mail] Docente {prestamo.docente.nombre_completo} sin correo — devolución carro omitida.'
        )
        return
    cantidad_nb = _cantidad_netbooks_carro(prestamo.carro)
    mins = prestamo.duracion_minutos or 0
    asunto = f'Devolución de carro {prestamo.carro.display}'
    _tpl = _get_template_mail('mail_devolucion_carro')
    if _tpl:
        cuerpo = _tpl.format(
            docente=prestamo.docente.nombre_completo,
            carro=prestamo.carro.display,
            hora_retiro=_hora_ar(prestamo.hora_retiro),
            hora_devolucion=_hora_ar(prestamo.hora_devolucion),
            duracion=f"{mins // 60}h {mins % 60}m",
            encargado=prestamo.encargado_devolucion or '—',
            cantidad_netbooks=cantidad_nb,
        )
    else:
        cuerpo = (
            f"Devolución de carro\n\n"
            f"Docente:    {prestamo.docente.nombre_completo}\n"
            f"Carro:      {prestamo.carro.display}\n"
            f"Netbooks:   {cantidad_nb} equipos operativos\n"
            f"Retiro:     {_hora_ar(prestamo.hora_retiro)}\n"
            f"Devolución: {_hora_ar(prestamo.hora_devolucion)}\n"
            f"Duración:   {mins // 60}h {mins % 60}m\n"
            f"Registró:   {prestamo.encargado_devolucion}\n"
        )
    try:
        _enviar_mail(correo, asunto, cuerpo)
        _log('devolucion_carro', correo, asunto, enviado=True)
        current_app.logger.info(f'[mail] Enviado a {correo} — {asunto}')
    except Exception as e:
        _log('devolucion_carro', correo, asunto, enviado=False, error=traceback.format_exc())
        current_app.logger.error(f'[mail] Error enviando a {correo}: {e}')


# ── Notificaciones de netbooks (Espacio Digital) ───────────────────────────────
#
#  {items} muestra cada netbook con su número interno y el alumno asignado:
#    • N°5 — García, Lucía
#    • N°12 — Sin asignar
#
#  {cantidad} muestra el total de netbooks del préstamo.

def enviar_notificacion_retiro_netbook(prestamo):
    correo = prestamo.docente.correo
    if not correo:
        current_app.logger.warning(
            f'[mail] Docente {prestamo.docente.nombre_completo} sin correo — retiro netbooks omitido.'
        )
        return
    asunto = f'Retiro de netbooks — {prestamo.docente.nombre_completo}'
    items = '\n'.join(
        f'  • N°{i.numero_interno} — {i.alumno or "Sin asignar"}'
        for i in prestamo.items
    )
    _tpl = _get_template_mail('mail_retiro_nb')
    if _tpl:
        cuerpo = _tpl.format(
            docente=prestamo.docente.nombre_completo,
            hora=_hora_ar(prestamo.hora_retiro),
            encargado=prestamo.encargado_retiro or '—',
            items=items,
            cantidad=len(prestamo.items),
        )
    else:
        cuerpo = (
            f"Retiro de netbooks — Espacio Digital\n\n"
            f"Docente:   {prestamo.docente.nombre_completo}\n"
            f"Hora:      {_hora_ar(prestamo.hora_retiro)}\n"
            f"Registró:  {prestamo.encargado_retiro}\n\n"
            f"Netbooks retiradas ({len(prestamo.items)}):\n"
            f"{items}\n"
        )
    try:
        _enviar_mail(correo, asunto, cuerpo)
        _log('retiro_netbook', correo, asunto, enviado=True)
        current_app.logger.info(f'[mail] Enviado a {correo} — {asunto}')
    except Exception as e:
        _log('retiro_netbook', correo, asunto, enviado=False, error=traceback.format_exc())
        current_app.logger.error(f'[mail] Error enviando a {correo}: {e}')


def enviar_notificacion_devolucion_netbook(prestamo):
    correo = prestamo.docente.correo
    if not correo:
        current_app.logger.warning(
            f'[mail] Docente {prestamo.docente.nombre_completo} sin correo — devolución netbooks omitida.'
        )
        return
    asunto = f'Devolución de netbooks — {prestamo.docente.nombre_completo}'
    mins = int((prestamo.hora_devolucion - prestamo.hora_retiro).total_seconds() / 60)
    items = '\n'.join(
        f'  • N°{i.numero_interno} — {i.alumno or "Sin asignar"}'
        for i in prestamo.items
    )
    _tpl = _get_template_mail('mail_devolucion_nb')
    if _tpl:
        cuerpo = _tpl.format(
            docente=prestamo.docente.nombre_completo,
            hora_retiro=_hora_ar(prestamo.hora_retiro),
            hora_devolucion=_hora_ar(prestamo.hora_devolucion),
            duracion=f"{mins // 60}h {mins % 60}m",
            encargado=prestamo.encargado_devolucion or '—',
            cantidad=len(prestamo.items),
            items=items,
        )
    else:
        cuerpo = (
            f"Devolución de netbooks — Espacio Digital\n\n"
            f"Docente:    {prestamo.docente.nombre_completo}\n"
            f"Retiro:     {_hora_ar(prestamo.hora_retiro)}\n"
            f"Devolución: {_hora_ar(prestamo.hora_devolucion)}\n"
            f"Duración:   {mins // 60}h {mins % 60}m\n"
            f"Registró:   {prestamo.encargado_devolucion}\n\n"
            f"Netbooks devueltas ({len(prestamo.items)}):\n"
            f"{items}\n"
        )
    try:
        _enviar_mail(correo, asunto, cuerpo)
        _log('devolucion_netbook', correo, asunto, enviado=True)
        current_app.logger.info(f'[mail] Enviado a {correo} — {asunto}')
    except Exception as e:
        _log('devolucion_netbook', correo, asunto, enviado=False, error=traceback.format_exc())
        current_app.logger.error(f'[mail] Error enviando a {correo}: {e}')


# ── Alertas ────────────────────────────────────────────────────────────────────

def enviar_alerta_demora(prestamo, tipo='carro'):
    evento = 'alerta_demora'
    if tipo == 'carro':
        item   = prestamo.carro.display
        asunto = f'⚠️ DEMORA — carro {item} no devuelto'
    else:
        item   = f'{len(prestamo.items)} netbook(s)'
        asunto = '⚠️ DEMORA — netbooks no devueltas'
    cuerpo = (
        f"⚠️ Alerta de demora\n\n"
        f"Docente:      {prestamo.docente.nombre_completo}\n"
        f"Ítem:         {item}\n"
        f"Retirado:     {_hora_ar(prestamo.hora_retiro)}\n"
        f"Transcurrido: {prestamo.tiempo_transcurrido}\n\n"
        f"Por favor verificar el estado del préstamo.\n"
    )
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_alerta_horario(prestamo, horario, tipo='carro'):
    evento = 'alerta_horario'
    if tipo == 'carro':
        item   = prestamo.carro.display
        asunto = f'⚠️ Clase terminada — carro {item} no devuelto'
    else:
        item   = f'{len(prestamo.items)} netbook(s)'
        asunto = '⚠️ Clase terminada — netbooks no devueltas'
    cuerpo = (
        f"⚠️ El docente terminó su módulo y no devolvió el material.\n\n"
        f"Docente:  {prestamo.docente.nombre_completo}\n"
        f"Materia:  {horario.materia or prestamo.docente.materia or '—'}\n"
        f"Módulo:   {horario.modulo} ({horario.hora_inicio} - {horario.hora_fin})\n"
        f"Ítem:     {item}\n"
        f"Retirado: {_hora_ar(prestamo.hora_retiro)}\n"
    )
    _enviar_a_todos(evento, asunto, cuerpo)


def init_mail(app):
    """Compatibilidad con app.py."""
    usuario = os.environ.get('GMAIL_USER', 'aulamagnaespaciodigital@gmail.com')
    tiene   = bool(os.environ.get('GMAIL_APP_PASSWORD'))
    app.logger.info(
        f'Servicio de mail: SMTP Gmail. '
        f'Usuario: {usuario} | App Password configurada: {tiene}'
    )


# ── Planilla de Movimientos Activos ───────────────────────────────────────────

def enviar_planilla_movimientos(destinatario, pdf_buffer, remitente_nombre=''):
    """
    Envía la Planilla de Movimientos Activos como adjunto PDF al destinatario indicado.
    pdf_buffer: BytesIO con el PDF ya generado.
    """
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    from datetime import datetime

    if not GMAIL_PASSWORD:
        raise RuntimeError(
            'GMAIL_APP_PASSWORD no está configurada. '
            'Agregala como variable de entorno en Render.'
        )

    ahora_ar = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(AR)
    fecha_str = ahora_ar.strftime('%d/%m/%Y %H:%M')
    nombre_archivo = f'movimientos_activos_{ahora_ar.strftime("%Y%m%d_%H%M")}.pdf'

    asunto = f'Planilla de Movimientos Activos — {fecha_str}'
    cuerpo = (
        f'Se adjunta la Planilla de Movimientos Activos generada el {fecha_str} hs.\n\n'
        f'Contiene todos los préstamos activos (carros y Espacio Digital) '
        f'al momento de su generación.\n\n'
        f'Generada por: {remitente_nombre or "SIGA-Tec"}\n'
        f'Sistema: SIGA-Tec — E.T. N°7 D.E. 5\n'
    )

    mensaje = MIMEMultipart()
    mensaje['To']      = destinatario
    mensaje['From']    = GMAIL_FROM
    mensaje['Subject'] = asunto
    mensaje.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    adjunto = MIMEBase('application', 'pdf')
    adjunto.set_payload(pdf_buffer.read())
    encoders.encode_base64(adjunto)
    adjunto.add_header('Content-Disposition', 'attachment', filename=nombre_archivo)
    mensaje.attach(adjunto)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        smtp.sendmail(GMAIL_FROM, destinatario, mensaje.as_bytes())


# ── Notificaciones de TVs ──────────────────────────────────────────────────────
#
#  Se envían al docente (si tiene correo).
#  PrestamoTV usa encargado_retiro_id / encargado_devolucion_id como FK a usuarios,
#  no como string — se accede via .encargado_retiro.nombre_completo.

def enviar_notificacion_retiro_tv(prestamo):
    """Notifica al docente cuando retira una TV."""
    if not prestamo.docente:
        current_app.logger.warning(
            f'[mail] Préstamo TV #{prestamo.id} sin docente — retiro omitido.'
        )
        return
    correo = prestamo.docente.correo
    if not correo:
        current_app.logger.warning(
            f'[mail] Docente {prestamo.docente.nombre_completo} sin correo — retiro TV omitido.'
        )
        return

    tv = prestamo.tv
    encargado_nombre = (
        prestamo.encargado_retiro.nombre_completo
        if prestamo.encargado_retiro else '—'
    )
    componentes = ', '.join(tv.componentes_lista) or 'Sin accesorios'
    pulgadas_str = f' ({tv.pulgadas}")' if tv.pulgadas else ''

    asunto = f'Retiro de televisor {tv.codigo}'
    _tpl = _get_template_mail('mail_retiro_tv')
    if _tpl:
        cuerpo = _tpl.format(
            docente=prestamo.docente.nombre_completo,
            tv=f'{tv.codigo} — {tv.marca} {tv.modelo}{pulgadas_str}',
            aula_destino=prestamo.aula_destino or '—',
            motivo=prestamo.motivo or '—',
            componentes=componentes,
            hora=_hora_ar(prestamo.fecha_retiro),
            encargado=encargado_nombre,
        )
    else:
        cuerpo = (
            f"Retiro de televisor\n\n"
            f"Docente:      {prestamo.docente.nombre_completo}\n"
            f"TV:           {tv.codigo} — {tv.marca} {tv.modelo}{pulgadas_str}\n"
            f"Aula destino: {prestamo.aula_destino or '—'}\n"
            f"Motivo:       {prestamo.motivo or '—'}\n"
            f"Componentes:  {componentes}\n"
            f"Hora:         {_hora_ar(prestamo.fecha_retiro)}\n"
            f"Registró:     {encargado_nombre}\n"
        )
    try:
        _enviar_mail(correo, asunto, cuerpo)
        _log('retiro_tv', correo, asunto, enviado=True)
        current_app.logger.info(f'[mail] Enviado a {correo} — {asunto}')
    except Exception as e:
        _log('retiro_tv', correo, asunto, enviado=False, error=traceback.format_exc())
        current_app.logger.error(f'[mail] Error enviando a {correo}: {e}')


def enviar_notificacion_devolucion_tv(prestamo):
    """Notifica al docente cuando devuelve una TV."""
    if not prestamo.docente:
        current_app.logger.warning(
            f'[mail] Préstamo TV #{prestamo.id} sin docente — devolución omitida.'
        )
        return
    correo = prestamo.docente.correo
    if not correo:
        current_app.logger.warning(
            f'[mail] Docente {prestamo.docente.nombre_completo} sin correo — devolución TV omitida.'
        )
        return

    tv = prestamo.tv
    encargado_nombre = (
        prestamo.encargado_devolucion.nombre_completo
        if prestamo.encargado_devolucion else '—'
    )

    # Duración
    if prestamo.fecha_devolucion_real and prestamo.fecha_retiro:
        mins = int(
            (prestamo.fecha_devolucion_real - prestamo.fecha_retiro).total_seconds() / 60
        )
        duracion = f"{mins // 60}h {mins % 60}m"
    else:
        duracion = '—'

    # Componentes devueltos vs. prestados
    devueltos = []
    faltantes  = []
    pares = [
        (tv.tiene_control_remoto,   prestamo.devuelto_control_remoto,  'Control remoto'),
        (tv.tiene_cable_hdmi,       prestamo.devuelto_cable_hdmi,      'Cable HDMI'),
        (tv.tiene_cable_vga,        prestamo.devuelto_cable_vga,       'Cable VGA'),
        (tv.tiene_cable_corriente,  prestamo.devuelto_cable_corriente, 'Cable de corriente'),
        (tv.tiene_soporte_pared,    prestamo.devuelto_soporte_pared,   'Soporte de pared'),
        (tv.tiene_soporte_pie,      prestamo.devuelto_soporte_pie,     'Soporte de pie'),
        (tv.tiene_chromecast,       prestamo.devuelto_chromecast,      'Chromecast'),
        (tv.tiene_adaptador_hdmi,   prestamo.devuelto_adaptador_hdmi,  'Adaptador HDMI'),
    ]
    for tiene, devuelto, nombre in pares:
        if tiene:
            if devuelto:
                devueltos.append(nombre)
            else:
                faltantes.append(nombre)

    linea_devueltos = ', '.join(devueltos) if devueltos else 'Ninguno'
    linea_faltantes = (
        f"  ⚠️  FALTANTES: {', '.join(faltantes)}\n" if faltantes else ''
    )

    pulgadas_str = f' ({tv.pulgadas}")' if tv.pulgadas else ''
    asunto = f'Devolución de televisor {tv.codigo}'
    _tpl = _get_template_mail('mail_devolucion_tv')
    if _tpl:
        cuerpo = _tpl.format(
            docente=prestamo.docente.nombre_completo,
            tv=f'{tv.codigo} — {tv.marca} {tv.modelo}{pulgadas_str}',
            hora_retiro=_hora_ar(prestamo.fecha_retiro),
            hora_devolucion=_hora_ar(prestamo.fecha_devolucion_real),
            duracion=duracion,
            encargado=encargado_nombre,
        )
    else:
        cuerpo = (
            f"Devolución de televisor\n\n"
            f"Docente:      {prestamo.docente.nombre_completo}\n"
            f"TV:           {tv.codigo} — {tv.marca} {tv.modelo}{pulgadas_str}\n"
            f"Retiro:       {_hora_ar(prestamo.fecha_retiro)}\n"
            f"Devolución:   {_hora_ar(prestamo.fecha_devolucion_real)}\n"
            f"Duración:     {duracion}\n"
            f"Devueltos:    {linea_devueltos}\n"
            f"{linea_faltantes}"
            f"Observaciones:{' ' + prestamo.observaciones if prestamo.observaciones else ' —'}\n"
            f"Registró:     {encargado_nombre}\n"
        )
    try:
        _enviar_mail(correo, asunto, cuerpo)
        _log('devolucion_tv', correo, asunto, enviado=True)
        current_app.logger.info(f'[mail] Enviado a {correo} — {asunto}')
    except Exception as e:
        _log('devolucion_tv', correo, asunto, enviado=False, error=traceback.format_exc())
        current_app.logger.error(f'[mail] Error enviando a {correo}: {e}')
