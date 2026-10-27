"""Input validation for the ingestion endpoint (no external dependency)."""
import math
from datetime import UTC, datetime

from .errors import ValidationError

# Physically plausible sensor ranges; anything outside is rejected as a wiring/firmware bug.
FIELD_RANGES = {
    "temperature": (-40.0, 200.0),   # °C
    "voltage": (0.0, 1000.0),        # V
    "current": (0.0, 1000.0),        # A
    "oil": (0.0, 1000.0),            # cm (ultrasonic distance to oil surface)
}


def parse_reading_payload(data) -> dict[str, float]:
    if not isinstance(data, dict):
        raise ValidationError({"body": "Request body must be a JSON object"})

    errors, clean = {}, {}
    for name, (lo, hi) in FIELD_RANGES.items():
        if name not in data:
            errors[name] = "required"
            continue
        raw = data[name]
        if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
            errors[name] = "must be a number"
            continue
        try:
            value = float(raw)
        except ValueError:
            errors[name] = "must be a number"
            continue
        if not math.isfinite(value):
            errors[name] = "must be finite"
        elif not lo <= value <= hi:
            errors[name] = f"must be between {lo:g} and {hi:g}"
        else:
            clean[name] = value
    if errors:
        raise ValidationError(errors)
    return clean


def parse_since(value: str | None) -> datetime | None:
    """Parse ISO-8601 into naive UTC (how timestamps are stored)."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError({"since": "must be ISO-8601, e.g. 2026-10-26T09:00:00Z"}) from None
    if dt.tzinfo:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def parse_int_arg(value: str | None, name: str, default: int, lo: int, hi: int) -> int:
    if value is None:
        return default
    try:
        n = int(value)
    except ValueError:
        raise ValidationError({name: "must be an integer"}) from None
    if not lo <= n <= hi:
        raise ValidationError({name: f"must be between {lo} and {hi}"})
    return n
