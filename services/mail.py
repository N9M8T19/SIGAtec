"""
services/mail.py
Envío de mails usando Gmail API con OAuth2.
Usa las mismas credenciales del sendMail.py existente.
"""

import os
import base64
import traceback
from email.mime.text import MIMEText
from flask import current_app
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from models import db

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE       = 'token.json'
GMAIL_FROM       = 'det_7_de5@bue.edu.ar'


def _get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        else:
            raise RuntimeError(
                'No hay token válido. Ejecutá sendMail.py una vez para autorizar.'
            )
    return creds


def _build_service():
    creds = _get_credentials()
    return build('gmail', 'v1', credentials=creds)


def _enviar_mail(destinatario, asunto, cuerpo):
    service  = _build_service()
    mensaje  = MIMEText(cuerpo)
    mensaje['to']      = destinatario
    mensaje['from']    = GMAIL_FROM
    mensaje['subject'] = asunto
    raw    = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()
    result = service.users().messages().send(userId='me', body={'raw': raw}).execute()
    return result


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
        return
    for correo in destinatarios:
        try:
            _enviar_mail(correo, asunto, cuerpo)
            _log(evento, correo, asunto, enviado=True)
        except Exception as e:
            _log(evento, correo, asunto, enviado=False, error=traceback.format_exc())
            current_app.logger.error(f'Error enviando mail a {correo}: {e}')


def enviar_notificacion_retiro_carro(prestamo):
    evento = 'retiro_carro'
    asunto = f'[SIGA-Tec] Retiro de carro {prestamo.carro.display}'
    cuerpo = f"""
Se registró un retiro de carro en SIGA-Tec.

Docente:        {prestamo.docente.nombre_completo}
Carro:          {prestamo.carro.display}
Aula:           {prestamo.aula or '—'}
Hora:           {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Autorizado por: {prestamo.encargado_retiro}

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_notificacion_devolucion_carro(prestamo):
    evento = 'devolucion_carro'
    asunto = f'[SIGA-Tec] Devolución — carro {prestamo.carro.display}'
    mins   = prestamo.duracion_minutos or 0
    cuerpo = f"""
Se registró la devolución de un carro en SIGA-Tec.

Docente:        {prestamo.docente.nombre_completo}
Carro:          {prestamo.carro.display}
Retiro:         {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Devolución:     {prestamo.hora_devolucion.strftime('%d/%m/%Y %H:%M')}
Duración:       {mins // 60}h {mins % 60}m
Recibido por:   {prestamo.encargado_devolucion}

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_notificacion_retiro_netbook(prestamo):
    evento = 'retiro_netbook'
    asunto = f'[SIGA-Tec] Retiro de netbooks — {prestamo.docente.nombre_completo}'
    items  = '\n'.join([f'  • N°{i.numero_interno} — {i.alumno or "Sin asignar"}' for i in prestamo.items])
    cuerpo = f"""
Se registró un préstamo de netbooks en el Espacio Digital.

Docente:        {prestamo.docente.nombre_completo}
Hora:           {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Autorizado por: {prestamo.encargado_retiro}

Netbooks retiradas:
{items}

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_notificacion_devolucion_netbook(prestamo):
    evento = 'devolucion_netbook'
    asunto = f'[SIGA-Tec] Devolución netbooks — {prestamo.docente.nombre_completo}'
    mins   = int((prestamo.hora_devolucion - prestamo.hora_retiro).total_seconds() / 60)
    cuerpo = f"""
Se registró la devolución de netbooks en SIGA-Tec.

Docente:        {prestamo.docente.nombre_completo}
Retiro:         {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Devolución:     {prestamo.hora_devolucion.strftime('%d/%m/%Y %H:%M')}
Duración:       {mins // 60}h {mins % 60}m
Recibido por:   {prestamo.encargado_devolucion}
Netbooks:       {len(prestamo.items)}

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_alerta_demora(prestamo, tipo='carro'):
    evento = 'alerta_demora'
    if tipo == 'carro':
        item   = prestamo.carro.display
        asunto = f'⚠️ [SIGA-Tec] DEMORA — carro {item} no devuelto'
    else:
        item   = f'{len(prestamo.items)} netbook(s)'
        asunto = f'⚠️ [SIGA-Tec] DEMORA — netbooks no devueltas'
    cuerpo = f"""
⚠️ ALERTA DE DEMORA

El siguiente préstamo supera el tiempo permitido.

Docente:             {prestamo.docente.nombre_completo}
Ítem:                {item}
Retirado:            {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Tiempo transcurrido: {prestamo.tiempo_transcurrido}

Por favor verificar el estado del préstamo.

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_alerta_horario(prestamo, horario, tipo='carro'):
    evento = 'alerta_horario'
    if tipo == 'carro':
        item   = prestamo.carro.display
        asunto = f'⚠️ [SIGA-Tec] CLASE TERMINADA — carro {item} no devuelto'
    else:
        item   = f'{len(prestamo.items)} netbook(s)'
        asunto = f'⚠️ [SIGA-Tec] CLASE TERMINADA — netbooks no devueltas'
    cuerpo = f"""
⚠️ ALERTA DE HORARIO

El docente terminó su módulo y no devolvió el material.

Docente:    {prestamo.docente.nombre_completo}
Materia:    {horario.materia or prestamo.docente.materia or '—'}
Módulo:     {horario.modulo} ({horario.hora_inicio} - {horario.hora_fin})
Ítem:       {item}
Retirado:   {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}

Por favor verificar la devolución.

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def init_mail(app):
    """Compatibilidad con app.py. Con Gmail API no hay nada que inicializar."""
    app.logger.info('Servicio de mail: Gmail API con OAuth2.')
