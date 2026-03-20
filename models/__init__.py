from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────────────────────
#  USUARIO (encargados, directivos, admin)
# ─────────────────────────────────────────────────────────────────────────────

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id              = db.Column(db.Integer, primary_key=True)
    dni             = db.Column(db.String(20), unique=True, nullable=False)
    nombre          = db.Column(db.String(100), nullable=False)
    apellido        = db.Column(db.String(100), nullable=False)
    username        = db.Column(db.String(50), unique=True, nullable=False)
    password_hash   = db.Column(db.String(255))
    codigo_credencial = db.Column(db.String(20), unique=True)
    rol             = db.Column(db.String(30), default='Encargado')
    activo          = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    ROLES = ['Encargado', 'Directivo', 'Administrador']
    PERMISOS = {
        'Encargado':     ['prestamos'],
        'Directivo':     ['prestamos', 'estadisticas', 'reportes'],
        'Administrador': ['prestamos', 'estadisticas', 'reportes', 'configuracion', 'todo'],
    }

    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def tiene_permiso(self, permiso):
        permisos = self.PERMISOS.get(self.rol, [])
        return permiso in permisos or 'todo' in permisos

    @staticmethod
    def generar_codigo():
        chars = ''.join(c for c in (string.ascii_uppercase + string.digits)
                        if c not in 'O0I1L')
        while True:
            codigo = "ENC" + ''.join(random.choices(chars, k=6))
            if not Usuario.query.filter_by(codigo_credencial=codigo).first():
                return codigo


# ─────────────────────────────────────────────────────────────────────────────
#  DOCENTE
# ─────────────────────────────────────────────────────────────────────────────

class Docente(db.Model):
    __tablename__ = 'docentes'

    id       = db.Column(db.Integer, primary_key=True)
    dni      = db.Column(db.String(20), unique=True, nullable=False)
    nombre   = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    materia  = db.Column(db.String(150))
    correo   = db.Column(db.String(150))
    turno    = db.Column(db.String(50))
    activo   = db.Column(db.Boolean, default=True)

    prestamos_carros   = db.relationship('PrestamoCarro', backref='docente', lazy=True)
    prestamos_netbooks = db.relationship('PrestamoNetbook', backref='docente', lazy=True)

    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"


# ─────────────────────────────────────────────────────────────────────────────
#  CARRO
# ─────────────────────────────────────────────────────────────────────────────

class Carro(db.Model):
    __tablename__ = 'carros'

    id                = db.Column(db.Integer, primary_key=True)
    numero_fisico     = db.Column(db.String(20))
    numero_serie      = db.Column(db.String(100))
    division          = db.Column(db.String(100))
    aula              = db.Column(db.String(100))
    sheet_url         = db.Column(db.String(500))
    estado            = db.Column(db.String(30), default='activo')  # activo/reparacion/baja
    problema          = db.Column(db.Text)
    fecha_reparacion  = db.Column(db.String(50))

    netbooks  = db.relationship('Netbook', backref='carro', lazy=True,
                                 cascade='all, delete-orphan')
    prestamos = db.relationship('PrestamoCarro', backref='carro', lazy=True)

    @property
    def display(self):
        return f"#{self.numero_fisico}" if self.numero_fisico else f"ID:{self.id}"

    @property
    def total_netbooks(self):
        return len(self.netbooks)

    @property
    def operativas(self):
        return len([n for n in self.netbooks if n.estado == 'operativa'])

    @property
    def en_servicio(self):
        return len([n for n in self.netbooks if n.estado == 'servicio_tecnico'])


# ─────────────────────────────────────────────────────────────────────────────
#  NETBOOK
# ─────────────────────────────────────────────────────────────────────────────

class Netbook(db.Model):
    __tablename__ = 'netbooks'

    id             = db.Column(db.Integer, primary_key=True)
    carro_id       = db.Column(db.Integer, db.ForeignKey('carros.id'), nullable=False)
    numero_interno = db.Column(db.String(20))
    numero_serie   = db.Column(db.String(100))
    alumno         = db.Column(db.String(200))
    estado         = db.Column(db.String(30), default='operativa')  # operativa/servicio_tecnico
    problema       = db.Column(db.Text)


# ─────────────────────────────────────────────────────────────────────────────
#  PRESTAMO CARRO
# ─────────────────────────────────────────────────────────────────────────────

class PrestamoCarro(db.Model):
    __tablename__ = 'prestamos_carros'

    id                    = db.Column(db.Integer, primary_key=True)
    codigo                = db.Column(db.String(20), unique=True)
    docente_id            = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    carro_id              = db.Column(db.Integer, db.ForeignKey('carros.id'), nullable=False)
    aula                  = db.Column(db.String(100))
    hora_retiro           = db.Column(db.DateTime, default=datetime.utcnow)
    hora_devolucion       = db.Column(db.DateTime)
    estado                = db.Column(db.String(20), default='activo')
    encargado_retiro      = db.Column(db.String(200))
    encargado_devolucion  = db.Column(db.String(200))

    @property
    def duracion_minutos(self):
        if self.hora_devolucion:
            delta = self.hora_devolucion - self.hora_retiro
            return int(delta.total_seconds() / 60)
        return None

    @property
    def tiempo_transcurrido(self):
        from datetime import timezone
        ahora = datetime.utcnow()
        delta = ahora - self.hora_retiro
        mins  = int(delta.total_seconds() / 60)
        if mins < 60:
            return f"{mins}m"
        return f"{mins//60}h {mins%60}m"


# ─────────────────────────────────────────────────────────────────────────────
#  PRESTAMO NETBOOK (Espacio Digital)
# ─────────────────────────────────────────────────────────────────────────────

class PrestamoNetbook(db.Model):
    __tablename__ = 'prestamos_netbooks'

    id                    = db.Column(db.Integer, primary_key=True)
    codigo                = db.Column(db.String(20), unique=True)
    docente_id            = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False)
    hora_retiro           = db.Column(db.DateTime, default=datetime.utcnow)
    hora_devolucion       = db.Column(db.DateTime)
    estado                = db.Column(db.String(20), default='activo')
    encargado_retiro      = db.Column(db.String(200))
    encargado_devolucion  = db.Column(db.String(200))

    items = db.relationship('PrestamoNetbookItem', backref='prestamo',
                             lazy=True, cascade='all, delete-orphan')

    @property
    def tiempo_transcurrido(self):
        ahora = datetime.utcnow()
        delta = ahora - self.hora_retiro
        mins  = int(delta.total_seconds() / 60)
        if mins < 60:
            return f"{mins}m"
        return f"{mins//60}h {mins%60}m"


class PrestamoNetbookItem(db.Model):
    __tablename__ = 'prestamo_netbook_items'

    id           = db.Column(db.Integer, primary_key=True)
    prestamo_id  = db.Column(db.Integer, db.ForeignKey('prestamos_netbooks.id'), nullable=False)
    netbook_id   = db.Column(db.Integer, db.ForeignKey('netbooks.id'))
    numero_interno = db.Column(db.String(20))
    numero_serie   = db.Column(db.String(100))
    alumno         = db.Column(db.String(200))


# ─────────────────────────────────────────────────────────────────────────────
#  CARRO ESPACIO DIGITAL (configuración)
# ─────────────────────────────────────────────────────────────────────────────

class ConfigEspacioDigital(db.Model):
    __tablename__ = 'config_espacio_digital'

    id            = db.Column(db.Integer, primary_key=True)
    carro_id      = db.Column(db.Integer, db.ForeignKey('carros.id'))
    nombre        = db.Column(db.String(200), default='Carro Espacio Digital')
    minutos_alerta = db.Column(db.Integer, default=120)
