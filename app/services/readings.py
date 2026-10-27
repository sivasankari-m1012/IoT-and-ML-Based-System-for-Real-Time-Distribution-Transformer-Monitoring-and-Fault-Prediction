"""Ingestion pipeline: validate -> oil % -> rules -> ML -> persist -> alert lifecycle."""
from flask import current_app

from ..extensions import db
from ..models import Alert, Reading, Transformer, utcnow
from .rules import RANK, evaluate


def oil_percentage_from_distance(distance_cm: float, tank_height_cm: float) -> float:
    """Ultrasonic sensor reports distance to the oil surface: small distance = full tank.

    0 (sensor timeout) or a distance beyond the tank height is reported as 0 %.
    """
    if distance_cm <= 0 or distance_cm > tank_height_cm:
        return 0.0
    return round(max(0.0, min(100.0, (tank_height_cm - distance_cm) / tank_height_cm * 100)), 1)


def get_or_create_transformer(transformer_id: int) -> Transformer:
    transformer = db.session.get(Transformer, transformer_id)
    if transformer is None:
        transformer = Transformer(id=transformer_id, name=f"Transformer {transformer_id}")
        db.session.add(transformer)
        db.session.flush()
    return transformer


def ingest_reading(transformer_id: int, clean: dict[str, float]) -> Reading:
    cfg = current_app.config
    detector = current_app.extensions["detector"]
    transformer = get_or_create_transformer(transformer_id)

    temperature, voltage, current = clean["temperature"], clean["voltage"], clean["current"]
    oil = oil_percentage_from_distance(clean["oil"], cfg["TANK_HEIGHT_CM"])

    evaluation = evaluate(temperature, voltage, current, oil, cfg["THRESHOLDS"])
    status, reasons = evaluation.status, list(evaluation.reasons)

    ml = None
    if status != "OFF":
        ml = detector.score(temperature, voltage, current, oil)
        # Hybrid: rules catch known limits; ML catches unusual *combinations* of normal-looking values.
        if ml and ml["anomaly"] and status == "NORMAL":
            status = "WARNING"
            reasons.append("Unusual sensor pattern detected by anomaly model")

    previous = db.session.scalars(
        db.select(Reading)
        .filter_by(transformer_id=transformer.id)
        .order_by(Reading.timestamp.desc(), Reading.id.desc())
        .limit(1)
    ).first()

    reading = Reading(
        transformer_id=transformer.id,
        temperature=temperature,
        voltage=voltage,
        current=current,
        oil_percentage=oil,
        power=round(voltage * current, 3),
        status=status,
        anomaly_score=ml["score"] if ml else None,
        reasons=reasons or ["All readings within limits"],
    )
    db.session.add(reading)
    db.session.flush()

    # Alert lifecycle: open one when severity *increases* (no spam on every reading),
    # auto-resolve everything when the transformer is NORMAL again.
    previous_rank = RANK[previous.status] if previous else 0
    if RANK[status] > previous_rank:
        db.session.add(
            Alert(
                transformer_id=transformer.id,
                reading_id=reading.id,
                severity=status,
                message="; ".join(reasons)[:500],
            )
        )
    elif status == "NORMAL":
        db.session.execute(
            db.update(Alert)
            .where(Alert.transformer_id == transformer.id, Alert.resolved_at.is_(None))
            .values(resolved_at=utcnow())
        )

    db.session.commit()
    current_app.logger.info(
        "reading transformer=%s status=%s temp=%.1f V=%.2f I=%.2f oil=%.0f%%",
        transformer.id, status, temperature, voltage, current, oil,
    )
    return reading
