# migrate_netbook_alumno.py
# Agrega netbook_id a la tabla alumnos para registrar alumnos sin netbook disponible.
# Funciona tanto en SQLite (local) como en PostgreSQL (Render).
#
# Ejecutar UNA SOLA VEZ:
#   python migrate_netbook_alumno.py

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db

def migrate():
    app = create_app()
    with app.app_context():
        con = db.engine.connect()

        # Detectar motor
        es_postgres = 'postgresql' in str(db.engine.url)

        if es_postgres:
            # PostgreSQL
            resultado = con.execute(db.text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='alumnos' AND column_name='netbook_id'
            """))
            existe = resultado.fetchone() is not None
        else:
            # SQLite
            resultado = con.execute(db.text("PRAGMA table_info(alumnos)"))
            columnas  = [row[1] for row in resultado.fetchall()]
            existe    = 'netbook_id' in columnas

        if existe:
            print("ℹ️  'netbook_id' ya existe en 'alumnos'. No se hicieron cambios.")
        else:
            con.execute(db.text(
                "ALTER TABLE alumnos ADD COLUMN netbook_id INTEGER REFERENCES netbooks(id)"
            ))
            con.commit()
            print("✅ Columna 'netbook_id' agregada a 'alumnos'.")

        con.close()
        print("✅ Migración completada.")

if __name__ == '__main__':
    migrate()
