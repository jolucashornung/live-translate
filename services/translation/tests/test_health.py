def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_has_required_fields(client):
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert "provider" in data
    assert "model" in data
    assert "license" in data


def test_health_provider_is_opus_mt(client):
    data = client.get("/health").json()
    assert data["provider"] == "opus-mt"


def test_health_device_is_cpu_or_cuda(client):
    data = client.get("/health").json()
    assert data["device"] in ("cpu", "cuda")


def test_health_lists_both_language_pairs(client):
    data = client.get("/health").json()
    loaded = data["loaded_pairs"]
    assert "en→zh" in loaded
    assert "zh→en" in loaded


def test_health_license_is_apache(client):
    data = client.get("/health").json()
    assert "Apache-2.0" in data["license"]
