"""
migrate_obsolescencia.py
Crea la tabla obsolescencias en PostgreSQL (psycopg2 directo).
Ejecutar desde la Shell de Render:
    python migrate_obsolescencia.py
"""

import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está configurada")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Tabla principal de obsolescencias
cur.execute("""
    CREATE TABLE IF NOT EXISTS obsolescencias (
        id               SERIAL PRIMARY KEY,
        netbook_id       INTEGER NOT NULL REFERENCES netbooks(id),
        motivo           VARCHAR(100) NOT NULL,
        observaciones    TEXT,
        fecha_baja       TIMESTAMP NOT NULL DEFAULT NOW(),
        registrado_por   INTEGER REFERENCES usuarios(id),

        -- Datos del reemplazo (puede llegar después)
        tiene_reemplazo  BOOLEAN NOT NULL DEFAULT FALSE,
        reemplazo_serie  VARCHAR(100),
        reemplazo_modelo VARCHAR(200),
        reemplazo_carro_id INTEGER REFERENCES carros(id),
        reemplazo_pendiente BOOLEAN NOT NULL DEFAULT FALSE,
        fecha_reemplazo  TIMESTAMP,
        reemplazo_registrado_por INTEGER REFERENCES usuarios(id)
    );
""")
print("Tabla 'obsolescencias' creada (o ya existía).")

cur.close()
conn.close()
print("Migración completada.")
