import base64

import httpx
import pytest

from .conftest import ORCHESTRATOR_URL, TTS_URL

ASR_URL = "http://localhost:8001"
TRANSLATION_URL = "http://localhost:8002"


def _post_translate(payload: dict) -> httpx.Response:
    return httpx.post(f"{ORCHESTRATOR_URL}/translate", json=payload, timeout=30)


def test_invalid_base64_returns_error_response(services_healthy):
    response = _post_translate({"audio_base64": "not-valid-base64!!!", "sample_rate": 16000})
    # The orchestrator surfaces ASR errors as 4xx/5xx or a structured error body.
    assert response.status_code in (400, 422, 502)


def test_empty_audio_base64_returns_error_response(services_healthy):
    response = _post_translate({"audio_base64": "", "sample_rate": 16000})
    assert response.status_code in (400, 422, 502)


def test_random_non_audio_bytes_handled_gracefully(services_healthy):
    # Random bytes that are valid base64 but not a valid audio file.
    garbage = base64.b64encode(b"\x00" * 512).decode()
    response = _post_translate({"audio_base64": garbage, "sample_rate": 16000})
    # Must not crash with 500; a structured error or empty-speech response is acceptable.
    assert response.status_code != 500
    assert response.json()  # response body must be valid JSON


def test_orchestrator_health_returns_all_service_entries(services_healthy):
    response = httpx.get(f"{ORCHESTRATOR_URL}/health", timeout=10)
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "services" in body
    services = body["services"]
    assert "asr" in services
    assert "translation" in services
    assert "tts" in services


def test_asr_health_endpoint_is_reachable(services_healthy):
    response = httpx.get(f"{ASR_URL}/health", timeout=10)
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_translation_health_endpoint_is_reachable(services_healthy):
    response = httpx.get(f"{TRANSLATION_URL}/health", timeout=10)
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_tts_health_endpoint_is_reachable(services_healthy):
    response = httpx.get(f"{TTS_URL}/health", timeout=10)
    assert response.status_code == 200
    assert response.json().get("status") == "ok"
