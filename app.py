from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, Usuario
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import os

load_dotenv()

# Zona horaria Argentina: UTC-3
ARG_TZ = timezone(timedelta(hours=-3))


def utc_a_arg(dt):
    """
    Convierte datetime a hora Argentina (UTC-3).
    Maneja naive (SQLite) y aware (PostgreSQL devuelve tzinfo=UTC).
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ARG_TZ)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Solo permitir OAuth sin HTTPS en desarrollo local
    if os.environ.get('FLASK_ENV') != 'production':
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    db.init_app(app)

    # ── Filtros Jinja2 para hora argentina ────────────────────────────────────
    @app.template_filter('arg_time')
    def arg_time_filter(dt):
        """Convierte UTC a hora argentina y formatea como HH:MM."""
        if dt is None:
            return '—'
        return utc_a_arg(dt).strftime('%H:%M')

    @app.template_filter('arg_datetime')
    def arg_datetime_filter(dt):
        """Convierte UTC a hora argentina y formatea como dd/mm/YYYY HH:MM."""
        if dt is None:
            return '—'
        return utc_a_arg(dt).strftime('%d/%m/%Y %H:%M')

    @app.template_filter('arg_date')
    def arg_date_filter(dt):
        """Convierte UTC a hora argentina y formatea como dd/mm."""
        if dt is None:
            return '—'
        return utc_a_arg(dt).strftime('%d/%m')

    # Hacer utc_a_arg disponible en templates
    app.jinja_env.globals['utc_a_arg'] = utc_a_arg

    from services.mail import init_mail
    init_mail(app)

    from routes.auth import google_bp
    app.register_blueprint(google_bp, url_prefix='/google_auth')

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view             = 'auth.login'
    login_manager.login_message          = 'Debes iniciar sesion para acceder.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from routes.auth           import auth_bp
    from routes.carros         import carros_bp
    from routes.netbooks       import netbooks_bp
    from routes.prestamos      import prestamos_bp
    from routes.docentes       import docentes_bp
    from routes.usuarios       import usuarios_bp
    from routes.reportes       import reportes_bp
    from routes.main           import main_bp
    from routes.horarios       import horarios_bp
    from routes.notificaciones import notificaciones_bp
    from routes.pantallas      import pantallas_bp
    from routes.importar       import importar_bp
    from routes.transferencias import transferencias_bp
    from routes.stock          import stock_bp
    from routes.tickets_ba     import tickets_ba_bp
    from routes.alumnos        import alumnos_bp
    from routes.etiquetas      import etiquetas_bp
    from routes.impresoras3d   import impresoras3d_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(carros_bp)
    app.register_blueprint(netbooks_bp)
    app.register_blueprint(prestamos_bp)
    app.register_blueprint(docentes_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(horarios_bp)
    app.register_blueprint(notificaciones_bp)
    app.register_blueprint(pantallas_bp)
    app.register_blueprint(importar_bp)
    app.register_blueprint(transferencias_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(tickets_ba_bp)
    app.register_blueprint(alumnos_bp)
    app.register_blueprint(etiquetas_bp)
    app.register_blueprint(impresoras3d_bp)

    with app.app_context():
        import models_extra.horarios_notificaciones  # noqa
        db.create_all()
        _crear_admin_inicial()

    from services.backup import iniciar_scheduler_backup
    from services.alertas_horario import iniciar_scheduler_alertas
    iniciar_scheduler_backup(app)
    iniciar_scheduler_alertas(app)

    return app


def _crear_admin_inicial():
    admin = Usuario.query.filter_by(dni='41469656').first()
    if not admin:
        admin = Usuario(
            dni      = '41469656',
            nombre   = 'Nicolás',
            apellido = 'Montefinal Turnes',
            username = 'admin',
            rol      = 'Administrador',
            activo   = True,
            correo   = 'nicolas.montefinal@bue.edu.ar'
        )
        db.session.add(admin)
        db.session.commit()
        print("Usuario administrador creado.")
    else:
        if not admin.correo:
            admin.correo = 'nicolas.montefinal@bue.edu.ar'
        db.session.commit()
        print("Usuario administrador verificado.")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
