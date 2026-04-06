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


def _enviar_a_todos(evento, asunto, cuerpo):
    destinatarios = _destinatarios_por_evento(evento)
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


# ── Notificaciones de carros ───────────────────────────────────────────────────

def enviar_notificacion_retiro_carro(prestamo):
    evento = 'retiro_carro'
    asunto = f'Retiro de carro {prestamo.carro.display}'
    cuerpo = f"""Retiro de carro

Docente:   {prestamo.docente.nombre_completo}
Carro:     {prestamo.carro.display}
Aula:      {prestamo.aula or '—'}
Hora:      {_hora_ar(prestamo.hora_retiro)}
Registró:  {prestamo.encargado_retiro}
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_notificacion_devolucion_carro(prestamo):
    evento = 'devolucion_carro'
    asunto = f'Devolución de carro {prestamo.carro.display}'
    mins   = prestamo.duracion_minutos or 0
    cuerpo = f"""Devolución de carro

Docente:    {prestamo.docente.nombre_completo}
Carro:      {prestamo.carro.display}
Retiro:     {_hora_ar(prestamo.hora_retiro)}
Devolución: {_hora_ar(prestamo.hora_devolucion)}
Duración:   {mins // 60}h {mins % 60}m
Registró:   {prestamo.encargado_devolucion}
"""
    _enviar_a_todos(evento, asunto, cuerpo)


# ── Notificaciones de netbooks ─────────────────────────────────────────────────

def enviar_notificacion_retiro_netbook(prestamo):
    evento = 'retiro_netbook'
    asunto = f'Retiro de netbooks — {prestamo.docente.nombre_completo}'
    items  = '\n'.join(
        [f'  • N°{i.numero_interno} — {i.alumno or "Sin asignar"}' for i in prestamo.items]
    )
    cuerpo = f"""Retiro de netbooks

Docente:   {prestamo.docente.nombre_completo}
Hora:      {_hora_ar(prestamo.hora_retiro)}
Registró:  {prestamo.encargado_retiro}

Netbooks:
{items}
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_notificacion_devolucion_netbook(prestamo):
    evento = 'devolucion_netbook'
    asunto = f'Devolución de netbooks — {prestamo.docente.nombre_completo}'
    mins   = int((prestamo.hora_devolucion - prestamo.hora_retiro).total_seconds() / 60)
    cuerpo = f"""Devolución de netbooks

Docente:    {prestamo.docente.nombre_completo}
Retiro:     {_hora_ar(prestamo.hora_retiro)}
Devolución: {_hora_ar(prestamo.hora_devolucion)}
Duración:   {mins // 60}h {mins % 60}m
Registró:   {prestamo.encargado_devolucion}
Netbooks:   {len(prestamo.items)}
"""
    _enviar_a_todos(evento, asunto, cuerpo)


# ── Alertas ────────────────────────────────────────────────────────────────────

def enviar_alerta_demora(prestamo, tipo='carro'):
    evento = 'alerta_demora'
    if tipo == 'carro':
        item   = prestamo.carro.display
        asunto = f'⚠️ DEMORA — carro {item} no devuelto'
    else:
        item   = f'{len(prestamo.items)} netbook(s)'
        asunto = '⚠️ DEMORA — netbooks no devueltas'
    cuerpo = f"""⚠️ Alerta de demora

Docente:   {prestamo.docente.nombre_completo}
Ítem:      {item}
Retirado:  {_hora_ar(prestamo.hora_retiro)}
Transcurrido: {prestamo.tiempo_transcurrido}

Por favor verificar el estado del préstamo.
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_alerta_horario(prestamo, horario, tipo='carro'):
    evento = 'alerta_horario'
    if tipo == 'carro':
        item   = prestamo.carro.display
        asunto = f'⚠️ Clase terminada — carro {item} no devuelto'
    else:
        item   = f'{len(prestamo.items)} netbook(s)'
        asunto = '⚠️ Clase terminada — netbooks no devueltas'
    cuerpo = f"""⚠️ El docente terminó su módulo y no devolvió el material.

Docente:  {prestamo.docente.nombre_completo}
Materia:  {horario.materia or prestamo.docente.materia or '—'}
Módulo:   {horario.modulo} ({horario.hora_inicio} - {horario.hora_fin})
Ítem:     {item}
Retirado: {_hora_ar(prestamo.hora_retiro)}
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def init_mail(app):
    """Compatibilidad con app.py."""
    usuario = os.environ.get('GMAIL_USER', 'aulamagnaespaciodigital@gmail.com')
    tiene   = bool(os.environ.get('GMAIL_APP_PASSWORD'))
    app.logger.info(
        f'Servicio de mail: SMTP Gmail. '
        f'Usuario: {usuario} | App Password configurada: {tiene}'
    )
