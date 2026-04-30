"""
migrate_cargo_docente.py
Agrega la columna `cargo` (VARCHAR 150, nullable) a la tabla `docentes`.
Ejecutar una sola vez desde la Shell de Render:
    python migrate_cargo_docente.py
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('Variable de entorno DATABASE_URL no definida.')

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    ALTER TABLE docentes
    ADD COLUMN IF NOT EXISTS cargo VARCHAR(150);
""")

print("✅ Columna 'cargo' agregada a la tabla 'docentes' (o ya existía).")

cur.close()
conn.close()
