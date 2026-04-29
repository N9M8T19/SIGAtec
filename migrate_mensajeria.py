"""
migrate_mensajeria.py
Crea las tablas mensajes y mensajes_leidos.
Ejecutar UNA sola vez desde la Shell de Render:
    python migrate_mensajeria.py
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no definida")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS mensajes (
    id          SERIAL PRIMARY KEY,
    canal       VARCHAR(50)  NOT NULL DEFAULT 'general',
    autor_id    INTEGER      REFERENCES usuarios(id) ON DELETE SET NULL,
    autor_nombre VARCHAR(200),
    autor_rol   VARCHAR(50),
    contenido   TEXT         NOT NULL,
    tipo        VARCHAR(30)  NOT NULL DEFAULT 'normal',
    creado_en   TIMESTAMP    NOT NULL DEFAULT NOW()
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS mensajes_leidos (
    id          SERIAL PRIMARY KEY,
    mensaje_id  INTEGER NOT NULL REFERENCES mensajes(id) ON DELETE CASCADE,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    leido_en    TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(mensaje_id, usuario_id)
);
""")

cur.execute("CREATE INDEX IF NOT EXISTS idx_mensajes_canal ON mensajes(canal);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_mensajes_creado ON mensajes(creado_en DESC);")

print("OK — tablas mensajes y mensajes_leidos creadas.")
cur.close()
conn.close()
