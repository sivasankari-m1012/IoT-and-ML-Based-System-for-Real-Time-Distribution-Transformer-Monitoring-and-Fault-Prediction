from app.services.readings import oil_percentage_from_distance


def test_post_reading_ok(post):
    res = post()
    assert res.status_code == 201
    body = res.get_json()["reading"]
    assert body["status"] == "NORMAL" and body["oil_percentage"] == 80.0
    assert body["power"] == round(12.1 * 1.3, 3)


def test_requires_api_key(post):
    assert post(headers={}).status_code == 401
    assert post(headers={"X-API-Key": "wrong"}).status_code == 401


def test_legacy_v1_route_still_works(post):
    assert post(prefix="/api").status_code == 201


def test_validation_errors(post):
    res = post({"temperature": "hot", "voltage": 12})
    assert res.status_code == 400
    details = res.get_json()["details"]
    assert details["temperature"] == "must be a number"
    assert details["current"] == "required" and details["oil"] == "required"


def test_rejects_out_of_range_and_nan(post):
    assert post({**{"temperature": 32, "voltage": 12, "current": 1, "oil": 5}, "temperature": 999}).status_code == 400
    assert post({"temperature": "nan", "voltage": 12, "current": 1, "oil": 5}).status_code == 400


def test_rejects_non_json(client):
    res = client.post("/api/v1/transformers/1/readings", data="x", headers={"X-API-Key": "test-key"})
    assert res.status_code == 400


def test_fault_creates_one_alert_then_resolves(post, client):
    post()  # normal
    fault = {"temperature": 70, "voltage": 10.5, "current": 2.0, "oil": 15}
    assert post(fault).get_json()["reading"]["status"] == "FAULT"
    post(fault)  # still faulty -> must NOT create a second alert
    active = client.get("/api/v1/alerts?transformer_id=1&active=true").get_json()
    assert active["count"] == 1 and active["alerts"][0]["severity"] == "FAULT"

    post()  # back to normal -> auto-resolved
    assert client.get("/api/v1/alerts?active=true").get_json()["count"] == 0
    assert client.get("/api/v1/alerts?active=false").get_json()["count"] == 1


def test_readings_latest_stats(post, client):
    for _ in range(3):
        post()
    data = client.get("/api/v1/transformers/1/readings?limit=2").get_json()
    assert data["count"] == 2
    assert client.get("/api/v1/transformers/1/latest").get_json()["reading"]["temperature"] == 32
    stats = client.get("/api/v1/transformers/1/stats").get_json()
    assert stats["readings"] == 3 and stats["by_status"] == {"NORMAL": 3}


def test_unknown_transformer_404_and_bad_limit_400(client, post):
    assert client.get("/api/v1/transformers/99/latest").status_code == 404
    post()
    assert client.get("/api/v1/transformers/1/readings?limit=abc").status_code == 400
    assert client.get("/api/v1/transformers/1/readings?since=yesterday").status_code == 400


def test_health_and_dashboard(client):
    health = client.get("/api/v1/health").get_json()
    assert health["status"] == "ok" and health["model_loaded"] is False
    page = client.get("/dashboard/1")
    assert page.status_code == 200 and b"Transformer monitor" in page.data
    assert client.get("/").status_code == 302


def test_oil_conversion():
    assert oil_percentage_from_distance(6, 30) == 80.0
    assert oil_percentage_from_distance(0, 30) == 0.0     # sensor timeout
    assert oil_percentage_from_distance(45, 30) == 0.0    # beyond tank
