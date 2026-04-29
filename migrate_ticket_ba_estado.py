"""
migrate_ticket_ba_estado.py
Agrega columnas de cierre a la tabla tickets_ba:
  - estado          VARCHAR(20)   DEFAULT 'activo'
  - fecha_cierre    TIMESTAMP
  - motivo_cierre   TEXT
  - cerrado_por     VARCHAR(200)

Ejecutar UNA sola vez desde la Shell de Render:
    python migrate_ticket_ba_estado.py
"""
import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

columnas = [
    ("estado",        "VARCHAR(20)  DEFAULT 'activo'"),
    ("fecha_cierre",  "TIMESTAMP"),
    ("motivo_cierre", "TEXT"),
    ("cerrado_por",   "VARCHAR(200)"),
]

for nombre, tipo in columnas:
    try:
        cur.execute(
            f"ALTER TABLE tickets_ba ADD COLUMN IF NOT EXISTS {nombre} {tipo};"
        )
        print(f"  ✓ columna '{nombre}' agregada (o ya existía)")
    except Exception as e:
        print(f"  ✗ error en columna '{nombre}': {e}")

# Marcar todos los tickets existentes como 'activo'
cur.execute("UPDATE tickets_ba SET estado = 'activo' WHERE estado IS NULL;")
print(f"  ✓ tickets existentes marcados como 'activo'")

cur.close()
conn.close()
print("\nMigración completada.")
