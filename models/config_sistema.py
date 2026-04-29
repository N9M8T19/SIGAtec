"""
models/config_sistema.py
Modelo para persistir la configuración editable del sistema:
- Lista de materias / cargos
- Horarios de módulos
- Templates de mail
"""

import json
from models import db


class ConfigSistema(db.Model):
    __tablename__ = 'config_sistema'

    id                    = db.Column(db.Integer, primary_key=True)
    # JSON con lista de materias/cargos
    _materias_json        = db.Column('materias_json', db.Text, default='[]')
    # JSON con dict de módulos {num: [inicio, fin, turno, codigo]}
    _modulos_json         = db.Column('modulos_json', db.Text, default='{}')
    # Templates de mail (texto plano con placeholders {docente}, {carro}, etc.)
    mail_retiro_carro     = db.Column(db.Text, default='')
    mail_devolucion_carro = db.Column(db.Text, default='')
    mail_retiro_nb        = db.Column(db.Text, default='')
    mail_devolucion_nb    = db.Column(db.Text, default='')

    @classmethod
    def obtener(cls):
        """Devuelve la única fila de config, la crea si no existe."""
        cfg = cls.query.first()
        if not cfg:
            cfg = cls()
            db.session.add(cfg)
            db.session.commit()
        return cfg

    # ── Materias ─────────────────────────────────────────────────────────────

    def get_materias(self):
        try:
            data = json.loads(self._materias_json or '[]')
            return data if isinstance(data, list) and data else []
        except Exception:
            return []

    def set_materias(self, lista):
        self._materias_json = json.dumps(lista, ensure_ascii=False)
        db.session.commit()

    # ── Módulos ───────────────────────────────────────────────────────────────

    def get_modulos(self):
        """Devuelve dict {int: (inicio, fin, turno, codigo)} o {} si vacío."""
        try:
            raw = json.loads(self._modulos_json or '{}')
            return {int(k): tuple(v) for k, v in raw.items()} if raw else {}
        except Exception:
            return {}

    def set_modulos(self, diccionario):
        """Recibe dict {int: (inicio, fin, turno, codigo)}."""
        serializable = {str(k): list(v) for k, v in diccionario.items()}
        self._modulos_json = json.dumps(serializable, ensure_ascii=False)
        db.session.commit()

    def guardar(self):
        db.session.commit()
