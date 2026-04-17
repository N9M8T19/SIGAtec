import os

class Config:
    SECRET_KEY          = os.environ.get('SECRET_KEY') or 'sigartec-clave-secreta-2024'

    # Render genera URLs con prefijo 'postgres://' pero SQLAlchemy requiere 'postgresql://'
    _database_url = os.environ.get('DATABASE_URL') or 'sqlite:///sigartec.db'
    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _database_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,      # verifica la conexión antes de usarla
        'pool_recycle':  280,       # recicla conexiones cada 280 seg (< timeout de Render)
    }
    APP_NOMBRE          = 'SIGA-Tec'
    APP_ESCUELA         = 'E.T. N°7 D.E. 5'
    APP_ESCUELA_NOMBRE  = 'Dolores Lavalle de Lavalle'
    MINUTOS_ALERTA_PRESTAMO = 260

    # ── Configuración de Mail (Gmail) ─────────────────────────────────────────
    # Completar con los datos reales o setear como variables de entorno
    MAIL_SERVER         = 'smtp.gmail.com'
    MAIL_PORT           = 587
    MAIL_USE_TLS        = True
    MAIL_USE_SSL        = False
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME') or ''      # ej: escuela@gmail.com
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD') or ''      # Contraseña de aplicación Google
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'SIGA-Tec <escuela@gmail.com>'
