import hmac
from functools import wraps

from flask import current_app, jsonify, request


def require_api_key(view):
    """Protect write endpoints with the shared `X-API-Key` header (constant-time compare)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config["API_KEY"]
        if expected:
            supplied = request.headers.get("X-API-Key", "")
            if not hmac.compare_digest(supplied.encode(), expected.encode()):
                return jsonify(error="unauthorized", message="Missing or invalid X-API-Key"), 401
        return view(*args, **kwargs)

    return wrapper
