"""
services/backup.py
Backup de la base de datos — compatible con SQLite (local) y PostgreSQL (Render).
"""

import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from flask import current_app, send_file


BACKUP_DIR = 'backups'
MAX_BACKUPS = 30


# ─────────────────────────────────────────────────────────────────────────────
#  DETECCIÓN DE BASE DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def _es_sqlite():
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    return uri.startswith('sqlite')


def _ruta_db_sqlite():
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite:///'):
        return os.path.join(current_app.root_path, uri.replace('sqlite:///', ''))
    elif uri.startswith('sqlite://'):
        return uri.replace('sqlite://', '')
    return None


def _database_url_postgres():
    return current_app.config.get('SQLALCHEMY_DATABASE_URI', '')


# ─────────────────────────────────────────────────────────────────────────────
#  BACKUP SQLITE
# ─────────────────────────────────────────────────────────────────────────────

def _backup_sqlite(destino_sin_ext):
    db_path = _ruta_db_sqlite()
    if not db_path or not os.path.exists(db_path):
        current_app.logger.warning('Backup SQLite: no se encontró el archivo .db')
        return None
    destino = destino_sin_ext + '.db'
    shutil.copy2(db_path, destino)
    return destino


# ─────────────────────────────────────────────────────────────────────────────
#  BACKUP POSTGRESQL con pg_dump
# ─────────────────────────────────────────────────────────────────────────────

def _backup_postgres(destino_sin_ext):
    database_url = _database_url_postgres()
    destino = destino_sin_ext + '.sql'

    try:
        result = subprocess.run(
            ['pg_dump', '--no-password', '--format=plain', database_url],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            current_app.logger.error(f'pg_dump error: {result.stderr}')
            return None

        with open(destino, 'w', encoding='utf-8') as f:
            f.write(result.stdout)

        return destino

    except FileNotFoundError:
        # pg_dump no está instalado en Render — usar método alternativo con psycopg2
        current_app.logger.warning('pg_dump no disponible, usando exportación por psycopg2')
        return _backup_postgres_psycopg2(destino_sin_ext)

    except subprocess.TimeoutExpired:
        current_app.logger.error('Backup PostgreSQL: timeout al ejecutar pg_dump')
        return None


def _backup_postgres_psycopg2(destino_sin_ext):
    """
    Alternativa a pg_dump usando psycopg2 directamente.
    Exporta todas las tablas como INSERT INTO en un archivo .sql
    """
    try:
        import psycopg2
    except ImportError:
        current_app.logger.error('psycopg2 no disponible para backup')
        return None

    database_url = _database_url_postgres()
    destino = destino_sin_ext + '.sql'

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Obtener todas las tablas del esquema público
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tablas = [row[0] for row in cursor.fetchall()]

        with open(destino, 'w', encoding='utf-8') as f:
            f.write(f'-- Backup SIGA-Tec — {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n')
            f.write(f'-- Base de datos: PostgreSQL\n')
            f.write(f'-- Tablas: {", ".join(tablas)}\n\n')

            for tabla in tablas:
                f.write(f'\n-- ═══════════════════════════════\n')
                f.write(f'-- Tabla: {tabla}\n')
                f.write(f'-- ═══════════════════════════════\n\n')

                # Obtener columnas
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """, (tabla,))
                columnas = [row[0] for row in cursor.fetchall()]

                # Obtener datos
                cursor.execute(f'SELECT * FROM "{tabla}";')
                filas = cursor.fetchall()

                if not filas:
                    f.write(f'-- (sin datos)\n')
                    continue

                cols_str = ', '.join(f'"{c}"' for c in columnas)

                for fila in filas:
                    valores = []
                    for v in fila:
                        if v is None:
                            valores.append('NULL')
                        elif isinstance(v, bool):
                            valores.append('TRUE' if v else 'FALSE')
                        elif isinstance(v, (int, float)):
                            valores.append(str(v))
                        else:
                            # Escapar comillas simples
                            v_str = str(v).replace("'", "''")
                            valores.append(f"'{v_str}'")
                    vals_str = ', '.join(valores)
                    f.write(f'INSERT INTO "{tabla}" ({cols_str}) VALUES ({vals_str});\n')

        cursor.close()
        conn.close()
        current_app.logger.info(f'Backup PostgreSQL creado con psycopg2: {destino}')
        return destino

    except Exception as e:
        current_app.logger.error(f'Error en backup psycopg2: {e}')
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  FUNCIONES PÚBLICAS
# ─────────────────────────────────────────────────────────────────────────────

def hacer_backup(app=None):
    """
    Crea un backup con timestamp.
    Detecta automáticamente si es SQLite o PostgreSQL.
    """
    ctx = app.app_context() if app else current_app._get_current_object().app_context()

    with ctx:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp     = datetime.now().strftime('%Y%m%d_%H%M%S')
        destino_base  = os.path.join(BACKUP_DIR, f'sigartec_backup_{timestamp}')

        if _es_sqlite():
            resultado = _backup_sqlite(destino_base)
        else:
            resultado = _backup_postgres(destino_base)

        if resultado:
            current_app.logger.info(f'Backup creado: {resultado}')
            _limpiar_backups_viejos()
        else:
            current_app.logger.warning('No se pudo crear el backup.')

        return resultado


def descargar_backup_actual():
    """
    Crea un backup y retorna el response para descarga directa.
    Retorna None si falló.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp    = datetime.now().strftime('%Y%m%d_%H%M%S')
    destino_base = os.path.join(BACKUP_DIR, f'sigartec_backup_{timestamp}')

    if _es_sqlite():
        ruta = _backup_sqlite(destino_base)
        mimetype = 'application/octet-stream'
    else:
        ruta = _backup_postgres(destino_base)
        mimetype = 'text/plain'

    if not ruta or not os.path.exists(ruta):
        return None

    return send_file(
        ruta,
        as_attachment=True,
        download_name=os.path.basename(ruta),
        mimetype=mimetype
    )


def listar_backups():
    """Retorna lista de backups existentes con metadata."""
    if not os.path.exists(BACKUP_DIR):
        return []
    archivos = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.startswith('sigartec_backup_') and (f.endswith('.db') or f.endswith('.sql')):
            ruta  = os.path.join(BACKUP_DIR, f)
            size  = os.path.getsize(ruta)
            mtime = datetime.fromtimestamp(os.path.getmtime(ruta))
            archivos.append({
                'nombre':  f,
                'ruta':    ruta,
                'size_kb': round(size / 1024, 1),
                'fecha':   mtime.strftime('%d/%m/%Y %H:%M'),
                'tipo':    'PostgreSQL' if f.endswith('.sql') else 'SQLite',
            })
    return archivos


def _limpiar_backups_viejos():
    """Elimina backups más antiguos si superan MAX_BACKUPS."""
    if not os.path.exists(BACKUP_DIR):
        return
    archivos = sorted([
        os.path.join(BACKUP_DIR, f)
        for f in os.listdir(BACKUP_DIR)
        if f.startswith('sigartec_backup_')
    ])
    while len(archivos) > MAX_BACKUPS:
        os.remove(archivos.pop(0))


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDULER — backup automático cada 24hs
# ─────────────────────────────────────────────────────────────────────────────

def iniciar_scheduler_backup(app):
    """
    Lanza un hilo de fondo que hace backup automático cada 24hs.
    Llamar desde create_app() después de inicializar la app.
    """
    def loop():
        time.sleep(60)  # Esperar que la app esté lista
        while True:
            try:
                hacer_backup(app)
            except Exception as e:
                app.logger.error(f'Error en backup automático: {e}')
            time.sleep(60 * 60 * 24)  # 24 horas

    hilo = threading.Thread(target=loop, daemon=True, name='backup-scheduler')
    hilo.start()
    app.logger.info('Scheduler de backup iniciado (cada 24hs).')
