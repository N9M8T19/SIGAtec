"""
services/backup.py
Backup automático diario de la base de datos SQLite.
También expone una función para descarga manual.
"""

import os
import shutil
import threading
from datetime import datetime, timedelta
from flask import current_app, send_file
import time


BACKUP_DIR = 'backups'
MAX_BACKUPS = 30  # Máximo de backups a conservar (1 mes de diarios)


def _ruta_db():
    """Obtiene la ruta del archivo SQLite."""
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite:///'):
        # Ruta relativa a la app
        return os.path.join(current_app.root_path, uri.replace('sqlite:///', ''))
    elif uri.startswith('sqlite://'):
        return uri.replace('sqlite://', '')
    return None


def hacer_backup(app=None):
    """
    Crea una copia de la base SQLite con timestamp.
    Puede llamarse con contexto de app o pasando la app explícitamente.
    """
    ctx = app.app_context() if app else current_app._get_current_object().app_context()

    with ctx:
        db_path = _ruta_db()
        if not db_path or not os.path.exists(db_path):
            current_app.logger.warning('Backup: no se encontró la base SQLite.')
            return None

        os.makedirs(BACKUP_DIR, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre    = f'sigartec_backup_{timestamp}.db'
        destino   = os.path.join(BACKUP_DIR, nombre)

        shutil.copy2(db_path, destino)
        current_app.logger.info(f'Backup creado: {destino}')

        # Limpiar backups viejos
        _limpiar_backups_viejos()

        return destino


def _limpiar_backups_viejos():
    """Elimina backups más antiguos que MAX_BACKUPS."""
    if not os.path.exists(BACKUP_DIR):
        return
    archivos = sorted([
        os.path.join(BACKUP_DIR, f)
        for f in os.listdir(BACKUP_DIR)
        if f.startswith('sigartec_backup_') and f.endswith('.db')
    ])
    while len(archivos) > MAX_BACKUPS:
        os.remove(archivos.pop(0))


def descargar_backup_actual():
    """Crea un backup y retorna el response para descarga directa."""
    db_path = _ruta_db()
    if not db_path or not os.path.exists(db_path):
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre    = f'sigartec_backup_{timestamp}.db'
    destino   = os.path.join(BACKUP_DIR, nombre)
    shutil.copy2(db_path, destino)

    return send_file(
        destino,
        as_attachment=True,
        download_name=nombre,
        mimetype='application/octet-stream'
    )


def listar_backups():
    """Retorna lista de backups existentes con metadata."""
    if not os.path.exists(BACKUP_DIR):
        return []
    archivos = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.startswith('sigartec_backup_') and f.endswith('.db'):
            ruta  = os.path.join(BACKUP_DIR, f)
            size  = os.path.getsize(ruta)
            mtime = datetime.fromtimestamp(os.path.getmtime(ruta))
            archivos.append({
                'nombre': f,
                'ruta':   ruta,
                'size_kb': round(size / 1024, 1),
                'fecha':   mtime.strftime('%d/%m/%Y %H:%M'),
            })
    return archivos


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDULER SIMPLE — hilo de fondo que hace backup diario
# ─────────────────────────────────────────────────────────────────────────────

def iniciar_scheduler_backup(app):
    """
    Lanza un hilo de fondo que hace backup automático cada 24hs.
    Llamar desde create_app() después de crear la app.
    """
    def loop():
        # Esperar 60 segundos al arrancar para que la app esté lista
        time.sleep(60)
        while True:
            try:
                hacer_backup(app)
            except Exception as e:
                app.logger.error(f'Error en backup automático: {e}')
            # Dormir 24 horas
            time.sleep(60 * 60 * 24)

    hilo = threading.Thread(target=loop, daemon=True, name='backup-scheduler')
    hilo.start()
    app.logger.info('Scheduler de backup iniciado (cada 24hs).')
