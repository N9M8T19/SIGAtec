from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────────────────────
#  USUARIO
# ─────────────────────────────────────────────────────────────────────────────

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id                = db.Column(db.Integer, primary_key=True)
    dni               = db.Column(db.String(20), unique=True, nullable=False)
    nombre            = db.Column(db.String(100), nullable=False)
    apellido          = db.Column(db.String(100), nullable=False)
    username          = db.Column(db.String(50), unique=True, nullable=False)
    password_hash     = db.Column(db.String(255))
    correo            = db.Column(db.String(150), unique=True)   # mail de Google para login
    codigo_credencial = db.Column(db.String(20), unique=True)
    rol               = db.Column(db.String(30), default='Encargado')
    activo            = db.Column(db.Boolean, default=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    ROLES = ['Encargado', 'Directivo', 'Administrador']

    PERMISOS = {
        'Encargado':     ['prestamos'],
        'Directivo':     ['prestamos', 'estadisticas', 'reportes', 'configuracion', 'todo'],
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
    estado            = db.Column(db.String(30), default='activo')
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
#  ALUMNO
# ─────────────────────────────────────────────────────────────────────────────

class Alumno(db.Model):
    __tablename__ = 'alumnos'

    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni      = db.Column(db.String(20), unique=True, nullable=False)
    curso    = db.Column(db.String(20), nullable=False)   # ej: "N1G1"
    turno    = db.Column(db.String(10), nullable=False, default='M')  # 'M' o 'T'

    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"

    def __repr__(self):
        return f'<Alumno {self.apellido} {self.nombre} ({self.curso} {self.turno})>'

    netbook_manana_rel = db.relationship('Netbook', foreign_keys='Netbook.alumno_manana_id',
                                          backref='alumno_manana_obj', lazy=True)
    netbook_tarde_rel  = db.relationship('Netbook', foreign_keys='Netbook.alumno_tarde_id',
                                          backref='alumno_tarde_obj',  lazy=True)


# ─────────────────────────────────────────────────────────────────────────────
#  NETBOOK
# ─────────────────────────────────────────────────────────────────────────────

class Netbook(db.Model):
    __tablename__ = 'netbooks'

    id                = db.Column(db.Integer, primary_key=True)
    carro_id          = db.Column(db.Integer, db.ForeignKey('carros.id'), nullable=False)
    numero_interno    = db.Column(db.String(20))
    numero_serie      = db.Column(db.String(100))
    alumno            = db.Column(db.String(200))   # campo legacy
    alumno_manana_id  = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=True)
    alumno_tarde_id   = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=True)
    estado            = db.Column(db.String(30), default='operativa')
    problema          = db.Column(db.Text)
    nro_reclamo       = db.Column(db.String(50))   # N° reclamo Mi BA Colaborativa

    alumno_manana = db.relationship('Alumno', foreign_keys=[alumno_manana_id])
    alumno_tarde  = db.relationship('Alumno', foreign_keys=[alumno_tarde_id])


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
        ahora = datetime.utcnow()
        delta = ahora - self.hora_retiro
        mins  = int(delta.total_seconds() / 60)
        if mins < 60:
            return f"{mins}m"
        return f"{mins//60}h {mins%60}m"


# ─────────────────────────────────────────────────────────────────────────────
#  PRESTAMO NETBOOK
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

    id             = db.Column(db.Integer, primary_key=True)
    prestamo_id    = db.Column(db.Integer, db.ForeignKey('prestamos_netbooks.id'), nullable=False)
    netbook_id     = db.Column(db.Integer, db.ForeignKey('netbooks.id'))
    numero_interno = db.Column(db.String(20))
    numero_serie   = db.Column(db.String(100))
    alumno         = db.Column(db.String(200))


# ─────────────────────────────────────────────────────────────────────────────
#  CARRO ESPACIO DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

class ConfigEspacioDigital(db.Model):
    __tablename__ = 'config_espacio_digital'

    id             = db.Column(db.Integer, primary_key=True)
    carro_id       = db.Column(db.Integer, db.ForeignKey('carros.id'))
    nombre         = db.Column(db.String(200), default='Carro Espacio Digital')
    minutos_alerta = db.Column(db.Integer, default=120)
    carro = db.relationship('Carro', foreign_keys=[carro_id])

# ─────────────────────────────────────────────────────────────────────────────
#  PANTALLA DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

class PantallaDigital(db.Model):
    __tablename__ = 'pantallas_digitales'

    id             = db.Column(db.Integer, primary_key=True)
    aula           = db.Column(db.String(100), nullable=False)
    numero_serie   = db.Column(db.String(100), unique=True, nullable=False)
    marca          = db.Column(db.String(100))
    modelo         = db.Column(db.String(100))
    estado         = db.Column(db.String(30), default='operativa')
    problema       = db.Column(db.Text)
    fecha_problema = db.Column(db.DateTime)
    observaciones  = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    historial = db.relationship('HistorialPantalla', backref='pantalla',
                                 lazy=True, cascade='all, delete-orphan',
                                 order_by='HistorialPantalla.fecha.desc()')

    @property
    def display(self):
        return f"Aula {self.aula}"

    @property
    def estado_badge(self):
        badges = {
            'operativa':        ('bg-green-100 text-green-700',   'Operativa'),
            'servicio_tecnico': ('bg-orange-100 text-orange-700', 'Servicio Técnico'),
            'baja':             ('bg-red-100 text-red-700',        'Baja'),
        }
        return badges.get(self.estado, ('bg-gray-100 text-gray-600', self.estado))


class HistorialPantalla(db.Model):
    __tablename__ = 'historial_pantallas'

    id          = db.Column(db.Integer, primary_key=True)
    pantalla_id = db.Column(db.Integer, db.ForeignKey('pantallas_digitales.id'), nullable=False)
    evento      = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    usuario     = db.Column(db.String(200))
    fecha       = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
#  TICKET BA COLABORATIVA
# ─────────────────────────────────────────────────────────────────────────────

class TicketBA(db.Model):
    __tablename__ = 'tickets_ba'

    id             = db.Column(db.Integer, primary_key=True)
    nro_reclamo    = db.Column(db.String(50), nullable=False)
    usuario        = db.Column(db.String(200))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones  = db.Column(db.Text)

    netbooks = db.relationship('TicketBANetbook', backref='ticket',
                                lazy=True, cascade='all, delete-orphan')


class TicketBANetbook(db.Model):
    __tablename__ = 'tickets_ba_netbooks'

    id         = db.Column(db.Integer, primary_key=True)
    ticket_id  = db.Column(db.Integer, db.ForeignKey('tickets_ba.id'), nullable=False)
    netbook_id = db.Column(db.Integer, db.ForeignKey('netbooks.id'), nullable=True)

    netbook = db.relationship('Netbook', foreign_keys=[netbook_id])
