from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

import random
import string

db = SQLAlchemy()

# ConfigSistema se inicializa aqui, despues de db, para evitar import circular
from models.config_sistema import _init_model as _init_config_sistema
ConfigSistema = _init_config_sistema(db)


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
    cargo    = db.Column(db.String(150))
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
    estado            = db.Column(db.String(30), default='operativo')
    motivo_servicio   = db.Column(db.String(200))
    fecha_servicio    = db.Column(db.DateTime)

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
    netbook_id = db.Column(db.Integer, db.ForeignKey('netbooks.id'), nullable=True)

    netbook_asignada = db.relationship('Netbook', foreign_keys=[netbook_id],
                                        backref='alumno_asignado', lazy=True)

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
    fecha_servicio    = db.Column(db.DateTime)      # para novedades del día

    alumno_manana = db.relationship('Alumno', foreign_keys=[alumno_manana_id],
                                    overlaps='alumno_manana_obj,netbook_manana_rel')
    alumno_tarde  = db.relationship('Alumno', foreign_keys=[alumno_tarde_id],
                                    overlaps='alumno_tarde_obj,netbook_tarde_rel')


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
    materia_prestamo      = db.Column(db.String(200), nullable=True)

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
    carro_id_2     = db.Column(db.Integer, db.ForeignKey('carros.id'), nullable=True)
    nombre         = db.Column(db.String(200), default='Carro Espacio Digital')
    minutos_alerta = db.Column(db.Integer, default=120)
    carro  = db.relationship('Carro', foreign_keys=[carro_id])
    carro_2 = db.relationship('Carro', foreign_keys=[carro_id_2])

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
#  ⚠️ Actualizado 29/04/2026 — campos estado, fecha_cierre, motivo_cierre, cerrado_por
# ─────────────────────────────────────────────────────────────────────────────

class TicketBA(db.Model):
    __tablename__ = 'tickets_ba'

    id             = db.Column(db.Integer, primary_key=True)
    nro_reclamo    = db.Column(db.String(50), nullable=False)
    usuario        = db.Column(db.String(200))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones  = db.Column(db.Text)

    # ── Campos de cierre ────────────────────────────────────────────────────
    estado         = db.Column(db.String(20), default='activo')   # 'activo' | 'resuelto'
    fecha_cierre   = db.Column(db.DateTime,   nullable=True)
    motivo_cierre  = db.Column(db.Text,       nullable=True)
    cerrado_por    = db.Column(db.String(200), nullable=True)

    netbooks = db.relationship('TicketBANetbook', backref='ticket',
                                lazy=True, cascade='all, delete-orphan')


class TicketBANetbook(db.Model):
    __tablename__ = 'tickets_ba_netbooks'

    id         = db.Column(db.Integer, primary_key=True)
    ticket_id  = db.Column(db.Integer, db.ForeignKey('tickets_ba.id'), nullable=False)
    netbook_id = db.Column(db.Integer, db.ForeignKey('netbooks.id'), nullable=True)
    carro_id   = db.Column(db.Integer, db.ForeignKey('carros.id'),   nullable=True)

    netbook = db.relationship('Netbook', foreign_keys=[netbook_id])
    carro   = db.relationship('Carro',   foreign_keys=[carro_id])


# ─────────────────────────────────────────────────────────────────────────────
#  IMPRESORA 3D
# ─────────────────────────────────────────────────────────────────────────────

class Impresora3D(db.Model):
    __tablename__ = 'impresoras_3d'

    id             = db.Column(db.Integer, primary_key=True)
    numero_interno = db.Column(db.String(20), nullable=False, unique=True)
    numero_serie   = db.Column(db.String(100))
    modelo         = db.Column(db.String(100), nullable=False)
    aula           = db.Column(db.String(50))
    # 'operativa' | 'en_servicio' | 'baja'
    estado         = db.Column(db.String(20), nullable=False, default='operativa')
    observaciones  = db.Column(db.Text)
    fecha_alta     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Impresora3D #{self.numero_interno} — {self.modelo}>'


# ─────────────────────────────────────────────────────────────────────────────
#  ASIGNACIÓN INTERNA
#  Netbooks asignadas permanentemente a un docente o área (no son préstamos).
#  Los datos de la netbook se ingresan manualmente (sin FK a netbooks).
#  Solo visible para Directivo y Administrador.
# ─────────────────────────────────────────────────────────────────────────────

class AsignacionInterna(db.Model):
    __tablename__ = 'asignaciones_internas'

    id               = db.Column(db.Integer, primary_key=True)
    # Datos de la netbook — ingreso libre, no FK
    numero_serie     = db.Column(db.String(200))
    numero_interno   = db.Column(db.String(50))
    modelo           = db.Column(db.String(200))
    # Destinatario: docente del sistema O área libre (texto)
    docente_id       = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=True)
    area             = db.Column(db.String(200))        # ej: "Dirección", "Preceptoría"

    # Metadatos
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    motivo           = db.Column(db.Text)
    activa           = db.Column(db.Boolean, default=True)
    fecha_baja       = db.Column(db.DateTime)
    motivo_baja      = db.Column(db.Text)
    registrado_por   = db.Column(db.String(200))

    docente = db.relationship('Docente', backref='asignaciones_internas', lazy=True)

    @property
    def destinatario(self):
        if self.docente:
            return self.docente.nombre_completo
        return self.area or '—'


# ─────────────────────────────────────────────────────────────────────────────
#  TV
#  Televisores del establecimiento con préstamos y componentes.
#  Agregado sesión 14 — 24/04/2026
# ─────────────────────────────────────────────────────────────────────────────

class TV(db.Model):
    __tablename__ = 'tvs'

    id                    = db.Column(db.Integer, primary_key=True)
    numero_interno        = db.Column(db.Integer, nullable=False, unique=True)
    marca                 = db.Column(db.String(80),  nullable=False)
    modelo                = db.Column(db.String(120), nullable=False)
    numero_serie          = db.Column(db.String(120), unique=True, nullable=True)
    pulgadas              = db.Column(db.Integer, nullable=True)
    aula                  = db.Column(db.String(60),  nullable=True)
    estado                = db.Column(db.String(30),  nullable=False, default='disponible')
    # estados: disponible | prestada | en_servicio | de_baja
    motivo_servicio       = db.Column(db.String(200), nullable=True)
    fecha_servicio        = db.Column(db.DateTime,    nullable=True)
    observaciones         = db.Column(db.Text,        nullable=True)
    fecha_alta            = db.Column(db.DateTime,    default=datetime.utcnow)

    # Componentes incluidos
    tiene_control_remoto   = db.Column(db.Boolean, default=False)
    tiene_cable_hdmi       = db.Column(db.Boolean, default=False)
    tiene_cable_vga        = db.Column(db.Boolean, default=False)
    tiene_cable_corriente  = db.Column(db.Boolean, default=False)
    tiene_soporte_pared    = db.Column(db.Boolean, default=False)
    tiene_soporte_pie      = db.Column(db.Boolean, default=False)
    tiene_chromecast       = db.Column(db.Boolean, default=False)
    tiene_adaptador_hdmi   = db.Column(db.Boolean, default=False)
    componentes_extra      = db.Column(db.String(300), nullable=True)

    prestamos = db.relationship('PrestamoTV', backref='tv', lazy=True,
                                order_by='PrestamoTV.fecha_retiro.desc()')

    @property
    def codigo(self):
        return f'TV-{self.numero_interno:02d}'

    @property
    def componentes_lista(self):
        comp = []
        if self.tiene_control_remoto:   comp.append('Control remoto')
        if self.tiene_cable_hdmi:       comp.append('Cable HDMI')
        if self.tiene_cable_vga:        comp.append('Cable VGA')
        if self.tiene_cable_corriente:  comp.append('Cable de corriente')
        if self.tiene_soporte_pared:    comp.append('Soporte de pared')
        if self.tiene_soporte_pie:      comp.append('Soporte de pie')
        if self.tiene_chromecast:       comp.append('Chromecast')
        if self.tiene_adaptador_hdmi:   comp.append('Adaptador HDMI')
        if self.componentes_extra:      comp.append(self.componentes_extra)
        return comp

    def __repr__(self):
        return f'<TV {self.codigo} {self.marca} {self.modelo}>'


class PrestamoTV(db.Model):
    __tablename__ = 'prestamos_tvs'

    id                        = db.Column(db.Integer, primary_key=True)
    tv_id                     = db.Column(db.Integer, db.ForeignKey('tvs.id'), nullable=False)
    docente_id                = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=True)
    nombre_solicitante        = db.Column(db.String(120), nullable=True)
    aula_destino              = db.Column(db.String(60),  nullable=True)
    motivo                    = db.Column(db.String(200), nullable=True)

    fecha_retiro              = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_devolucion_esperada = db.Column(db.DateTime, nullable=True)
    fecha_devolucion_real     = db.Column(db.DateTime, nullable=True)

    encargado_retiro_id       = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    encargado_devolucion_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    devuelto_control_remoto   = db.Column(db.Boolean, default=False)
    devuelto_cable_hdmi       = db.Column(db.Boolean, default=False)
    devuelto_cable_vga        = db.Column(db.Boolean, default=False)
    devuelto_cable_corriente  = db.Column(db.Boolean, default=False)
    devuelto_soporte_pared    = db.Column(db.Boolean, default=False)
    devuelto_soporte_pie      = db.Column(db.Boolean, default=False)
    devuelto_chromecast       = db.Column(db.Boolean, default=False)
    devuelto_adaptador_hdmi   = db.Column(db.Boolean, default=False)

    estado                    = db.Column(db.String(20), nullable=False, default='activo')
    observaciones             = db.Column(db.Text, nullable=True)

    docente              = db.relationship('Docente',  foreign_keys=[docente_id])
    encargado_retiro     = db.relationship('Usuario',  foreign_keys=[encargado_retiro_id])
    encargado_devolucion = db.relationship('Usuario',  foreign_keys=[encargado_devolucion_id])

    def __repr__(self):
        return f'<PrestamoTV {self.id}>'


# ─────────────────────────────────────────────────────────────────────────────
#  UBICACION EQUIPO
#  Registro fijo de dónde está cada TV / Pantalla Digital / Impresora 3D.
#  NO es AsignacionInterna (esa tabla es solo para netbooks fuera de carro).
#  Agregado sesión 14 — 24/04/2026
# ─────────────────────────────────────────────────────────────────────────────

class UbicacionEquipo(db.Model):
    __tablename__ = 'ubicaciones_equipos'

    id                = db.Column(db.Integer, primary_key=True)
    tipo_equipo       = db.Column(db.String(40), nullable=False)
    # valores: 'tv' | 'pantalla_digital' | 'impresora_3d'
    equipo_id         = db.Column(db.Integer, nullable=False)

    aula              = db.Column(db.String(60),  nullable=False)
    sector            = db.Column(db.String(100), nullable=True)
    piso              = db.Column(db.String(20),  nullable=True)
    descripcion       = db.Column(db.String(200), nullable=True)
    fecha_asignacion  = db.Column(db.DateTime,    default=datetime.utcnow)
    activa            = db.Column(db.Boolean,     default=True)

    registrado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    registrado_por    = db.relationship('Usuario', foreign_keys=[registrado_por_id])

    def __repr__(self):
        return f'<UbicacionEquipo {self.tipo_equipo} #{self.equipo_id} → {self.aula}>'


# ─────────────────────────────────────────────────────────────────────────────
#  MENSAJERÍA INTERNA
#  Solo visible para Encargado, Directivo y Administrador.
#  Canales: general | servicio_tecnico | prestamos | avisos
#  Agregado 29/04/2026
# ─────────────────────────────────────────────────────────────────────────────

class Mensaje(db.Model):
    __tablename__ = 'mensajes'

    id           = db.Column(db.Integer, primary_key=True)
    canal        = db.Column(db.String(50),  nullable=False, default='general')
    autor_id     = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    autor_nombre = db.Column(db.String(200))
    autor_rol    = db.Column(db.String(50))
    contenido    = db.Column(db.Text, nullable=False)
    # 'normal' | 'aviso'
    tipo         = db.Column(db.String(30),  nullable=False, default='normal')
    creado_en    = db.Column(db.DateTime, default=datetime.utcnow)

    leidos = db.relationship('MensajeLeid', backref='mensaje',
                             lazy=True, cascade='all, delete-orphan')
    autor  = db.relationship('Usuario', foreign_keys=[autor_id])

    def __repr__(self):
        return f'<Mensaje #{self.id} canal={self.canal}>'


class MensajeLeid(db.Model):
    __tablename__ = 'mensajes_leidos'

    id         = db.Column(db.Integer, primary_key=True)
    mensaje_id = db.Column(db.Integer, db.ForeignKey('mensajes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    leido_en   = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('mensaje_id', 'usuario_id',
                                          name='uq_mensaje_usuario'),)
