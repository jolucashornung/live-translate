import httpx
import respx

AUDIO_PAYLOAD = {"audio_base64": "dGVzdA==", "sample_rate": 16000}


def test_unsupported_language_returns_error_response(client):
    with respx.mock:
        respx.post("http://localhost:8001/transcribe").mock(
            return_value=httpx.Response(
                200, json={"text": "Bonjour", "language": "fr", "confidence": 0.91}
            )
        )

        response = client.post("/translate", json=AUDIO_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["detected_language"] == "fr"
    assert data["original_text"] == "Bonjour"
    assert "'fr'" in data["error"]
    assert "audio_base64" not in data


def test_empty_transcription_returns_no_speech_error(client):
    with respx.mock:
        respx.post("http://localhost:8001/transcribe").mock(
            return_value=httpx.Response(
                200, json={"text": "", "language": "en", "confidence": 0.0}
            )
        )

        response = client.post("/translate", json=AUDIO_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "No speech" in data["error"]
    assert data["detected_language"] == "en"
    assert "audio_base64" not in data


def test_whitespace_only_transcription_returns_no_speech_error(client):
    with respx.mock:
        respx.post("http://localhost:8001/transcribe").mock(
            return_value=httpx.Response(
                200, json={"text": "   ", "language": "en", "confidence": 0.01}
            )
        )

        response = client.post("/translate", json=AUDIO_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "No speech" in data["error"]


def test_asr_service_unreachable_returns_503(client):
    with respx.mock:
        respx.post("http://localhost:8001/transcribe").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        response = client.post("/translate", json=AUDIO_PAYLOAD)

    assert response.status_code == 503
    assert "ASR service unreachable" in response.json()["detail"]


def test_translation_service_returns_500_gives_502(client):
    with respx.mock:
        respx.post("http://localhost:8001/transcribe").mock(
            return_value=httpx.Response(
                200, json={"text": "Hello", "language": "en", "confidence": 0.95}
            )
        )
        respx.post("http://localhost:8002/translate").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        response = client.post("/translate", json=AUDIO_PAYLOAD)

    assert response.status_code == 502
    assert "Translation service error" in response.json()["detail"]


def test_tts_service_unreachable_returns_503(client):
    with respx.mock:
        respx.post("http://localhost:8001/transcribe").mock(
            return_value=httpx.Response(
                200, json={"text": "Hello", "language": "en", "confidence": 0.95}
            )
        )
        respx.post("http://localhost:8002/translate").mock(
            return_value=httpx.Response(
                200,
                json={"translated_text": "你好", "source_lang": "en", "target_lang": "zh"},
            )
        )
        respx.post("http://localhost:8003/synthesize").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        response = client.post("/translate", json=AUDIO_PAYLOAD)

    assert response.status_code == 503
    assert "TTS service unreachable" in response.json()["detail"]
