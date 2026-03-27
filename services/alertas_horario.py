"""
services/alertas_horario.py
Chequea préstamos activos contra horarios de docentes.
Envía alerta cuando el módulo del docente ya terminó y no devolvió.
Se ejecuta periódicamente desde un hilo de fondo.
"""

import time
import threading
from datetime import datetime


def _chequear_alertas(app):
    """Lógica principal de chequeo. Corre dentro del contexto de la app."""
    with app.app_context():
        from models import PrestamoCarro, PrestamoNetbook
        from models_extra.horarios_notificaciones import HorarioDocente, MODULOS, LogNotificacion
        from services.mail import enviar_alerta_horario, enviar_alerta_demora
        from config import Config
        from models import db

        ahora     = datetime.now()
        dia_actual = ahora.strftime('%A')  # En inglés, mapeamos a español
        dia_map   = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado'
        }
        dia_es = dia_map.get(dia_actual, '')

        hora_actual_str = ahora.strftime('%H:%M')

        # ── Chequeo por horario de módulos ────────────────────────────────
        for prestamo in PrestamoCarro.query.filter_by(estado='activo').all():
            horarios = HorarioDocente.query.filter_by(
                docente_id=prestamo.docente_id,
                dia=dia_es
            ).all()
            for h in horarios:
                hora_fin = MODULOS.get(h.modulo, (None, None))[1]
                if hora_fin and hora_actual_str >= hora_fin:
                    # Ya terminó el módulo — verificar si ya se envió alerta hoy
                    ya_enviado = LogNotificacion.query.filter(
                        LogNotificacion.evento == 'alerta_horario',
                        LogNotificacion.destinatario.like('%'),
                        LogNotificacion.asunto.like(f'%carro {prestamo.carro.display}%'),
                        LogNotificacion.created_at >= ahora.replace(hour=0, minute=0, second=0)
                    ).first()
                    if not ya_enviado:
                        enviar_alerta_horario(prestamo, h, tipo='carro')

        for prestamo in PrestamoNetbook.query.filter_by(estado='activo').all():
            horarios = HorarioDocente.query.filter_by(
                docente_id=prestamo.docente_id,
                dia=dia_es
            ).all()
            for h in horarios:
                hora_fin = MODULOS.get(h.modulo, (None, None))[1]
                if hora_fin and hora_actual_str >= hora_fin:
                    ya_enviado = LogNotificacion.query.filter(
                        LogNotificacion.evento == 'alerta_horario',
                        LogNotificacion.asunto.like(f'%{prestamo.docente.nombre_completo}%'),
                        LogNotificacion.created_at >= ahora.replace(hour=0, minute=0, second=0)
                    ).first()
                    if not ya_enviado:
                        enviar_alerta_horario(prestamo, h, tipo='netbook')

        # ── Chequeo de demora general (tiempo configurado) ─────────────────
        limite_mins = Config.MINUTOS_ALERTA_PRESTAMO

        for prestamo in PrestamoCarro.query.filter_by(estado='activo').all():
            mins = int((datetime.utcnow() - prestamo.hora_retiro).total_seconds() / 60)
            if mins >= limite_mins:
                ya_enviado = LogNotificacion.query.filter(
                    LogNotificacion.evento == 'alerta_demora',
                    LogNotificacion.asunto.like(f'%carro {prestamo.carro.display}%'),
                    LogNotificacion.created_at >= ahora.replace(hour=0, minute=0, second=0)
                ).first()
                if not ya_enviado:
                    enviar_alerta_demora(prestamo, tipo='carro')

        for prestamo in PrestamoNetbook.query.filter_by(estado='activo').all():
            mins = int((datetime.utcnow() - prestamo.hora_retiro).total_seconds() / 60)
            if mins >= limite_mins:
                ya_enviado = LogNotificacion.query.filter(
                    LogNotificacion.evento == 'alerta_demora',
                    LogNotificacion.asunto.like(f'%{prestamo.docente.nombre_completo}%'),
                    LogNotificacion.created_at >= ahora.replace(hour=0, minute=0, second=0)
                ).first()
                if not ya_enviado:
                    enviar_alerta_demora(prestamo, tipo='netbook')


def iniciar_scheduler_alertas(app):
    """
    Lanza un hilo de fondo que chequea alertas cada 10 minutos.
    Llamar desde create_app().
    """
    def loop():
        time.sleep(30)  # Esperar arranque de la app
        while True:
            try:
                _chequear_alertas(app)
            except Exception as e:
                app.logger.error(f'Error en chequeo de alertas: {e}')
            time.sleep(60 * 10)  # Cada 10 minutos

    hilo = threading.Thread(target=loop, daemon=True, name='alertas-scheduler')
    hilo.start()
    app.logger.info('Scheduler de alertas iniciado (cada 10 min).')
