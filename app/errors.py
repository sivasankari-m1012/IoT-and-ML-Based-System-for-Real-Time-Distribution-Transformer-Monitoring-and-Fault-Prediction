from flask import jsonify, request
from werkzeug.exceptions import HTTPException


class ValidationError(Exception):
    """Raised for bad client input. `errors` maps field name -> message."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("validation failed")
        self.errors = errors


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def _validation(err):
        return jsonify(error="validation_failed", details=err.errors), 400

    @app.errorhandler(HTTPException)
    def _http(err):
        if request.path.startswith("/api"):
            return jsonify(error=err.name.lower().replace(" ", "_"), message=err.description), err.code
        return err

    @app.errorhandler(Exception)
    def _unhandled(err):
        app.logger.exception("Unhandled error")
        if request.path.startswith("/api"):
            return jsonify(error="internal_server_error"), 500
        return "Internal server error", 500
