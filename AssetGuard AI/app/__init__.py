"""
Application factory.

Layers: controllers (HTTP) -> services (business) -> models (ORM).
"""

from flask import Flask, request
from flask_cors import CORS

from .commands.seed import register_seed_command
from .config import Config
from .controllers.alert_controller import alerts_bp
from .controllers.auth_controller import auth_bp
from .controllers.asset_controller import assets_bp
from .controllers.dashboard_controller import dashboard_bp
from .controllers.evaluation_controller import evaluations_bp
from .controllers.location_controller import locations_bp
from .extensions import db, migrate
from .utils.errors import register_error_handlers


def create_app(config_object: type[Config] = Config) -> Flask:
    """Create Flask app, bind extensions, blueprints, errors, and CLI seed."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(
        app,
        resources={r"/api/.*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
    )

    @app.after_request
    def add_api_cors_headers(response):
        """
        Add permissive CORS headers for API routes so local UI requests do not fail
        due to origin/port mismatches during development.
        """
        if request.path.startswith("/api/"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(alerts_bp, url_prefix="/api/v1/alerts")
    app.register_blueprint(locations_bp, url_prefix="/api/v1/locations")
    app.register_blueprint(assets_bp, url_prefix="/api/v1/assets")
    app.register_blueprint(evaluations_bp, url_prefix="/api/v1/evaluations")
    app.register_blueprint(dashboard_bp)

    register_error_handlers(app)
    register_seed_command(app)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    return app
