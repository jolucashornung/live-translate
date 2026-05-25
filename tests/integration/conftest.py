import time

import httpx
import pytest

ORCHESTRATOR_URL = "http://localhost:8000"
TTS_URL = "http://localhost:8003"

_HEALTH_POLL_INTERVAL_S = 5
_HEALTH_TIMEOUT_S = 120


@pytest.fixture(scope="session")
def services_healthy():
    deadline = time.monotonic() + _HEALTH_TIMEOUT_S
    last_error: str = ""
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{ORCHESTRATOR_URL}/health", timeout=10)
            if response.status_code == 200:
                body = response.json()
                all_ok = all(
                    v.get("status") == "ok"
                    for v in body.get("services", {}).values()
                )
                if all_ok:
                    return
                last_error = f"degraded: {body}"
        except httpx.TransportError as e:
            last_error = str(e)
        time.sleep(_HEALTH_POLL_INTERVAL_S)

    pytest.skip(
        f"Services did not become healthy within {_HEALTH_TIMEOUT_S}s. "
        f"Last status: {last_error}. "
        "Run `waxberry start` before running integration tests."
    )


def generate_speech_audio(text: str, lang: str) -> str:
    """Call TTS directly to produce test audio. Returns base64-encoded WAV."""
    response = httpx.post(
        f"{TTS_URL}/synthesize",
        json={"text": text, "language": lang, "voice": None},
        timeout=60,
    )
    assert response.status_code == 200, f"TTS failed ({response.status_code}): {response.text}"
    return response.json()["audio_base64"]
