# migrate_reclamo.py
# Ejecutar UNA SOLA VEZ desde la raíz del proyecto:
#   python migrate_reclamo.py

import sqlite3, os

DB_PATH = os.path.join('instance', 'sigartec.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("PRAGMA table_info(netbooks)")
    columnas = [row[1] for row in cur.fetchall()]

    if 'nro_reclamo' not in columnas:
        cur.execute("ALTER TABLE netbooks ADD COLUMN nro_reclamo VARCHAR(50)")
        print("✅ Columna 'nro_reclamo' agregada a 'netbooks'.")
    else:
        print("ℹ️  'nro_reclamo' ya existía.")

    conn.commit()
    conn.close()
    print("✅ Migración completada.")

if __name__ == '__main__':
    migrate()
