"""
Modelos para horarios de docentes y configuracion de notificaciones.
Agregar al final de models/__init__.py (o importar desde aca).
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# db se importa desde models para compartir la misma instancia
from models import db


# ─────────────────────────────────────────────────────────────────────────────
#  HORARIO DOCENTE
#  Cada fila = un módulo que dicta un docente en un día de la semana
# ─────────────────────────────────────────────────────────────────────────────

DIAS_SEMANA = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado']

# Módulos estándar de escuela técnica (ajustar si cambia el horario de la escuela)
MODULOS = {
    1:  ('07:30', '08:20'),
    2:  ('08:20', '09:10'),
    3:  ('09:10', '10:00'),
    4:  ('10:00', '10:50'),
    5:  ('10:50', '11:40'),
    6:  ('11:40', '12:30'),
    7:  ('13:00', '13:50'),
    8:  ('13:50', '14:40'),
    9:  ('14:40', '15:30'),
    10: ('15:30', '16:20'),
    11: ('16:20', '17:10'),
    12: ('17:10', '18:00'),
    13: ('18:00', '18:50'),
    14: ('18:50', '19:40'),
    15: ('19:40', '20:30'),
    16: ('20:30', '21:20'),
}


class HorarioDocente(db.Model):
    __tablename__ = 'horarios_docentes'

    id         = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    dia        = db.Column(db.String(20), nullable=False)   # 'Lunes', 'Martes', etc.
    modulo     = db.Column(db.Integer, nullable=False)       # 1-16
    materia    = db.Column(db.String(150))                   # puede diferir del campo general
    aula       = db.Column(db.String(50))

    docente    = db.relationship('Docente', backref='horarios')

    @property
    def hora_inicio(self):
        return MODULOS.get(self.modulo, ('--:--', '--:--'))[0]

    @property
    def hora_fin(self):
        return MODULOS.get(self.modulo, ('--:--', '--:--'))[1]

    @property
    def label(self):
        return f"{self.dia} — Módulo {self.modulo} ({self.hora_inicio}-{self.hora_fin})"


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACION DE NOTIFICACIONES
#  Lista de mails que reciben alertas de movimientos y devoluciones tardías
# ─────────────────────────────────────────────────────────────────────────────

class ConfigNotificacion(db.Model):
    __tablename__ = 'config_notificaciones'

    id        = db.Column(db.Integer, primary_key=True)
    nombre    = db.Column(db.String(150), nullable=False)   # nombre descriptivo
    correo    = db.Column(db.String(200), nullable=False)   # mail destino
    activo    = db.Column(db.Boolean, default=True)
    # Tipos de eventos que recibe (separados por coma)
    # Opciones: 'retiro_carro', 'devolucion_carro', 'retiro_netbook',
    #           'devolucion_netbook', 'alerta_demora', 'alerta_horario'
    eventos   = db.Column(db.String(300), default='alerta_demora,alerta_horario')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def lista_eventos(self):
        return [e.strip() for e in self.eventos.split(',') if e.strip()]

    def recibe(self, evento):
        return evento in self.lista_eventos


# ─────────────────────────────────────────────────────────────────────────────
#  LOG DE NOTIFICACIONES ENVIADAS
# ─────────────────────────────────────────────────────────────────────────────

class LogNotificacion(db.Model):
    __tablename__ = 'log_notificaciones'

    id          = db.Column(db.Integer, primary_key=True)
    evento      = db.Column(db.String(50))
    destinatario = db.Column(db.String(200))
    asunto      = db.Column(db.String(300))
    enviado     = db.Column(db.Boolean, default=False)
    error       = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
