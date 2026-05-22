"""Edge case tests for /synthesize endpoint."""

import base64
import wave
import io


def test_empty_text_returns_400(client):
    response = client.post("/synthesize", json={"text": "", "language": "en"})
    assert response.status_code == 400


def test_whitespace_only_text_returns_400(client):
    response = client.post("/synthesize", json={"text": "   ", "language": "en"})
    assert response.status_code == 400


def test_unsupported_language_returns_400(client):
    response = client.post("/synthesize", json={"text": "Bonjour", "language": "fr"})
    assert response.status_code == 400


def test_very_long_text_does_not_crash(client):
    long_text = "Hello world. " * 40  # ~520 chars
    response = client.post("/synthesize", json={"text": long_text, "language": "en"})
    assert response.status_code == 200


def test_punctuation_and_numbers_do_not_crash(client):
    text = "Call 911! It's 3:45 PM... really? Yes — 100%."
    response = client.post("/synthesize", json={"text": text, "language": "en"})
    assert response.status_code == 200


def test_mixed_language_text_does_not_crash(client):
    # English voice asked to render text with some Chinese characters — should not raise
    text = "Hello, 你好, world."
    response = client.post("/synthesize", json={"text": text, "language": "en"})
    assert response.status_code == 200


def test_specific_voice_override(client):
    response = client.post(
        "/synthesize",
        json={"text": "Hello", "language": "en", "voice": "en_US-lessac-medium.onnx"},
    )
    assert response.status_code == 200


def test_unknown_voice_override_returns_400(client):
    response = client.post(
        "/synthesize",
        json={"text": "Hello", "language": "en", "voice": "nonexistent-voice.onnx"},
    )
    assert response.status_code == 400


def test_newline_in_text_does_not_crash(client):
    response = client.post("/synthesize", json={"text": "Hello\nworld", "language": "en"})
    assert response.status_code == 200
