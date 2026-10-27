from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func, text

from ..auth import require_api_key
from ..extensions import db
from ..models import Alert, Reading, Transformer, iso, utcnow
from ..schemas import parse_int_arg, parse_reading_payload, parse_since
from ..services.readings import ingest_reading

bp = Blueprint("api", __name__)


def _transformer_or_404(transformer_id: int) -> Transformer:
    transformer = db.session.get(Transformer, transformer_id)
    if transformer is None:
        from werkzeug.exceptions import NotFound

        raise NotFound(f"Transformer {transformer_id} not found")
    return transformer


@bp.get("/health")
def health():
    db.session.execute(text("SELECT 1"))
    detector = current_app.extensions["detector"]
    return jsonify(
        status="ok",
        version=current_app.config["VERSION"],
        database="ok",
        model_loaded=detector.available,
        model_trained_at=detector.meta.get("trained_at"),
    )


@bp.get("/config")
def public_config():
    """Thresholds the dashboard draws on its gauges (single source of truth)."""
    return jsonify(thresholds=current_app.config["THRESHOLDS"])


@bp.get("/transformers")
def list_transformers():
    rows = db.session.scalars(db.select(Transformer).order_by(Transformer.id)).all()
    return jsonify(transformers=[t.to_dict() for t in rows])


@bp.post("/transformers/<int:transformer_id>/readings")
@require_api_key
def add_reading(transformer_id: int):
    clean = parse_reading_payload(request.get_json(silent=True))
    reading = ingest_reading(transformer_id, clean)
    return jsonify(message="Reading created successfully", reading=reading.to_dict()), 201


@bp.get("/transformers/<int:transformer_id>/readings")
def list_readings(transformer_id: int):
    """Latest `limit` readings (default 50, max 500), oldest first - ready for charting."""
    _transformer_or_404(transformer_id)
    limit = parse_int_arg(request.args.get("limit"), "limit", 50, 1, 500)
    since = parse_since(request.args.get("since"))

    query = db.select(Reading).filter_by(transformer_id=transformer_id)
    if since:
        query = query.where(Reading.timestamp >= since)
    rows = db.session.scalars(query.order_by(Reading.timestamp.desc(), Reading.id.desc()).limit(limit)).all()
    return jsonify(count=len(rows), readings=[r.to_dict() for r in reversed(rows)])


@bp.get("/transformers/<int:transformer_id>/latest")
def latest_reading(transformer_id: int):
    _transformer_or_404(transformer_id)
    row = db.session.scalars(
        db.select(Reading)
        .filter_by(transformer_id=transformer_id)
        .order_by(Reading.timestamp.desc(), Reading.id.desc())
        .limit(1)
    ).first()
    return jsonify(reading=row.to_dict() if row else None)


@bp.get("/transformers/<int:transformer_id>/stats")
def stats(transformer_id: int):
    """Aggregates over the last `hours` (default 24)."""
    _transformer_or_404(transformer_id)
    hours = parse_int_arg(request.args.get("hours"), "hours", 24, 1, 720)
    since = utcnow() - timedelta(hours=hours)
    where = (Reading.transformer_id == transformer_id, Reading.timestamp >= since)

    agg = db.session.execute(
        db.select(
            func.count(Reading.id),
            func.min(Reading.temperature), func.avg(Reading.temperature), func.max(Reading.temperature),
            func.min(Reading.voltage), func.avg(Reading.voltage), func.max(Reading.voltage),
            func.min(Reading.current), func.avg(Reading.current), func.max(Reading.current),
            func.min(Reading.oil_percentage), func.avg(Reading.oil_percentage), func.max(Reading.oil_percentage),
        ).where(*where)
    ).one()
    by_status = dict(
        db.session.execute(db.select(Reading.status, func.count()).where(*where).group_by(Reading.status)).all()
    )

    def block(i):
        lo, avg, hi = agg[i : i + 3]
        return None if lo is None else {"min": lo, "avg": round(avg, 2), "max": hi}

    return jsonify(
        hours=hours,
        readings=agg[0],
        temperature=block(1),
        voltage=block(4),
        current=block(7),
        oil_percentage=block(10),
        by_status=by_status,
        generated_at=iso(utcnow()),
    )


@bp.get("/alerts")
def list_alerts():
    limit = parse_int_arg(request.args.get("limit"), "limit", 20, 1, 200)
    query = db.select(Alert)
    if request.args.get("transformer_id"):
        tid = parse_int_arg(request.args["transformer_id"], "transformer_id", 1, 1, 10**9)
        query = query.where(Alert.transformer_id == tid)
    active = request.args.get("active")
    if active is not None:
        query = query.where(Alert.resolved_at.is_(None) if active.lower() == "true" else Alert.resolved_at.is_not(None))
    rows = db.session.scalars(query.order_by(Alert.created_at.desc(), Alert.id.desc()).limit(limit)).all()
    return jsonify(count=len(rows), alerts=[a.to_dict() for a in rows])
