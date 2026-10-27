from datetime import UTC, datetime

from .extensions import db


def utcnow() -> datetime:
    """Naive UTC (SQLite has no tz support); serialised with a trailing Z."""
    return datetime.now(UTC).replace(tzinfo=None)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat(timespec="seconds") + "Z" if dt else None


class Transformer(db.Model):
    __tablename__ = "transformers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "location": self.location}


class Reading(db.Model):
    __tablename__ = "readings"
    __table_args__ = (db.Index("ix_readings_transformer_time", "transformer_id", "timestamp"),)

    id = db.Column(db.Integer, primary_key=True)
    transformer_id = db.Column(db.Integer, db.ForeignKey("transformers.id"), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow)
    temperature = db.Column(db.Float, nullable=False)
    voltage = db.Column(db.Float, nullable=False)
    current = db.Column(db.Float, nullable=False)
    oil_percentage = db.Column(db.Float, nullable=False)
    power = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # NORMAL | WARNING | FAULT | OFF
    anomaly_score = db.Column(db.Float)  # IsolationForest decision score (<0 = anomalous); None if no model
    reasons = db.Column(db.JSON, nullable=False, default=list)

    def to_dict(self):
        return {
            "id": self.id,
            "transformer_id": self.transformer_id,
            "timestamp": iso(self.timestamp),
            "temperature": self.temperature,
            "voltage": self.voltage,
            "current": self.current,
            "oil_percentage": self.oil_percentage,
            "power": self.power,
            "status": self.status,
            "anomaly_score": self.anomaly_score,
            "reasons": self.reasons or [],
        }


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    transformer_id = db.Column(db.Integer, db.ForeignKey("transformers.id"), nullable=False, index=True)
    reading_id = db.Column(db.Integer, db.ForeignKey("readings.id"), nullable=False)
    severity = db.Column(db.String(10), nullable=False)  # WARNING | FAULT
    message = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    resolved_at = db.Column(db.DateTime)  # set automatically when the transformer returns to NORMAL

    def to_dict(self):
        return {
            "id": self.id,
            "transformer_id": self.transformer_id,
            "reading_id": self.reading_id,
            "severity": self.severity,
            "message": self.message,
            "created_at": iso(self.created_at),
            "resolved_at": iso(self.resolved_at),
            "active": self.resolved_at is None,
        }
