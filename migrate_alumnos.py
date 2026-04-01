# migrate_alumnos.py
# Ejecutar UNA SOLA VEZ desde la raíz del proyecto:
#   python migrate_alumnos.py

import sqlite3
import os

DB_PATH = os.path.join('instance', 'sigartec.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # 1. Crear tabla alumnos con columna turno
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alumnos (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            dni      VARCHAR(20)  NOT NULL UNIQUE,
            curso    VARCHAR(20)  NOT NULL,
            turno    VARCHAR(10)  NOT NULL DEFAULT 'M'
        )
    """)
    print("✅ Tabla 'alumnos' lista.")

    # 2. Verificar columnas actuales de netbooks
    cur.execute("PRAGMA table_info(netbooks)")
    columnas = [row[1] for row in cur.fetchall()]

    # 3. Agregar alumno_manana_id si no existe
    if 'alumno_manana_id' not in columnas:
        cur.execute("ALTER TABLE netbooks ADD COLUMN alumno_manana_id INTEGER REFERENCES alumnos(id)")
        print("✅ Columna 'alumno_manana_id' agregada.")
    else:
        print("ℹ️  'alumno_manana_id' ya existía.")

    # 4. Agregar alumno_tarde_id si no existe
    if 'alumno_tarde_id' not in columnas:
        cur.execute("ALTER TABLE netbooks ADD COLUMN alumno_tarde_id INTEGER REFERENCES alumnos(id)")
        print("✅ Columna 'alumno_tarde_id' agregada.")
    else:
        print("ℹ️  'alumno_tarde_id' ya existía.")

    # 5. Si existía alumno_id del paso anterior, migrar datos
    if 'alumno_id' in columnas:
        cur.execute("UPDATE netbooks SET alumno_manana_id = alumno_id WHERE alumno_id IS NOT NULL")
        print("✅ Datos migrados de 'alumno_id' a 'alumno_manana_id'.")

    # 6. Agregar columna turno a alumnos si no existe
    cur.execute("PRAGMA table_info(alumnos)")
    cols_alumnos = [row[1] for row in cur.fetchall()]
    if 'turno' not in cols_alumnos:
        cur.execute("ALTER TABLE alumnos ADD COLUMN turno VARCHAR(10) NOT NULL DEFAULT 'M'")
        print("✅ Columna 'turno' agregada a 'alumnos'.")
    else:
        print("ℹ️  'turno' ya existía en 'alumnos'.")

    conn.commit()
    conn.close()
    print("\n✅ Migración completada.")

if __name__ == '__main__':
    migrate()
