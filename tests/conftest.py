import pytest

from app import create_app
from app.config import TestConfig

HEADERS = {"X-API-Key": "test-key"}
GOOD = {"temperature": 32, "voltage": 12.1, "current": 1.3, "oil": 6}  # oil 6 cm of 30 -> 80 %


@pytest.fixture
def app():
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def post(client):
    def _post(payload=GOOD, tid=1, headers=HEADERS, prefix="/api/v1"):
        return client.post(f"{prefix}/transformers/{tid}/readings", json=payload, headers=headers)

    return _post
