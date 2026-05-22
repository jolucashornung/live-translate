import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.providers.ollama_provider import OllamaProvider


def _make_chat_response(text: str) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"message": {"content": text}}
    mock.raise_for_status = MagicMock()
    return mock


def _make_tags_response(model: str) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"models": [{"name": model}]}
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def provider():
    return OllamaProvider(model="qwen2.5:7b", url="http://localhost:11434")


@pytest.mark.asyncio
async def test_translate_calls_chat_endpoint(provider):
    chat_resp = _make_chat_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=chat_resp)):
        result = await provider.translate("Hello", "en", "zh")
    assert result == "你好"


@pytest.mark.asyncio
async def test_translate_sends_correct_system_prompt(provider):
    chat_resp = _make_chat_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=chat_resp)) as mock_post:
        await provider.translate("Hello", "en", "zh")
    call_kwargs = mock_post.call_args
    payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
    system_msg = payload["messages"][0]
    assert system_msg["role"] == "system"
    assert "English" in system_msg["content"]
    assert "Mandarin" in system_msg["content"]


@pytest.mark.asyncio
async def test_translate_uses_configured_model(provider):
    chat_resp = _make_chat_response("结果")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=chat_resp)) as mock_post:
        await provider.translate("test", "en", "zh")
    payload = mock_post.call_args[1]["json"]
    assert payload["model"] == "qwen2.5:7b"


@pytest.mark.asyncio
async def test_translate_extracts_response_content(provider):
    chat_resp = _make_chat_response("  翻译结果  ")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=chat_resp)):
        result = await provider.translate("hello", "en", "zh")
    assert result == "翻译结果"


@pytest.mark.asyncio
async def test_translate_empty_text_returns_empty(provider):
    result = await provider.translate("", "en", "zh")
    assert result == ""


@pytest.mark.asyncio
async def test_health_raises_when_ollama_not_running(provider):
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=httpx.ConnectError("refused"))):
        with pytest.raises(RuntimeError, match="not running"):
            await provider.health()


@pytest.mark.asyncio
async def test_health_raises_when_model_not_available():
    provider = OllamaProvider(model="missing-model:7b", url="http://localhost:11434")
    tags_resp = _make_tags_response("qwen2.5:7b")
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=tags_resp)):
        with pytest.raises(RuntimeError, match="not found"):
            await provider.health()


@pytest.mark.asyncio
async def test_health_returns_ok_when_model_available(provider):
    tags_resp = _make_tags_response("qwen2.5:7b")
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=tags_resp)):
        result = await provider.health()
    assert result["status"] == "ok"
    assert result["provider"] == "ollama"
