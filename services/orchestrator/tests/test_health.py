import httpx
import respx

ASR_HEALTH_OK = {"status": "ok", "model": "base", "device": "cpu"}
TRANSLATION_HEALTH_OK = {"status": "ok", "device": "cpu", "loaded_pairs": ["en→zh", "zh→en"]}
TTS_HEALTH_OK = {"status": "ok", "engine": "piper", "loaded_voices": ["en", "zh"]}


def test_health_all_services_ok(client):
    with respx.mock:
        respx.get("http://localhost:8001/health").mock(
            return_value=httpx.Response(200, json=ASR_HEALTH_OK)
        )
        respx.get("http://localhost:8002/health").mock(
            return_value=httpx.Response(200, json=TRANSLATION_HEALTH_OK)
        )
        respx.get("http://localhost:8003/health").mock(
            return_value=httpx.Response(200, json=TTS_HEALTH_OK)
        )

        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["services"]["asr"]["status"] == "ok"
    assert data["services"]["asr"]["model"] == "base"
    assert data["services"]["translation"]["status"] == "ok"
    assert data["services"]["tts"]["status"] == "ok"


def test_health_one_service_unreachable(client):
    with respx.mock:
        respx.get("http://localhost:8001/health").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        respx.get("http://localhost:8002/health").mock(
            return_value=httpx.Response(200, json=TRANSLATION_HEALTH_OK)
        )
        respx.get("http://localhost:8003/health").mock(
            return_value=httpx.Response(200, json=TTS_HEALTH_OK)
        )

        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["services"]["asr"]["status"] == "error"
    assert data["services"]["translation"]["status"] == "ok"
    assert data["services"]["tts"]["status"] == "ok"


def test_health_service_returns_500(client):
    with respx.mock:
        respx.get("http://localhost:8001/health").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        respx.get("http://localhost:8002/health").mock(
            return_value=httpx.Response(200, json=TRANSLATION_HEALTH_OK)
        )
        respx.get("http://localhost:8003/health").mock(
            return_value=httpx.Response(200, json=TTS_HEALTH_OK)
        )

        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["services"]["asr"]["status"] == "error"
    assert "HTTP 500" in data["services"]["asr"]["detail"]
    assert data["services"]["translation"]["status"] == "ok"
    assert data["services"]["tts"]["status"] == "ok"
