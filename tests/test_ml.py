import joblib
import pytest

from app import create_app
from app.config import TestConfig
from ml.train import DEFAULT_DATA, cross_validate, fit_model, load_data


@pytest.fixture(scope="module")
def df():
    return load_data(DEFAULT_DATA)


def test_cross_validated_recall_is_reasonable(df):
    m = cross_validate(df)
    assert m["fault_recall"] >= 0.7 and m["fault_precision"] >= 0.7


def test_app_uses_model_when_present(tmp_path, df):
    path = tmp_path / "m.joblib"
    joblib.dump({"pipeline": fit_model(df), "meta": {"trained_at": "test"}}, path)

    class Cfg(TestConfig):
        MODEL_PATH = str(path)

    client = create_app(Cfg).test_client()
    headers = {"X-API-Key": "test-key"}
    healthy = client.post("/api/v1/transformers/1/readings", headers=headers,
                          json={"temperature": 32, "voltage": 12.3, "current": 1.3, "oil": 5}).get_json()["reading"]
    assert healthy["anomaly_score"] is not None and healthy["status"] == "NORMAL"
    # Every individual value is inside its warning limit, but the *combination* is wrong:
    odd = client.post("/api/v1/transformers/1/readings", headers=headers,
                      json={"temperature": 49, "voltage": 10.1, "current": 2.9, "oil": 5}).get_json()["reading"]
    assert odd["status"] == "WARNING"
    assert any("anomaly model" in r for r in odd["reasons"])


def test_corrupt_model_falls_back_to_rules(tmp_path):
    bad = tmp_path / "bad.joblib"
    bad.write_bytes(b"not a model")

    class Cfg(TestConfig):
        MODEL_PATH = str(bad)

    assert create_app(Cfg).test_client().get("/api/v1/health").get_json()["model_loaded"] is False
