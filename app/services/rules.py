"""Deterministic rule engine - explainable, instant, works even without an ML model."""
from dataclasses import dataclass, field

RANK = {"NORMAL": 0, "OFF": 0, "WARNING": 1, "FAULT": 2}


@dataclass
class Evaluation:
    status: str = "NORMAL"
    reasons: list[str] = field(default_factory=list)

    def escalate(self, level: str, reason: str) -> None:
        self.reasons.append(reason)
        if RANK[level] > RANK[self.status]:
            self.status = level


def evaluate(temperature: float, voltage: float, current: float, oil_percentage: float, th: dict) -> Evaluation:
    if voltage <= 0 and current <= 0:
        return Evaluation("OFF", ["Power supply is off (no voltage or current)"])

    ev = Evaluation()

    t = th["temperature"]
    if temperature >= t["fault"]:
        ev.escalate("FAULT", f"Over-temperature: {temperature:.1f} °C (limit {t['fault']:g} °C)")
    elif temperature >= t["warn"]:
        ev.escalate("WARNING", f"High temperature: {temperature:.1f} °C (warning at {t['warn']:g} °C)")

    v = th["voltage"]
    if voltage < v["fault_below"]:
        ev.escalate("FAULT", f"Under-voltage: {voltage:.2f} V (limit {v['fault_below']:g} V)")
    elif voltage < v["warn_below"]:
        ev.escalate("WARNING", f"Low voltage: {voltage:.2f} V (warning below {v['warn_below']:g} V)")

    c = th["current"]
    if current >= c["fault"]:
        ev.escalate("FAULT", f"Over-current: {current:.2f} A (limit {c['fault']:g} A)")
    elif current >= c["warn"]:
        ev.escalate("WARNING", f"High current: {current:.2f} A (warning at {c['warn']:g} A)")

    o = th["oil"]
    if oil_percentage < o["fault_below"]:
        ev.escalate("FAULT", f"Critically low oil: {oil_percentage:.0f} % (limit {o['fault_below']:g} %)")
    elif oil_percentage < o["warn_below"]:
        ev.escalate("WARNING", f"Low oil: {oil_percentage:.0f} % (warning below {o['warn_below']:g} %)")

    return ev
