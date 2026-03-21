"""
Application factory.

Layers: controllers (HTTP) -> services (business) -> models (ORM).
"""

from flask import Flask

from .commands.seed import register_seed_command
from .config import Config
from .controllers.auth_controller import auth_bp
from .controllers.asset_controller import assets_bp
from .controllers.evaluation_controller import evaluations_bp
from .extensions import db, migrate
from .utils.errors import register_error_handlers


def create_app(config_object: type[Config] = Config) -> Flask:
    """Create Flask app, bind extensions, blueprints, errors, and CLI seed."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(assets_bp, url_prefix="/api/v1/assets")
    app.register_blueprint(evaluations_bp, url_prefix="/api/v1/evaluations")

    register_error_handlers(app)
    register_seed_command(app)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    return app
