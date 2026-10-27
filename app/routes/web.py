from flask import Blueprint, current_app, redirect, render_template, url_for

from ..extensions import db
from ..models import Transformer

bp = Blueprint("web", __name__)

METRICS = [
    ("temperature", "Temperature", "°C"),
    ("voltage", "Voltage", "V"),
    ("current", "Current", "A"),
    ("oil", "Oil level", "%"),
]


@bp.get("/")
def index():
    return redirect(url_for("web.dashboard", transformer_id=1))


@bp.get("/dashboard/<int:transformer_id>")
def dashboard(transformer_id: int):
    transformers = db.session.scalars(db.select(Transformer).order_by(Transformer.id)).all()
    boot = {
        "transformerId": transformer_id,
        "thresholds": current_app.config["THRESHOLDS"],
        "staleSeconds": current_app.config["DEVICE_STALE_SECONDS"],
        "pollMs": current_app.config["DASHBOARD_POLL_MS"],
    }
    return render_template(
        "dashboard.html",
        transformer_id=transformer_id,
        transformers=transformers,
        metrics=METRICS,
        boot=boot,
    )
