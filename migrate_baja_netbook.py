# migrate_baja_netbook.py
# Ejecutar UNA SOLA VEZ desde la raíz del proyecto:
#   python migrate_baja_netbook.py

import sqlite3, os

DB_PATH = os.path.join('instance', 'sigartec.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("PRAGMA table_info(netbooks)")
    columnas = [row[1] for row in cur.fetchall()]

    for col, tipo in [('motivo_baja', 'TEXT'),
                      ('fecha_baja',  'DATETIME'),
                      ('usuario_baja','VARCHAR(200)')]:
        if col not in columnas:
            cur.execute(f"ALTER TABLE netbooks ADD COLUMN {col} {tipo}")
            print(f"✅ Columna '{col}' agregada.")
        else:
            print(f"ℹ️  '{col}' ya existía.")

    conn.commit()
    conn.close()
    print("\n✅ Migración completada.")

if __name__ == '__main__':
    migrate()
