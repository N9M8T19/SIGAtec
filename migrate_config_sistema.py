"""
migrate_config_sistema.py
Crea la tabla config_sistema si no existe.
Ejecutar una sola vez:  python migrate_config_sistema.py
"""

import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL', '')

if not DATABASE_URL:
    # Local SQLite — usar SQLAlchemy directamente
    from app import create_app
    from models import db

    app = create_app()
    with app.app_context():
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS config_sistema (
                id                    SERIAL PRIMARY KEY,
                materias_json         TEXT    DEFAULT '[]',
                modulos_json          TEXT    DEFAULT '{}',
                mail_retiro_carro     TEXT    DEFAULT '',
                mail_devolucion_carro TEXT    DEFAULT '',
                mail_retiro_nb        TEXT    DEFAULT '',
                mail_devolucion_nb    TEXT    DEFAULT ''
            );
        """)
        print("Tabla config_sistema creada (SQLite).")
else:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS config_sistema (
            id                    SERIAL PRIMARY KEY,
            materias_json         TEXT    DEFAULT '[]',
            modulos_json          TEXT    DEFAULT '{}',
            mail_retiro_carro     TEXT    DEFAULT '',
            mail_devolucion_carro TEXT    DEFAULT '',
            mail_retiro_nb        TEXT    DEFAULT '',
            mail_devolucion_nb    TEXT    DEFAULT ''
        );
    """)
    print("Tabla config_sistema creada (PostgreSQL).")
    cur.close()
    conn.close()
