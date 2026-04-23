"""
migrate_asignaciones_internas.py — versión directa con psycopg2
"""
import os
from dotenv import load_dotenv
load_dotenv()

import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL', '')

def migrar():
    if not DATABASE_URL:
        print("❌ No se encontró DATABASE_URL en las variables de entorno.")
        return

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    sql = """
    CREATE TABLE IF NOT EXISTS asignaciones_internas (
        id               SERIAL PRIMARY KEY,
        netbook_id       INTEGER NOT NULL REFERENCES netbooks(id),
        docente_id       INTEGER REFERENCES docentes(id),
        area             VARCHAR(200),
        fecha_asignacion TIMESTAMP DEFAULT NOW(),
        motivo           TEXT,
        activa           BOOLEAN DEFAULT TRUE,
        fecha_baja       TIMESTAMP,
        motivo_baja      TEXT,
        registrado_por   VARCHAR(200)
    );
    """

    try:
        cur.execute(sql)
        print("✅ Tabla 'asignaciones_internas' creada correctamente.")
    except Exception as e:
        print(f"⚠️  {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    migrar()
