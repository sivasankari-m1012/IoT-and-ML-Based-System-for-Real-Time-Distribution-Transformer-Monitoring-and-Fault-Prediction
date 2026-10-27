"""Isolation Forest wrapper. Loaded once at startup; degrades gracefully if the model is absent."""
import logging
from pathlib import Path

import joblib

from .features import single_row

log = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self, pipeline=None, meta: dict | None = None):
        self.pipeline = pipeline
        self.meta = meta or {}

    @property
    def available(self) -> bool:
        return self.pipeline is not None

    @classmethod
    def load(cls, path: str | Path) -> "AnomalyDetector":
        path = Path(path)
        if not path.exists():
            log.warning("Model %s not found - running rules-only. Train one: python -m ml.train", path)
            return cls()
        try:
            bundle = joblib.load(path)
            log.info("Loaded anomaly model (trained %s)", bundle["meta"].get("trained_at"))
            return cls(bundle["pipeline"], bundle["meta"])
        except Exception:  # corrupt file or scikit-learn version mismatch
            log.exception("Could not load model %s - running rules-only. Retrain with: python -m ml.train", path)
            return cls()

    def score(self, temperature: float, voltage: float, current: float, oil_percentage: float) -> dict | None:
        """Return {'anomaly': bool, 'score': float}. Score < 0 means anomalous."""
        if not self.available:
            return None
        s = float(self.pipeline.decision_function(single_row(temperature, voltage, current, oil_percentage))[0])
        return {"anomaly": s < 0, "score": round(s, 4)}
