import os

class Config:
    SECRET_KEY          = os.environ.get('SECRET_KEY') or 'sigartec-clave-secreta-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///sigartec.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_NOMBRE          = 'SIGA-Tec'
    APP_ESCUELA         = 'E.T. N°7 D.E. 5'
    APP_ESCUELA_NOMBRE  = 'Dolores Lavalle de Lavalle'
    MINUTOS_ALERTA_PRESTAMO = 120
