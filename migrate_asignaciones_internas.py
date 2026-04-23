"""
migrate_asignaciones_internas.py
Crea la tabla `asignaciones_internas` si no existe.
Ejecutar: python migrate_asignaciones_internas.py
"""

from app import create_app
from models import db

def migrar():
    app = create_app()
    with app.app_context():
        sql = """
        CREATE TABLE IF NOT EXISTS asignaciones_internas (
            id               SERIAL PRIMARY KEY,
            netbook_id       INTEGER NOT NULL REFERENCES netbooks(id),
            docente_id       INTEGER REFERENCES docentes(id),
            area             VARCHAR(200),
            fecha_asignacion TIMESTAMP DEFAULT NOW(),
            motivo           TEXT,
            activa           BOOLEAN DEFAULT TRUE,
            fecha_baja       TIMESTAMP,
            motivo_baja      TEXT,
            registrado_por   VARCHAR(200)
        );
        """
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text(sql))
                conn.commit()
            print("✅ Tabla 'asignaciones_internas' creada correctamente.")
        except Exception as e:
            print(f"⚠️  {e}")
            print("   Si el error es 'already exists', la migración ya fue ejecutada. Es seguro ignorarlo.")

if __name__ == '__main__':
    migrar()
