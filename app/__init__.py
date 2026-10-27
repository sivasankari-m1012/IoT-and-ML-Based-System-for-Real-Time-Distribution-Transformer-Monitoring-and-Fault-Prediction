"""Smart Transformer Monitor - Flask application factory."""
import logging
import os

from flask import Flask

from .config import Config
from .extensions import db
from .services.ml import AnomalyDetector

__version__ = "2.0.0"


def create_app(config_object=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config["VERSION"] = __version__

    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Fail closed: a production server without an API key would accept data from anyone.
    if not app.config["API_KEY"] and not (app.debug or app.testing):
        raise RuntimeError("API_KEY must be set (see .env.example). Use FLASK_DEBUG=1 for local dev.")
    if not app.config["API_KEY"]:
        app.logger.warning("API_KEY is empty - write endpoints are UNPROTECTED (dev mode only).")

    os.makedirs(app.config["INSTANCE_DIR"], exist_ok=True)
    db.init_app(app)
    from . import models  # noqa: F401  (register tables)

    with app.app_context():
        db.create_all()

    # Loaded once at startup, not on every request. App still works (rules only) if missing.
    app.extensions["detector"] = AnomalyDetector.load(app.config["MODEL_PATH"])

    from .errors import register_error_handlers
    from .routes.api import bp as api_bp
    from .routes.web import bp as web_bp

    app.register_blueprint(api_bp, url_prefix="/api/v1")
    # Backwards compatible with the v1 ESP32 firmware: POST /api/transformers/<id>/readings
    app.register_blueprint(api_bp, url_prefix="/api", name="api_legacy")
    app.register_blueprint(web_bp)
    register_error_handlers(app)
    return app
