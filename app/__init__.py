"""Fábrica da aplicação CorteCerto."""
from flask import Flask

from config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError(
            "SECRET_KEY não definida. Copie .env.example para .env e preencha."
        )

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401  (registra as tabelas)
    from app.routes.auth import bp as auth_bp
    from app.routes.barbeiros import bp as barbeiros_bp
    from app.routes.main import bp as main_bp
    from app.routes.paineis import bp as paineis_bp
    from app.routes.servicos import bp as servicos_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(paineis_bp)
    app.register_blueprint(servicos_bp)
    app.register_blueprint(barbeiros_bp)

    from app.utils import formatar_preco
    app.jinja_env.filters["brl"] = formatar_preco
    return app
