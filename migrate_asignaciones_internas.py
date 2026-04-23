"""
migrate_asignaciones_internas.py — tabla sin FK a netbooks (campo libre)
"""
import os, psycopg2
from dotenv import load_dotenv
load_dotenv()

def migrar():
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if not DATABASE_URL:
        print("❌ No se encontró DATABASE_URL.")
        return

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # Eliminar tabla vieja si existe (puede tener FK incorrecta)
    cur.execute("DROP TABLE IF EXISTS asignaciones_internas;")
    print("🗑  Tabla anterior eliminada (si existía).")

    cur.execute("""
    CREATE TABLE asignaciones_internas (
        id               SERIAL PRIMARY KEY,
        numero_serie     VARCHAR(200),
        numero_interno   VARCHAR(50),
        modelo           VARCHAR(200),
        docente_id       INTEGER REFERENCES docentes(id),
        area             VARCHAR(200),
        fecha_asignacion TIMESTAMP DEFAULT NOW(),
        motivo           TEXT,
        activa           BOOLEAN DEFAULT TRUE,
        fecha_baja       TIMESTAMP,
        motivo_baja      TEXT,
        registrado_por   VARCHAR(200)
    );
    """)
    print("✅ Tabla 'asignaciones_internas' creada correctamente.")
    cur.close()
    conn.close()

if __name__ == '__main__':
    migrar()
