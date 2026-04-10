"""
migrate_impresoras3d.py
Agrega la tabla impresoras_3d a la base de datos.
Ejecutar una sola vez: python migrate_impresoras3d.py
"""

from app import create_app
from models import db

app = create_app()

with app.app_context():
    with db.engine.connect() as con:
        # Verificar si la tabla ya existe
        resultado = con.execute(db.text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'impresoras_3d'
        """))
        if resultado.fetchone():
            print("La tabla impresoras_3d ya existe.")
        else:
            con.execute(db.text("""
                CREATE TABLE impresoras_3d (
                    id          SERIAL PRIMARY KEY,
                    numero_interno VARCHAR(20) NOT NULL UNIQUE,
                    numero_serie   VARCHAR(100),
                    modelo         VARCHAR(100) NOT NULL,
                    aula           VARCHAR(50),
                    estado         VARCHAR(20) NOT NULL DEFAULT 'operativa',
                    observaciones  TEXT,
                    fecha_alta     TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """))
            print("Tabla impresoras_3d creada correctamente.")
