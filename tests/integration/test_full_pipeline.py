import base64
import re

import httpx
import pytest

from .conftest import ORCHESTRATOR_URL, generate_speech_audio

_CHINESE_CHAR_PATTERN = re.compile(r"[一-鿿]")


def _post_translate(audio_base64: str) -> dict:
    response = httpx.post(
        f"{ORCHESTRATOR_URL}/translate",
        json={"audio_base64": audio_base64, "sample_rate": 16000},
        timeout=120,
    )
    assert response.status_code == 200
    return response.json()


def test_english_audio_translates_to_chinese(services_healthy):
    audio_b64 = generate_speech_audio("Hello, how are you today?", "en")
    result = _post_translate(audio_b64)

    assert result["detected_language"] == "en"
    assert result["target_language"] == "zh"
    assert _CHINESE_CHAR_PATTERN.search(result["translated_text"]), (
        f"Expected Chinese characters in: {result['translated_text']!r}"
    )
    assert result["audio_base64"]
    base64.b64decode(result["audio_base64"])  # validates it is well-formed base64


def test_chinese_audio_translates_to_english(services_healthy):
    audio_b64 = generate_speech_audio("你好，今天天气怎么样？", "zh")
    result = _post_translate(audio_b64)

    assert result["detected_language"] == "zh"
    assert result["target_language"] == "en"
    assert re.search(r"[a-zA-Z]", result["translated_text"]), (
        f"Expected ASCII letters in: {result['translated_text']!r}"
    )
    assert result["audio_base64"]
    base64.b64decode(result["audio_base64"])


def test_english_to_chinese_round_trip_produces_non_empty_english(services_healthy):
    # Translate English → Chinese via the pipeline.
    en_audio = generate_speech_audio("The weather is nice today.", "en")
    first = _post_translate(en_audio)
    assert first["detected_language"] == "en"
    chinese_text = first["translated_text"]

    # Use the translated Chinese text to generate audio, then translate back.
    zh_audio = generate_speech_audio(chinese_text, "zh")
    second = _post_translate(zh_audio)

    assert second["detected_language"] == "zh"
    assert second["translated_text"].strip(), "Round-trip translation produced empty English output"
