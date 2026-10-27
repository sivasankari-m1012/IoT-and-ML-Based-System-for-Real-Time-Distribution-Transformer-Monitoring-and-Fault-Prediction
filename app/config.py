"""Central configuration. Every value can be overridden with an environment variable."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    INSTANCE_DIR = BASE_DIR / "instance"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{(INSTANCE_DIR / 'transformer.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Shared secret the ESP32 sends in the `X-API-Key` header.
    API_KEY = os.getenv("API_KEY", "")

    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "anomaly_model.joblib"))

    # Ultrasonic sensor sits on top of the tank; it measures distance to the oil surface.
    TANK_HEIGHT_CM = _float("TANK_HEIGHT_CM", 30)

    # Dashboard shows "device offline" if no reading arrives within this many seconds.
    DEVICE_STALE_SECONDS = int(_float("DEVICE_STALE_SECONDS", 120))
    DASHBOARD_POLL_MS = int(_float("DASHBOARD_POLL_MS", 5000))

    # Rule-engine limits. Tuned to the sample dataset; change per transformer rating.
    THRESHOLDS = {
        "temperature": {
            "warn": _float("TEMP_WARN", 50),
            "fault": _float("TEMP_FAULT", 60),
        },
        "voltage": {
            "warn_below": _float("VOLT_WARN_BELOW", 10),
            "fault_below": _float("VOLT_FAULT_BELOW", 5),
        },
        "current": {
            "warn": _float("CURRENT_WARN", 3),
            "fault": _float("CURRENT_FAULT", 4),
        },
        "oil": {
            "warn_below": _float("OIL_WARN_BELOW", 25),
            "fault_below": _float("OIL_FAULT_BELOW", 15),
        },
    }


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    API_KEY = "test-key"
    MODEL_PATH = str(BASE_DIR / "models" / "does-not-exist.joblib")
