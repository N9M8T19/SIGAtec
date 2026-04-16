"""
models/sesion.py
Modelo para el registro de sesiones de encargados.
"""

from datetime import datetime
from models import db


class SesionEncargado(db.Model):
    __tablename__ = 'sesiones_encargados'

    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    ip          = db.Column(db.String(45))          # IPv4 o IPv6
    user_agent  = db.Column(db.String(300))
    inicio      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fin         = db.Column(db.DateTime, nullable=True)
    activa      = db.Column(db.Boolean, default=True, nullable=False)
    cerrada_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    # Relaciones
    usuario     = db.relationship('Usuario', foreign_keys=[usuario_id], backref='sesiones')
    admin       = db.relationship('Usuario', foreign_keys=[cerrada_por])

    def __repr__(self):
        return f'<SesionEncargado {self.id} usuario={self.usuario_id} activa={self.activa}>'
