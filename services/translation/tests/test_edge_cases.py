import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.anthropic_provider import AnthropicProvider

CHINESE_CHAR_RE = re.compile(r"[一-鿿]")


def _post(client, text, source_lang, target_lang):
    return client.post(
        "/translate",
        json={"text": text, "source_lang": source_lang, "target_lang": target_lang},
    )


# ── Opus-MT (real model via session client) ──────────────────────────────────

def test_empty_text_returns_empty_not_error(client):
    response = _post(client, "", "en", "zh")
    assert response.status_code == 200
    assert response.json()["translated_text"] == ""


def test_unsupported_pair_returns_400(client):
    response = _post(client, "Bonjour", "fr", "de")
    assert response.status_code == 400


def test_same_source_and_target_returns_400(client):
    response = _post(client, "Hello", "en", "en")
    assert response.status_code == 400


def test_very_long_input_does_not_crash(client):
    long_text = "This is a test sentence. " * 100
    response = _post(client, long_text, "en", "zh")
    assert response.status_code == 200
    assert len(response.json()["translated_text"]) > 0


def test_special_characters_and_punctuation(client):
    text = "Hello! How are you? I'm fine... (great, actually)."
    response = _post(client, text, "en", "zh")
    assert response.status_code == 200
    assert len(response.json()["translated_text"]) > 0


def test_numbers_and_mixed_content(client):
    response = _post(client, "I have 3 cats and 2 dogs.", "en", "zh")
    assert response.status_code == 200
    translated = response.json()["translated_text"]
    assert len(translated) > 0
    assert CHINESE_CHAR_RE.search(translated)


# ── Cloud provider edge cases (mocked) ───────────────────────────────────────

def _cloud_response(text: str) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"content": [{"text": text}]}
    mock.raise_for_status = MagicMock()
    return mock


@pytest.mark.asyncio
async def test_cloud_empty_text_returns_empty_without_api_call():
    provider = AnthropicProvider(model="claude-haiku-4-5-20251001", api_key="sk-ant-test")
    with patch("httpx.AsyncClient.post", new=AsyncMock()) as mock_post:
        result = await provider.translate("", "en", "zh")
    assert result == ""
    mock_post.assert_not_called()
