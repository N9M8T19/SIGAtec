"""
migrate_ticket_ba_carro.py
Agrega la columna carro_id a la tabla tickets_ba_netbooks.
Ejecutar UNA SOLA VEZ: python migrate_ticket_ba_carro.py
"""
from app import create_app
from models import db

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(db.text(
                "ALTER TABLE tickets_ba_netbooks ADD COLUMN carro_id INTEGER REFERENCES carros(id)"
            ))
            # Para SQLite (local) el COMMIT es automático en DDL.
            # Para PostgreSQL también, pero por las dudas:
            try:
                conn.execute(db.text("COMMIT"))
            except Exception:
                pass
            print("✅ Columna carro_id agregada correctamente.")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                print("ℹ️  La columna carro_id ya existe — no se requiere acción.")
            else:
                print(f"❌ Error: {e}")
