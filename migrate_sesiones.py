"""
migrate_sesiones.py
Crea la tabla `sesiones_encargados` para registrar inicios de sesión.
Ejecutar una sola vez: python migrate_sesiones.py
"""

from app import create_app
from models import db
import sqlalchemy as sa

def migrate():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            # ── Verificar si la tabla ya existe ──────────────────────────────
            inspector = sa.inspect(db.engine)
            if 'sesiones_encargados' in inspector.get_table_names():
                print("✓ La tabla 'sesiones_encargados' ya existe — nada que hacer.")
                return

            conn.execute(sa.text("""
                CREATE TABLE sesiones_encargados (
                    id          SERIAL PRIMARY KEY,
                    usuario_id  INTEGER NOT NULL
                                REFERENCES usuarios(id) ON DELETE CASCADE,
                    ip          VARCHAR(45),
                    user_agent  VARCHAR(300),
                    inicio      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    fin         TIMESTAMP,
                    activa      BOOLEAN NOT NULL DEFAULT TRUE,
                    cerrada_por INTEGER REFERENCES usuarios(id)
                )
            """))
            conn.commit()
            print("✓ Tabla 'sesiones_encargados' creada correctamente.")

if __name__ == '__main__':
    migrate()
