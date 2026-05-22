"""Tests for /health and /voices endpoints."""


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_engine_is_piper(client):
    data = client.get("/health").json()
    assert data["engine"] == "piper"


def test_health_license_is_mit(client):
    data = client.get("/health").json()
    assert data["license"] == "MIT"


def test_health_status_is_ok(client):
    data = client.get("/health").json()
    assert data["status"] == "ok"


def test_health_loaded_voices_includes_en(client):
    data = client.get("/health").json()
    assert "en" in data["loaded_voices"]


def test_health_loaded_voices_includes_zh(client):
    data = client.get("/health").json()
    assert "zh" in data["loaded_voices"]


def test_voices_endpoint_returns_200(client):
    response = client.get("/voices")
    assert response.status_code == 200


def test_voices_endpoint_lists_loaded_voices(client):
    data = client.get("/voices").json()
    assert "en" in data["loaded"]
    assert "zh" in data["loaded"]


def test_voices_endpoint_lists_available_models(client):
    data = client.get("/voices").json()
    assert isinstance(data["available_models"], list)
    assert len(data["available_models"]) > 0
