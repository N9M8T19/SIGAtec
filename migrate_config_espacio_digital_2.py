"""
Migración: agrega columna carro_id_2 a la tabla config_espacio_digital
Ejecutar una sola vez: python migrate_config_espacio_digital_2.py
"""
from models import db
from app import create_app

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(db.text(
                "ALTER TABLE config_espacio_digital "
                "ADD COLUMN carro_id_2 INTEGER REFERENCES carros(id)"
            ))
            conn.commit()
            print("✅ OK: columna carro_id_2 agregada a config_espacio_digital")
        except Exception as e:
            msg = str(e).lower()
            if 'already exists' in msg or 'duplicate column' in msg:
                print("ℹ️  La columna carro_id_2 ya existe — migracion omitida")
            else:
                print(f"❌ Error inesperado: {e}")
                raise
