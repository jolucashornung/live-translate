import httpx
import pytest

from .conftest import ORCHESTRATOR_URL, generate_speech_audio


def _detected_language(audio_b64: str) -> str:
    response = httpx.post(
        f"{ORCHESTRATOR_URL}/translate",
        json={"audio_base64": audio_b64, "sample_rate": 16000},
        timeout=120,
    )
    assert response.status_code == 200
    return response.json()["detected_language"]


def test_short_english_audio_detected_as_english(services_healthy):
    audio_b64 = generate_speech_audio("Hello.", "en")
    assert _detected_language(audio_b64) == "en"


def test_long_english_audio_detected_as_english(services_healthy):
    text = (
        "The quick brown fox jumps over the lazy dog. "
        "Speech recognition systems must handle varying sentence lengths reliably. "
        "This sentence is intentionally long to exercise that capability."
    )
    audio_b64 = generate_speech_audio(text, "en")
    assert _detected_language(audio_b64) == "en"


def test_short_chinese_audio_detected_as_chinese(services_healthy):
    audio_b64 = generate_speech_audio("你好。", "zh")
    assert _detected_language(audio_b64) == "zh"


def test_long_chinese_audio_detected_as_chinese(services_healthy):
    text = (
        "今天天气非常好，阳光明媚，微风吹拂。"
        "语音识别系统需要可靠地处理不同长度的句子。"
        "这个句子故意写得很长，以测试该功能。"
    )
    audio_b64 = generate_speech_audio(text, "zh")
    assert _detected_language(audio_b64) == "zh"
