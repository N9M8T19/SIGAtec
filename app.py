from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, Usuario
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)

    # ── Mail ──────────────────────────────────────────────────────────────────
    from services.mail import init_mail
    init_mail(app)

    # ── Login ─────────────────────────────────────────────────────────────────
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view     = 'auth.login'
    login_manager.login_message  = 'Debes iniciar sesion para acceder.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # ── Blueprints ────────────────────────────────────────────────────────────
    from routes.auth          import auth_bp
    from routes.carros        import carros_bp
    from routes.netbooks      import netbooks_bp
    from routes.prestamos     import prestamos_bp
    from routes.docentes      import docentes_bp
    from routes.usuarios      import usuarios_bp
    from routes.reportes      import reportes_bp
    from routes.main          import main_bp
    from routes.horarios      import horarios_bp          # NUEVO
    from routes.notificaciones import notificaciones_bp   # NUEVO

    app.register_blueprint(auth_bp)
    app.register_blueprint(carros_bp)
    app.register_blueprint(netbooks_bp)
    app.register_blueprint(prestamos_bp)
    app.register_blueprint(docentes_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(horarios_bp)           # NUEVO
    app.register_blueprint(notificaciones_bp)     # NUEVO

    # ── Crear tablas ──────────────────────────────────────────────────────────
    with app.app_context():
        # Importar modelos nuevos para que SQLAlchemy los registre
        import models_extra.horarios_notificaciones  # noqa
        db.create_all()
        _crear_admin_inicial()

    # ── Schedulers en segundo plano ───────────────────────────────────────────
    from services.backup import iniciar_scheduler_backup
    from services.alertas_horario import iniciar_scheduler_alertas
    iniciar_scheduler_backup(app)
    iniciar_scheduler_alertas(app)

    return app


def _crear_admin_inicial():
    """Crea el usuario administrador si no existe"""
    if not Usuario.query.filter_by(dni='41469656').first():
        admin = Usuario(
            dni               = '41469656',
            nombre            = 'Nicolas',
            apellido          = 'Montefinal Turnes',
            username          = 'admin',
            rol               = 'Administrador',
            activo            = True,
            codigo_credencial = 'ENCU7JRUR'
        )
        admin.set_password('sigartec2024')
        db.session.add(admin)
        db.session.commit()
        print("Usuario administrador creado: admin / sigartec2024")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
