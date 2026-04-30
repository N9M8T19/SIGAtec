"""
models/config_sistema.py
Modelo para persistir la configuración editable del sistema.

IMPORTANTE: NO importa 'db' a nivel módulo — evita import circular.
La clase real se construye mediante _init_model(db) desde models/__init__.py.
"""

import json
import sys


# ── Secciones del sistema que se pueden habilitar/deshabilitar para el Encargado ──
SECCIONES_DISPONIBLES = [
    # (clave, label, descripción)
    # ── Inventario ────────────────────────────────────────────────────────────
    ('carros',              'Carros',                 'ABM de carros de netbooks'),
    ('servicio_tecnico',    'Servicio Técnico',       'Pantalla de netbooks y carros en servicio'),
    ('tickets_ba',          'Tickets BA Colaborativa','Gestión de reclamos BA'),
    ('pantallas',           'Pantallas Digitales',    'ABM de pizarrones interactivos'),
    ('impresoras3d',        'Impresoras 3D',          'ABM de impresoras 3D'),
    ('stock',               'Control de Stock',       'Relevamiento físico por carro'),
    ('stock_masivo',        'Stock Masivo',           'Control masivo de todas las netbooks'),
    ('tvs',                 'Televisores',            'ABM y préstamos de televisores'),
    ('obsolescencia',       'Obsolescencia',          'Registro de netbooks obsoletas y reemplazos'),
    ('transferencias',      'Transferir Netbooks',    'Mover netbooks entre carros'),
    ('asignaciones',        'Asignaciones Internas',  'Netbooks asignadas a docentes o áreas'),
    # ── Préstamos ─────────────────────────────────────────────────────────────
    ('prestamos_carros',    'Préstamos Carros',       'Retiro y devolución de llaves'),
    ('espacio_digital',     'Espacio Digital',        'Préstamo de netbooks individuales'),
    ('prestamos_tvs',       'Préstamos Televisores',  'Préstamos activos de TVs'),
    ('historial',           'Historial',              'Historial completo de préstamos'),
    # ── Personas ──────────────────────────────────────────────────────────────
    ('docentes',            'Docentes',               'ABM de docentes'),
    ('alumnos',             'Alumnos',                'Listado y asignación de alumnos'),
    ('usuarios',            'Usuarios',               'ABM de usuarios del sistema'),
    # ── Reportes ──────────────────────────────────────────────────────────────
    ('estadisticas',        'Estadísticas',           'Estadísticas de préstamos (solo Admin/Directivo por defecto)'),
    ('etiquetas',           'Etiquetas',              'Generación de etiquetas adhesivas'),
    # ── Comunicación ──────────────────────────────────────────────────────────
    ('mensajeria',          'Mensajería',             'Chat interno entre el equipo'),
    # ── Sistema ───────────────────────────────────────────────────────────────
    ('sesiones',            'Sesiones',               'Historial de sesiones de encargados'),
    ('importar',            'Importar Drive',         'Importación de datos desde Google Drive'),
    ('notificaciones',      'Notificaciones',         'Configuración de alertas por mail'),
    ('backups',             'Backups',                'Descarga de backups de la base de datos'),
    ('mantenimiento',       'Mantenimiento',          'Administración del historial de préstamos'),
    ('config_sistema',      'Config. Sistema',        'Configuración general del sistema'),
]

# Secciones habilitadas por defecto para el Encargado (todas)
SECCIONES_DEFAULT = [s[0] for s in SECCIONES_DISPONIBLES]


def _init_model(db):
    """
    Llamado desde models/__init__.py después de crear 'db'.
    Construye y registra la clase ConfigSistema con el db real.
    """

    class ConfigSistema(db.Model):
        __tablename__ = 'config_sistema'

        id                        = db.Column(db.Integer, primary_key=True)
        _materias_json            = db.Column('materias_json', db.Text, default='[]')
        _modulos_json             = db.Column('modulos_json', db.Text, default='{}')
        _secciones_encargado_json = db.Column('secciones_encargado_json', db.Text, default='[]')
        mail_retiro_carro         = db.Column(db.Text, default='')
        mail_devolucion_carro     = db.Column(db.Text, default='')
        mail_retiro_nb            = db.Column(db.Text, default='')
        mail_devolucion_nb        = db.Column(db.Text, default='')

        @classmethod
        def obtener(cls):
            cfg = cls.query.first()
            if not cfg:
                cfg = cls()
                db.session.add(cfg)
                db.session.commit()
            return cfg

        # ── Materias ──────────────────────────────────────────────────────────
        def get_materias(self):
            try:
                data = json.loads(self._materias_json or '[]')
                return data if isinstance(data, list) and data else []
            except Exception:
                return []

        def set_materias(self, lista):
            self._materias_json = json.dumps(lista, ensure_ascii=False)
            db.session.commit()

        # ── Módulos ───────────────────────────────────────────────────────────
        def get_modulos(self):
            try:
                raw = json.loads(self._modulos_json or '{}')
                return {int(k): tuple(v) for k, v in raw.items()} if raw else {}
            except Exception:
                return {}

        def set_modulos(self, diccionario):
            serializable = {str(k): list(v) for k, v in diccionario.items()}
            self._modulos_json = json.dumps(serializable, ensure_ascii=False)
            db.session.commit()

        # ── Secciones del Encargado ───────────────────────────────────────────
        def get_secciones_encargado(self):
            """Devuelve lista de claves de secciones habilitadas para el Encargado."""
            try:
                raw = self._secciones_encargado_json or '[]'
                data = json.loads(raw)
                # Si la lista está vacía (primera vez), devuelve todas habilitadas
                return data if isinstance(data, list) and data else list(SECCIONES_DEFAULT)
            except Exception:
                return list(SECCIONES_DEFAULT)

        def set_secciones_encargado(self, lista):
            self._secciones_encargado_json = json.dumps(lista, ensure_ascii=False)
            db.session.commit()

        def encargado_puede_ver(self, seccion):
            """True si la sección está habilitada para el Encargado."""
            return seccion in self.get_secciones_encargado()

        # ── Guardar ───────────────────────────────────────────────────────────
        def guardar(self):
            db.session.commit()

    # Reemplaza el placeholder en este módulo para que los imports posteriores
    # encuentren la clase real
    sys.modules[__name__].ConfigSistema = ConfigSistema
    return ConfigSistema


# ── Placeholder ───────────────────────────────────────────────────────────────
class ConfigSistema:
    """Placeholder reemplazado por _init_model(db)."""
    @classmethod
    def obtener(cls):
        raise RuntimeError('ConfigSistema no inicializada — llamar _init_model(db) primero.')
    @classmethod
    def query(cls):
        raise RuntimeError('ConfigSistema no inicializada.')
