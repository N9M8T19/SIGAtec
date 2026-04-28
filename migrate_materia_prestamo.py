"""
migrate_materia_prestamo.py
Agrega la columna materia_prestamo a la tabla prestamos_carros.
Ejecutar UNA sola vez desde la Shell de Render:
    python migrate_materia_prestamo.py
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('Variable DATABASE_URL no encontrada.')

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    ALTER TABLE prestamos_carros
    ADD COLUMN IF NOT EXISTS materia_prestamo VARCHAR(200);
""")

print("OK — columna materia_prestamo agregada a prestamos_carros.")
cur.close()
conn.close()
