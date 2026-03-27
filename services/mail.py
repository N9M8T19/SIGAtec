"""
services/mail.py
Servicio centralizado de envío de mails via Gmail (SMTP).

Configuración necesaria en config.py o variables de entorno:
    MAIL_USERNAME   = 'escuela@gmail.com'
    MAIL_PASSWORD   = 'xxxx xxxx xxxx xxxx'  # Contraseña de aplicación Google
    MAIL_DEFAULT_SENDER = 'SIGA-Tec <escuela@gmail.com>'
"""

from flask_mail import Mail, Message
from flask import current_app
from models import db
# Importación lazy para evitar circular imports
import traceback

mail = Mail()


def init_mail(app):
    """Llamar desde create_app() después de configurar la app."""
    app.config.setdefault('MAIL_SERVER',   'smtp.gmail.com')
    app.config.setdefault('MAIL_PORT',     587)
    app.config.setdefault('MAIL_USE_TLS',  True)
    app.config.setdefault('MAIL_USE_SSL',  False)
    mail.init_app(app)


def _destinatarios_por_evento(evento):
    """Retorna lista de correos activos que reciben ese tipo de evento."""
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


def enviar_notificacion_retiro_carro(prestamo):
    """Notifica retiro de carro a los configurados."""
    evento  = 'retiro_carro'
    asunto  = f'[SIGA-Tec] Retiro de carro {prestamo.carro.display}'
    cuerpo  = f"""
Se registró un retiro de carro en SIGA-Tec.

Docente:     {prestamo.docente.nombre_completo}
Carro:       {prestamo.carro.display}
Aula:        {prestamo.aula or '—'}
Hora:        {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Autorizado por: {prestamo.encargado_retiro}

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_notificacion_devolucion_carro(prestamo):
    """Notifica devolución de carro."""
    evento  = 'devolucion_carro'
    asunto  = f'[SIGA-Tec] Devolución — carro {prestamo.carro.display}'
    mins    = prestamo.duracion_minutos or 0
    cuerpo  = f"""
Se registró la devolución de un carro en SIGA-Tec.

Docente:     {prestamo.docente.nombre_completo}
Carro:       {prestamo.carro.display}
Retiro:      {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Devolución:  {prestamo.hora_devolucion.strftime('%d/%m/%Y %H:%M')}
Duración:    {mins // 60}h {mins % 60}m
Recibido por: {prestamo.encargado_devolucion}

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_notificacion_retiro_netbook(prestamo):
    """Notifica retiro de netbooks del Espacio Digital."""
    evento  = 'retiro_netbook'
    asunto  = f'[SIGA-Tec] Retiro de netbooks — {prestamo.docente.nombre_completo}'
    items   = '\n'.join([f'  • N°{i.numero_interno} — {i.alumno or "Sin asignar"}' for i in prestamo.items])
    cuerpo  = f"""
Se registró un préstamo de netbooks en el Espacio Digital.

Docente:     {prestamo.docente.nombre_completo}
Hora:        {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Autorizado por: {prestamo.encargado_retiro}

Netbooks retiradas:
{items}

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_notificacion_devolucion_netbook(prestamo):
    """Notifica devolución de netbooks."""
    evento  = 'devolucion_netbook'
    asunto  = f'[SIGA-Tec] Devolución netbooks — {prestamo.docente.nombre_completo}'
    mins    = int((prestamo.hora_devolucion - prestamo.hora_retiro).total_seconds() / 60)
    cuerpo  = f"""
Se registró la devolución de netbooks en SIGA-Tec.

Docente:     {prestamo.docente.nombre_completo}
Retiro:      {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Devolución:  {prestamo.hora_devolucion.strftime('%d/%m/%Y %H:%M')}
Duración:    {mins // 60}h {mins % 60}m
Recibido por: {prestamo.encargado_devolucion}
Netbooks:    {len(prestamo.items)}

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_alerta_demora(prestamo, tipo='carro'):
    """
    Alerta cuando un préstamo supera el tiempo configurado (MINUTOS_ALERTA_PRESTAMO).
    tipo = 'carro' | 'netbook'
    """
    evento = 'alerta_demora'
    if tipo == 'carro':
        item   = prestamo.carro.display
        asunto = f'⚠️ [SIGA-Tec] DEMORA — carro {item} no devuelto'
    else:
        item   = f'{len(prestamo.items)} netbook(s)'
        asunto = f'⚠️ [SIGA-Tec] DEMORA — netbooks no devueltas'

    cuerpo = f"""
⚠️ ALERTA DE DEMORA — El siguiente préstamo supera el tiempo permitido.

Docente:     {prestamo.docente.nombre_completo}
Ítem:        {item}
Retirado:    {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}
Tiempo transcurrido: {prestamo.tiempo_transcurrido}

Por favor verificar el estado del préstamo.

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def enviar_alerta_horario(prestamo, horario, tipo='carro'):
    """
    Alerta cuando un docente termina su módulo y no devolvió el material.
    """
    evento = 'alerta_horario'
    if tipo == 'carro':
        item   = prestamo.carro.display
        asunto = f'⚠️ [SIGA-Tec] CLASE TERMINADA — carro {item} no devuelto'
    else:
        item   = f'{len(prestamo.items)} netbook(s)'
        asunto = f'⚠️ [SIGA-Tec] CLASE TERMINADA — netbooks no devueltas'

    cuerpo = f"""
⚠️ ALERTA DE HORARIO — El docente terminó su módulo y no devolvió el material.

Docente:     {prestamo.docente.nombre_completo}
Materia:     {horario.materia or prestamo.docente.materia or '—'}
Módulo:      {horario.modulo} ({horario.hora_inicio} - {horario.hora_fin})
Ítem:        {item}
Retirado:    {prestamo.hora_retiro.strftime('%d/%m/%Y %H:%M')}

Por favor verificar la devolución.

---
Sistema SIGA-Tec — E.T. N°7 D.E. 5
"""
    _enviar_a_todos(evento, asunto, cuerpo)


def _enviar_a_todos(evento, asunto, cuerpo):
    """Envía el mail a todos los destinatarios configurados para el evento."""
    destinatarios = _destinatarios_por_evento(evento)
    if not destinatarios:
        return

    for correo in destinatarios:
        try:
            msg = Message(
                subject=asunto,
                recipients=[correo],
                body=cuerpo,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', current_app.config.get('MAIL_USERNAME'))
            )
            mail.send(msg)
            _log(evento, correo, asunto, enviado=True)
        except Exception as e:
            _log(evento, correo, asunto, enviado=False, error=traceback.format_exc())
            current_app.logger.error(f'Error enviando mail a {correo}: {e}')
