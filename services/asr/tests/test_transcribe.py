import pytest


def test_transcribe_sine_wave_returns_200(client, sine_wave_b64):
    response = client.post("/transcribe", json={"audio_base64": sine_wave_b64, "sample_rate": 16000})
    assert response.status_code == 200


def test_transcribe_response_has_required_fields(client, sine_wave_b64):
    response = client.post("/transcribe", json={"audio_base64": sine_wave_b64, "sample_rate": 16000})
    data = response.json()
    assert "text" in data
    assert "language" in data
    assert "confidence" in data


def test_transcribe_text_is_string(client, sine_wave_b64):
    response = client.post("/transcribe", json={"audio_base64": sine_wave_b64, "sample_rate": 16000})
    assert isinstance(response.json()["text"], str)


def test_transcribe_language_is_string(client, sine_wave_b64):
    response = client.post("/transcribe", json={"audio_base64": sine_wave_b64, "sample_rate": 16000})
    assert isinstance(response.json()["language"], str)


def test_transcribe_confidence_is_float_in_range(client, sine_wave_b64):
    response = client.post("/transcribe", json={"audio_base64": sine_wave_b64, "sample_rate": 16000})
    confidence = response.json()["confidence"]
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0


def test_transcribe_english_speech_returns_en(client, english_speech_b64):
    if english_speech_b64 is None:
        pytest.skip("English speech fixture not available — run tests/fixtures/generate_test_audio.py")
    response = client.post(
        "/transcribe", json={"audio_base64": english_speech_b64, "sample_rate": 16000}
    )
    assert response.status_code == 200
    assert response.json()["language"] == "en"


def test_transcribe_chinese_speech_returns_zh(client, chinese_speech_b64):
    if chinese_speech_b64 is None:
        pytest.skip("Chinese speech fixture not available — run tests/fixtures/generate_test_audio.py")
    response = client.post(
        "/transcribe", json={"audio_base64": chinese_speech_b64, "sample_rate": 16000}
    )
    assert response.status_code == 200
    assert response.json()["language"] == "zh"
