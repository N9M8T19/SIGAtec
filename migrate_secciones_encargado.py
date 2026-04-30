"""
migrate_secciones_encargado.py
Agrega la columna secciones_encargado_json a la tabla config_sistema.
Ejecutar una sola vez desde la Shell de Render:
    python migrate_secciones_encargado.py
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    ALTER TABLE config_sistema
    ADD COLUMN IF NOT EXISTS secciones_encargado_json TEXT DEFAULT '[]';
""")

print("OK — columna secciones_encargado_json agregada (o ya existía).")
cur.close()
conn.close()
