"""
migrate_tvs.py
Crea las tablas: tvs, prestamos_tvs, ubicaciones_equipos.
Usar psycopg2 directo (igual que migrate_asignaciones_internas.py).

Ejecutar UNA sola vez:
    python migrate_tvs.py

En Render — Shell del servicio:
    python migrate_tvs.py
"""

import os
import psycopg2

def run():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    cur = conn.cursor()

    # ── TVs ──────────────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tvs (
        id                     SERIAL PRIMARY KEY,
        numero_interno         INTEGER NOT NULL UNIQUE,
        marca                  VARCHAR(80)  NOT NULL,
        modelo                 VARCHAR(120) NOT NULL,
        numero_serie           VARCHAR(120) UNIQUE,
        pulgadas               INTEGER,
        aula                   VARCHAR(60),
        estado                 VARCHAR(30)  NOT NULL DEFAULT 'disponible',
        motivo_servicio        VARCHAR(200),
        fecha_servicio         TIMESTAMP,
        observaciones          TEXT,
        fecha_alta             TIMESTAMP DEFAULT NOW(),
        tiene_control_remoto   BOOLEAN DEFAULT FALSE,
        tiene_cable_hdmi       BOOLEAN DEFAULT FALSE,
        tiene_cable_vga        BOOLEAN DEFAULT FALSE,
        tiene_cable_corriente  BOOLEAN DEFAULT FALSE,
        tiene_soporte_pared    BOOLEAN DEFAULT FALSE,
        tiene_soporte_pie      BOOLEAN DEFAULT FALSE,
        tiene_chromecast       BOOLEAN DEFAULT FALSE,
        tiene_adaptador_hdmi   BOOLEAN DEFAULT FALSE,
        componentes_extra      VARCHAR(300)
    );
    """)
    print("✅ Tabla tvs OK")

    # ── Préstamos de TVs ──────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prestamos_tvs (
        id                          SERIAL PRIMARY KEY,
        tv_id                       INTEGER NOT NULL REFERENCES tvs(id),
        docente_id                  INTEGER REFERENCES docentes(id),
        nombre_solicitante          VARCHAR(120),
        aula_destino                VARCHAR(60),
        motivo                      VARCHAR(200),
        fecha_retiro                TIMESTAMP NOT NULL DEFAULT NOW(),
        fecha_devolucion_esperada   TIMESTAMP,
        fecha_devolucion_real       TIMESTAMP,
        encargado_retiro_id         INTEGER REFERENCES usuarios(id),
        encargado_devolucion_id     INTEGER REFERENCES usuarios(id),
        devuelto_control_remoto     BOOLEAN DEFAULT FALSE,
        devuelto_cable_hdmi         BOOLEAN DEFAULT FALSE,
        devuelto_cable_vga          BOOLEAN DEFAULT FALSE,
        devuelto_cable_corriente    BOOLEAN DEFAULT FALSE,
        devuelto_soporte_pared      BOOLEAN DEFAULT FALSE,
        devuelto_soporte_pie        BOOLEAN DEFAULT FALSE,
        devuelto_chromecast         BOOLEAN DEFAULT FALSE,
        devuelto_adaptador_hdmi     BOOLEAN DEFAULT FALSE,
        estado                      VARCHAR(20) NOT NULL DEFAULT 'activo',
        observaciones               TEXT
    );
    """)
    print("✅ Tabla prestamos_tvs OK")

    # ── Ubicaciones de equipos fijos ──────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ubicaciones_equipos (
        id                SERIAL PRIMARY KEY,
        tipo_equipo       VARCHAR(40)  NOT NULL,
        equipo_id         INTEGER      NOT NULL,
        aula              VARCHAR(60)  NOT NULL,
        sector            VARCHAR(100),
        piso              VARCHAR(20),
        descripcion       VARCHAR(200),
        fecha_asignacion  TIMESTAMP    DEFAULT NOW(),
        activa            BOOLEAN      DEFAULT TRUE,
        registrado_por_id INTEGER      REFERENCES usuarios(id)
    );
    """)
    print("✅ Tabla ubicaciones_equipos OK")

    cur.close()
    conn.close()
    print("\n🎉 Migración completada.")

if __name__ == '__main__':
    run()
