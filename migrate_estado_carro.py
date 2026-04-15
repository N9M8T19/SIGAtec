"""
migrate_estado_carro.py
Adapta la tabla carros para soportar servicio técnico del carro físico.

- Renombra 'problema' a 'motivo_servicio' (si existe)
- Renombra 'fecha_reparacion' a 'fecha_servicio' (si existe)
- Actualiza los valores de 'estado': 'activo' → 'operativo'

Ejecutar UNA SOLA VEZ:
    python migrate_estado_carro.py
"""

from app import create_app
from models import db

app = create_app()

with app.app_context():
    with db.engine.connect() as con:

        # 1. Renombrar 'problema' → 'motivo_servicio' si existe
        res = con.execute(db.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='carros' AND column_name='problema'"
        ))
        if res.fetchone():
            con.execute(db.text(
                "ALTER TABLE carros RENAME COLUMN problema TO motivo_servicio"
            ))
            print("OK: 'problema' renombrada a 'motivo_servicio'")
        else:
            res2 = con.execute(db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='carros' AND column_name='motivo_servicio'"
            ))
            if not res2.fetchone():
                con.execute(db.text(
                    "ALTER TABLE carros ADD COLUMN motivo_servicio VARCHAR(200)"
                ))
                print("OK: columna 'motivo_servicio' agregada")
            else:
                print("INFO: 'motivo_servicio' ya existe")

        # 2. Renombrar 'fecha_reparacion' → 'fecha_servicio' si existe
        res = con.execute(db.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='carros' AND column_name='fecha_reparacion'"
        ))
        if res.fetchone():
            con.execute(db.text(
                "ALTER TABLE carros RENAME COLUMN fecha_reparacion TO fecha_servicio"
            ))
            print("OK: 'fecha_reparacion' renombrada a 'fecha_servicio'")
        else:
            res2 = con.execute(db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='carros' AND column_name='fecha_servicio'"
            ))
            if not res2.fetchone():
                con.execute(db.text(
                    "ALTER TABLE carros ADD COLUMN fecha_servicio TIMESTAMP"
                ))
                print("OK: columna 'fecha_servicio' agregada")
            else:
                print("INFO: 'fecha_servicio' ya existe")

        # 3. Normalizar estado: 'activo' → 'operativo'
        res = con.execute(db.text(
            "SELECT COUNT(*) FROM carros WHERE estado = 'activo'"
        ))
        count = res.fetchone()[0]
        if count > 0:
            con.execute(db.text(
                "UPDATE carros SET estado = 'operativo' WHERE estado = 'activo'"
            ))
            print(f"OK: {count} carro(s) actualizados de 'activo' a 'operativo'")
        else:
            print("INFO: no hay carros con estado 'activo'")

        con.execute(db.text("COMMIT"))

    print("\nMigracion completada.")
