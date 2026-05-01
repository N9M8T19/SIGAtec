"""
migrate_mail_tv.py
Agrega las columnas mail_retiro_tv y mail_devolucion_tv a la tabla config_sistema.

Ejecutar UNA sola vez desde la Shell de Render:
    python migrate_mail_tv.py
"""

import os
import psycopg2

def run():
    url = os.environ['DATABASE_URL']
    # Render usa postgres://, psycopg2 necesita postgresql://
    url = url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        ALTER TABLE config_sistema
            ADD COLUMN IF NOT EXISTS mail_retiro_tv    TEXT DEFAULT '',
            ADD COLUMN IF NOT EXISTS mail_devolucion_tv TEXT DEFAULT '';
    """)
    print("✅ Columnas mail_retiro_tv y mail_devolucion_tv agregadas a config_sistema.")

    cur.close()
    conn.close()
    print("🎉 Migración completada.")

if __name__ == '__main__':
    run()
