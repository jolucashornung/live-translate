import json

import httpx
import respx

AUDIO_PAYLOAD = {"audio_base64": "dGVzdA==", "sample_rate": 16000}


def test_translate_en_to_zh_happy_path(client):
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
            return_value=httpx.Response(
                200, json={"audio_base64": "abc123", "mime_type": "audio/wav"}
            )
        )

        response = client.post("/translate", json=AUDIO_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["original_text"] == "Hello"
    assert data["detected_language"] == "en"
    assert data["translated_text"] == "你好"
    assert data["target_language"] == "zh"
    assert data["audio_base64"] == "abc123"
    assert data["mime_type"] == "audio/wav"
    assert "error" not in data


def test_translate_zh_to_en_happy_path(client):
    with respx.mock:
        respx.post("http://localhost:8001/transcribe").mock(
            return_value=httpx.Response(
                200, json={"text": "你好", "language": "zh", "confidence": 0.92}
            )
        )
        respx.post("http://localhost:8002/translate").mock(
            return_value=httpx.Response(
                200,
                json={"translated_text": "Hello", "source_lang": "zh", "target_lang": "en"},
            )
        )
        respx.post("http://localhost:8003/synthesize").mock(
            return_value=httpx.Response(
                200, json={"audio_base64": "xyz789", "mime_type": "audio/wav"}
            )
        )

        response = client.post("/translate", json=AUDIO_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["detected_language"] == "zh"
    assert data["target_language"] == "en"
    assert data["original_text"] == "你好"
    assert data["translated_text"] == "Hello"
    assert data["audio_base64"] == "xyz789"


def test_translate_passes_correct_langs_to_translation_service(client):
    with respx.mock:
        respx.post("http://localhost:8001/transcribe").mock(
            return_value=httpx.Response(
                200, json={"text": "Hello", "language": "en", "confidence": 0.95}
            )
        )
        translation_route = respx.post("http://localhost:8002/translate").mock(
            return_value=httpx.Response(
                200,
                json={"translated_text": "你好", "source_lang": "en", "target_lang": "zh"},
            )
        )
        respx.post("http://localhost:8003/synthesize").mock(
            return_value=httpx.Response(
                200, json={"audio_base64": "abc123", "mime_type": "audio/wav"}
            )
        )

        client.post("/translate", json=AUDIO_PAYLOAD)

    translation_body = json.loads(translation_route.calls.last.request.content)
    assert translation_body["text"] == "Hello"
    assert translation_body["source_lang"] == "en"
    assert translation_body["target_lang"] == "zh"


def test_translate_passes_correct_language_to_tts_service(client):
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
        tts_route = respx.post("http://localhost:8003/synthesize").mock(
            return_value=httpx.Response(
                200, json={"audio_base64": "abc123", "mime_type": "audio/wav"}
            )
        )

        client.post("/translate", json=AUDIO_PAYLOAD)

    tts_body = json.loads(tts_route.calls.last.request.content)
    assert tts_body["text"] == "你好"
    assert tts_body["language"] == "zh"
