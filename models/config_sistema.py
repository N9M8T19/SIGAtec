"""
models/config_sistema.py
Modelo para persistir la configuración editable del sistema.

IMPORTANTE: NO importa 'db' a nivel módulo — evita import circular.
La clase real se construye mediante _init_model(db) desde models/__init__.py.
"""

import json
import sys


def _init_model(db):
    """
    Llamado desde models/__init__.py después de crear 'db'.
    Construye y registra la clase ConfigSistema con el db real.
    """

    class ConfigSistema(db.Model):
        __tablename__ = 'config_sistema'

        id                    = db.Column(db.Integer, primary_key=True)
        _materias_json        = db.Column('materias_json', db.Text, default='[]')
        _modulos_json         = db.Column('modulos_json', db.Text, default='{}')
        mail_retiro_carro     = db.Column(db.Text, default='')
        mail_devolucion_carro = db.Column(db.Text, default='')
        mail_retiro_nb        = db.Column(db.Text, default='')
        mail_devolucion_nb    = db.Column(db.Text, default='')

        @classmethod
        def obtener(cls):
            cfg = cls.query.first()
            if not cfg:
                cfg = cls()
                db.session.add(cfg)
                db.session.commit()
            return cfg

        def get_materias(self):
            try:
                data = json.loads(self._materias_json or '[]')
                return data if isinstance(data, list) and data else []
            except Exception:
                return []

        def set_materias(self, lista):
            self._materias_json = json.dumps(lista, ensure_ascii=False)
            db.session.commit()

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

        def guardar(self):
            db.session.commit()

    # Reemplaza el placeholder en este módulo para que los imports posteriores
    # encuentren la clase real
    sys.modules[__name__].ConfigSistema = ConfigSistema
    return ConfigSistema


# ── Placeholder ───────────────────────────────────────────────────────────────
# Existe solo para que "from models.config_sistema import ConfigSistema"
# no falle en tiempo de importación. _init_model() lo reemplaza en runtime.
class ConfigSistema:
    """Placeholder reemplazado por _init_model(db)."""
    @classmethod
    def obtener(cls):
        raise RuntimeError('ConfigSistema no inicializada — llamar _init_model(db) primero.')
    @classmethod
    def query(cls):
        raise RuntimeError('ConfigSistema no inicializada.')
