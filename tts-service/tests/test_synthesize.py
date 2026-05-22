"""Tests for /synthesize endpoint with real Piper synthesis."""

import base64
import wave
import io


def _decode_wav(audio_base64: str) -> wave.Wave_read:
    wav_bytes = base64.b64decode(audio_base64)
    return wave.open(io.BytesIO(wav_bytes), "rb")


def test_english_synthesis_returns_200(client):
    response = client.post("/synthesize", json={"text": "Hello world", "language": "en"})
    assert response.status_code == 200


def test_english_synthesis_returns_valid_base64_wav(client):
    data = client.post("/synthesize", json={"text": "Hello world", "language": "en"}).json()
    wav = _decode_wav(data["audio_base64"])
    assert wav.getnframes() > 0
    wav.close()


def test_english_wav_has_valid_sample_rate(client):
    data = client.post("/synthesize", json={"text": "Hello world", "language": "en"}).json()
    wav = _decode_wav(data["audio_base64"])
    assert 16000 <= wav.getframerate() <= 22050
    wav.close()


def test_english_wav_is_mono(client):
    data = client.post("/synthesize", json={"text": "Hello world", "language": "en"}).json()
    wav = _decode_wav(data["audio_base64"])
    assert wav.getnchannels() == 1
    wav.close()


def test_chinese_synthesis_returns_200(client):
    response = client.post("/synthesize", json={"text": "你好世界", "language": "zh"})
    assert response.status_code == 200


def test_chinese_synthesis_returns_valid_base64_wav(client):
    data = client.post("/synthesize", json={"text": "你好世界", "language": "zh"}).json()
    wav = _decode_wav(data["audio_base64"])
    assert wav.getnframes() > 0
    wav.close()


def test_chinese_wav_has_valid_sample_rate(client):
    data = client.post("/synthesize", json={"text": "你好世界", "language": "zh"}).json()
    wav = _decode_wav(data["audio_base64"])
    assert 16000 <= wav.getframerate() <= 22050
    wav.close()


def test_chinese_wav_is_mono(client):
    data = client.post("/synthesize", json={"text": "你好世界", "language": "zh"}).json()
    wav = _decode_wav(data["audio_base64"])
    assert wav.getnchannels() == 1
    wav.close()


def test_long_sentence_synthesizes_without_error(client):
    long_text = (
        "The quick brown fox jumps over the lazy dog near the river bank "
        "while the sun sets slowly behind the mountains in the distance "
        "casting long shadows across the golden fields of wheat."
    )
    response = client.post("/synthesize", json={"text": long_text, "language": "en"})
    assert response.status_code == 200
    data = response.json()
    wav = _decode_wav(data["audio_base64"])
    assert wav.getnframes() > 0
    wav.close()


def test_response_mime_type_is_audio_wav(client):
    data = client.post("/synthesize", json={"text": "Hello", "language": "en"}).json()
    assert data["mime_type"] == "audio/wav"
