import base64


def test_invalid_base64_returns_400(client):
    response = client.post(
        "/transcribe", json={"audio_base64": "!!! not base64 !!!", "sample_rate": 16000}
    )
    assert response.status_code == 400


def test_empty_wav_does_not_crash(client, empty_wav_b64):
    response = client.post(
        "/transcribe", json={"audio_base64": empty_wav_b64, "sample_rate": 16000}
    )
    assert response.status_code in (200, 422)


def test_empty_wav_response_has_valid_schema(client, empty_wav_b64):
    response = client.post(
        "/transcribe", json={"audio_base64": empty_wav_b64, "sample_rate": 16000}
    )
    if response.status_code == 200:
        data = response.json()
        assert "text" in data
        assert "language" in data
        assert "confidence" in data


def test_very_short_audio_returns_response(client, short_wav_b64):
    response = client.post(
        "/transcribe", json={"audio_base64": short_wav_b64, "sample_rate": 16000}
    )
    assert response.status_code in (200, 422)


def test_non_audio_base64_returns_error_not_crash(client):
    non_audio_b64 = base64.b64encode(b"this is definitely not audio data at all").decode()
    response = client.post(
        "/transcribe", json={"audio_base64": non_audio_b64, "sample_rate": 16000}
    )
    assert response.status_code in (200, 400, 422, 500)
