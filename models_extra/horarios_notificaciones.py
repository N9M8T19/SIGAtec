"""
Modelos para horarios de docentes y configuracion de notificaciones.
"""
from datetime import datetime
from models import db


# ─────────────────────────────────────────────────────────────────────────────
#  DÍAS DE SEMANA
# ─────────────────────────────────────────────────────────────────────────────

DIAS_SEMANA = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado']


# ─────────────────────────────────────────────────────────────────────────────
#  MÓDULOS — Horarios reales de la escuela
#
#  TURNO MAÑANA:
#    M1  07:30 - 08:10
#    M2  08:10 - 08:50
#    M3  09:00 - 09:40
#    M4  09:40 - 10:20
#    M5  10:30 - 11:10
#    M6  11:10 - 11:50
#    M7  12:00 - 12:40
#    M8  12:40 - 13:20  ← compartido con Tarde
#
#  TURNO TARDE:
#    T1  12:40 - 13:20  ← compartido con Mañana
#    T2  13:20 - 14:00
#    T3  14:00 - 14:40
#    T4  14:50 - 15:30
#    T5  15:30 - 16:10
#    T6  16:20 - 17:00
#    T7  17:00 - 17:40
#    T8  17:40 - 18:20
# ─────────────────────────────────────────────────────────────────────────────

MODULOS = {
    # ── TURNO MAÑANA ──────────────────────────────────────────────────────────
    1:  ('07:30', '08:10', 'Mañana',   'M1'),
    2:  ('08:10', '08:50', 'Mañana',   'M2'),
    3:  ('09:00', '09:40', 'Mañana',   'M3'),
    4:  ('09:40', '10:20', 'Mañana',   'M4'),
    5:  ('10:30', '11:10', 'Mañana',   'M5'),
    6:  ('11:10', '11:50', 'Mañana',   'M6'),
    7:  ('12:00', '12:40', 'Mañana',   'M7'),
    8:  ('12:40', '13:20', 'Compartido','M8/T1'),
    # ── TURNO TARDE ───────────────────────────────────────────────────────────
    9:  ('13:20', '14:00', 'Tarde',    'T2'),
    10: ('14:00', '14:40', 'Tarde',    'T3'),
    11: ('14:50', '15:30', 'Tarde',    'T4'),
    12: ('15:30', '16:10', 'Tarde',    'T5'),
    13: ('16:20', '17:00', 'Tarde',    'T6'),
    14: ('17:00', '17:40', 'Tarde',    'T7'),
    15: ('17:40', '18:20', 'Tarde',    'T8'),
}


def _get_modulos_activos():
    """
    Devuelve el dict de módulos activos.
    Si ConfigSistema tiene módulos configurados, los usa.
    Si no, usa los MODULOS por defecto definidos arriba.
    """
    try:
        from models.config_sistema import ConfigSistema
        cfg = ConfigSistema.query.first()
        if cfg:
            custom = cfg.get_modulos()
            if custom:
                return custom
    except Exception:
        pass
    return MODULOS


def _get_materias_activas():
    """
    Devuelve la lista de materias activa.
    Si ConfigSistema tiene materias configuradas, las usa.
    Si no, usa MATERIAS por defecto.
    """
    try:
        from models.config_sistema import ConfigSistema
        cfg = ConfigSistema.query.first()
        if cfg:
            custom = cfg.get_materias()
            if custom:
                return custom
    except Exception:
        pass
    return MATERIAS


def modulo_label(num):
    """Devuelve el label completo de un módulo: 'M1 — 07:30 a 08:10 (Mañana)'"""
    m = _get_modulos_activos().get(num)
    if not m:
        return f'Módulo {num}'
    inicio, fin, turno, codigo = m
    return f'{codigo} — {inicio} a {fin} ({turno})'


# ─────────────────────────────────────────────────────────────────────────────
#  MATERIAS — Lista completa de la escuela
# ─────────────────────────────────────────────────────────────────────────────

MATERIAS = sorted([
    'ADMINISTRACIÓN DE SISTEMAS Y REDES',
    'ADMINISTRACIÓN Y GESTIÓN DE BASE DATOS',
    'ANALISIS DE SISTEMAS',
    'BANCOS Y FINANZAS',
    'BASE DE DATOS',
    'BIOLOGÍA',
    'CIENCIA Y TECNOLOGÍA',
    'CHINO MANDARÍN',
    'CIUDADANÍA Y TRABAJO',
    'COMPUTACIÓN APLICADA I',
    'COMPUTACIÓN APLICADA II',
    'COMPUTACIÓN APLICADA III',
    'CONTABILIDAD I',
    'CONTABILIDAD II',
    'COORDINACIÓN DE AREA',
    'COSTOS',
    'DERECHO COMERCIAL Y ADMINISTRACIÓN',
    'DESARROLLO DE SISTEMAS',
    'ECONOMÍA Y GESTIÓN DE LAS ORGANIZACIONES',
    'ED. ARTÍSTICA',
    'EDUCACIÓN CIUDADANA',
    'EDUCACIÓN FÍSICA',
    'ESTADOS CONTABLES',
    'EXTRA CLASES',
    'FÍSICA',
    'GEOGRAFÍA',
    'GEOGRAFÍA ECONOMICA ARGENTINA',
    'GESTIÓN DE LOS PROCESOS PRODUCTIVOS',
    'HISTORIA',
    'HISTORIA DE LA INDUSTRIA Y EL COMERCIO',
    'IMPUESTOS',
    'INGLÉS',
    'INTRODUCCIÓN A LA ECONOMÍA',
    'INTRODUCCIÓN AL DERECHO',
    'LABORATORIO DE ALGORITMOS Y ESTRUCTURAS DE DATOS',
    'LABORATORIO DE PROGRAMACIÓN ORIENTADA A OBJETOS',
    'LENGUA Y LITERATURA',
    'LÓGICA COMPUTACIONAL',
    'MARKETING',
    'MATEMÁTICA',
    'MATEMÁTICA FINANCIERA',
    'ORGANIZACIÓN DE COMPUTADORAS',
    'ORGANIZACIÓN DE LA PRODUCCIÓN',
    'PAT',
    'PRÁCTICAS PROFESIONALIZANTES',
    'PROGRAMACIÓN SOBRE REDES',
    'PROYECTO INFORMÁTICO I',
    'PROYECTO INFORMÁTICO II',
    'PSICOLOGÍA DE LAS ORGANIZACIONES',
    'QUÍMICA',
    'QUÍMICA APLICADA',
    'RECURSOS HUMANOS',
    'REDES',
    'TAREAS DOCENTES',
    'TALLER DE APLICACIONES LABORALES',
    'TALLER DE BASE ELECTRICIDAD',
    'TALLER DE BASE ELECTRÓNICA',
    'TALLER DE INFORMATICA',
    'TALLER DISEÑO MULTIMEDIA',
    'TALLER INFORMATICA APLICADA Y EL CONTROL',
    'TALLER PROGRAMACIÓN',
    'TALLER PROYECTO INFORMÁTICA',
    'TALLER PROYECTO JUGUETES',
    'TEC. DE LA PRODUCCIÓN',
    'TECNOLOGIA DE LA REPRESENTACIÓN',
    'TEORÍA DE LAS ORGANIZACIONES',
])


# ─────────────────────────────────────────────────────────────────────────────
#  MODELO HorarioDocente
# ─────────────────────────────────────────────────────────────────────────────

class HorarioDocente(db.Model):
    __tablename__ = 'horarios_docentes'

    id         = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    dia        = db.Column(db.String(20), nullable=False)
    modulo     = db.Column(db.Integer, nullable=False)   # clave del dict MODULOS
    materia    = db.Column(db.String(200))
    aula       = db.Column(db.String(50))

    docente    = db.relationship('Docente', backref='horarios')

    @property
    def hora_inicio(self):
        return _get_modulos_activos().get(self.modulo, ('--:--', '--:--', '', ''))[0]

    @property
    def hora_fin(self):
        return _get_modulos_activos().get(self.modulo, ('--:--', '--:--', '', ''))[1]

    @property
    def turno_modulo(self):
        return _get_modulos_activos().get(self.modulo, ('', '', '', ''))[2]

    @property
    def codigo_modulo(self):
        return _get_modulos_activos().get(self.modulo, ('', '', '', 'M?'))[3]

    @property
    def label(self):
        return modulo_label(self.modulo)


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACION DE NOTIFICACIONES
# ─────────────────────────────────────────────────────────────────────────────

class ConfigNotificacion(db.Model):
    __tablename__ = 'config_notificaciones'

    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(150), nullable=False)
    correo     = db.Column(db.String(200), nullable=False)
    activo     = db.Column(db.Boolean, default=True)
    eventos    = db.Column(db.String(300), default='alerta_demora,alerta_horario')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def lista_eventos(self):
        return [e.strip() for e in self.eventos.split(',') if e.strip()]

    def recibe(self, evento):
        return evento in self.lista_eventos


# ─────────────────────────────────────────────────────────────────────────────
#  LOG DE NOTIFICACIONES
# ─────────────────────────────────────────────────────────────────────────────

class LogNotificacion(db.Model):
    __tablename__ = 'log_notificaciones'

    id           = db.Column(db.Integer, primary_key=True)
    evento       = db.Column(db.String(50))
    destinatario = db.Column(db.String(200))
    asunto       = db.Column(db.String(300))
    enviado      = db.Column(db.Boolean, default=False)
    error        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
