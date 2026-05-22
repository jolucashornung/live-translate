def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_is_ok(client):
    response = client.get("/health")
    assert response.json()["status"] == "ok"


def test_health_has_model_field(client):
    response = client.get("/health")
    assert "model" in response.json()


def test_health_has_device_field(client):
    response = client.get("/health")
    assert "device" in response.json()
