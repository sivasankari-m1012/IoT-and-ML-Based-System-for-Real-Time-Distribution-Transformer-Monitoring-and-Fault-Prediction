from app.config import Config
from app.services.rules import evaluate

TH = Config.THRESHOLDS


def test_normal():
    ev = evaluate(32, 12.1, 1.3, 80, TH)
    assert ev.status == "NORMAL" and ev.reasons == []


def test_off_when_no_power():
    assert evaluate(28, 0, 0, 0, TH).status == "OFF"


def test_overtemperature_is_fault():
    ev = evaluate(65, 11, 1.8, 50, TH)
    assert ev.status == "FAULT" and "Over-temperature" in ev.reasons[0]


def test_warning_band():
    assert evaluate(52, 12, 1.3, 80, TH).status == "WARNING"


def test_undervoltage_fault():
    assert evaluate(40, 4.5, 1.9, 40, TH).status == "FAULT"


def test_low_oil_levels():
    assert evaluate(30, 12, 1.2, 20, TH).status == "WARNING"
    assert evaluate(30, 12, 1.2, 10, TH).status == "FAULT"


def test_worst_status_wins_and_all_reasons_kept():
    ev = evaluate(55, 12, 4.5, 80, TH)
    assert ev.status == "FAULT" and len(ev.reasons) == 2
