import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.providers.anthropic_provider import AnthropicProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.deepseek_provider import DeepSeekProvider


def _anthropic_response(text: str) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"content": [{"text": text}]}
    mock.raise_for_status = MagicMock()
    return mock


def _openai_response(text: str) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"choices": [{"message": {"content": text}}]}
    mock.raise_for_status = MagicMock()
    return mock


def _rate_limit_response() -> MagicMock:
    mock = MagicMock()
    mock.status_code = 429
    mock.raise_for_status = MagicMock()
    return mock


# ── Anthropic ────────────────────────────────────────────────────────────────

@pytest.fixture
def anthropic():
    return AnthropicProvider(model="claude-haiku-4-5-20251001", api_key="sk-ant-test")


@pytest.mark.asyncio
async def test_anthropic_sends_correct_headers(anthropic):
    resp = _anthropic_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)) as mock_post:
        await anthropic.translate("Hello", "en", "zh")
    headers = mock_post.call_args[1]["headers"]
    assert headers["x-api-key"] == "sk-ant-test"
    assert headers["anthropic-version"] == "2023-06-01"


@pytest.mark.asyncio
async def test_anthropic_sends_correct_request_body(anthropic):
    resp = _anthropic_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)) as mock_post:
        await anthropic.translate("Hello", "en", "zh")
    payload = mock_post.call_args[1]["json"]
    assert payload["model"] == "claude-haiku-4-5-20251001"
    assert payload["max_tokens"] == 1024
    assert payload["messages"][0]["content"] == "Hello"
    assert "English" in payload["system"]
    assert "Mandarin" in payload["system"]


@pytest.mark.asyncio
async def test_anthropic_parses_response(anthropic):
    resp = _anthropic_response("你好，你怎么样？")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)):
        result = await anthropic.translate("Hello, how are you?", "en", "zh")
    assert result == "你好，你怎么样？"


@pytest.mark.asyncio
async def test_anthropic_strips_quotes(anthropic):
    resp = _anthropic_response('"你好"')
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)):
        result = await anthropic.translate("Hello", "en", "zh")
    assert result == "你好"


@pytest.mark.asyncio
async def test_anthropic_retries_on_429(anthropic):
    rate_limit = _rate_limit_response()
    success = _anthropic_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=[rate_limit, success])) as mock_post:
        result = await anthropic.translate("Hello", "en", "zh")
    assert mock_post.call_count == 2
    assert result == "你好"


@pytest.mark.asyncio
async def test_anthropic_empty_text_returns_empty(anthropic):
    result = await anthropic.translate("", "en", "zh")
    assert result == ""


def test_anthropic_raises_without_api_key():
    with pytest.raises(ValueError, match="TRANSLATION_API_KEY"):
        AnthropicProvider(model="claude-haiku-4-5-20251001", api_key="")


# ── OpenAI ───────────────────────────────────────────────────────────────────

@pytest.fixture
def openai_provider():
    return OpenAIProvider(model="gpt-4o-mini", api_key="sk-test")


@pytest.mark.asyncio
async def test_openai_sends_bearer_auth(openai_provider):
    resp = _openai_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)) as mock_post:
        await openai_provider.translate("Hello", "en", "zh")
    headers = mock_post.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer sk-test"


@pytest.mark.asyncio
async def test_openai_sends_correct_body(openai_provider):
    resp = _openai_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)) as mock_post:
        await openai_provider.translate("Hello", "en", "zh")
    payload = mock_post.call_args[1]["json"]
    assert payload["model"] == "gpt-4o-mini"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["content"] == "Hello"


@pytest.mark.asyncio
async def test_openai_parses_response(openai_provider):
    resp = _openai_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)):
        result = await openai_provider.translate("Hello", "en", "zh")
    assert result == "你好"


@pytest.mark.asyncio
async def test_openai_retries_on_429(openai_provider):
    rate_limit = _rate_limit_response()
    success = _openai_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=[rate_limit, success])) as mock_post:
        result = await openai_provider.translate("Hello", "en", "zh")
    assert mock_post.call_count == 2
    assert result == "你好"


def test_openai_raises_without_api_key():
    with pytest.raises(ValueError, match="TRANSLATION_API_KEY"):
        OpenAIProvider(model="gpt-4o-mini", api_key="")


# ── DeepSeek ─────────────────────────────────────────────────────────────────

@pytest.fixture
def deepseek():
    return DeepSeekProvider(model="deepseek-chat", api_key="sk-ds-test")


@pytest.mark.asyncio
async def test_deepseek_uses_openai_compatible_format(deepseek):
    resp = _openai_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)) as mock_post:
        await deepseek.translate("Hello", "en", "zh")
    url = mock_post.call_args[0][0] if mock_post.call_args[0] else mock_post.call_args[1].get("url", "")
    # deepseek.com URL confirms OpenAI-compatible path
    assert "deepseek.com" in url


@pytest.mark.asyncio
async def test_deepseek_parses_choices_format(deepseek):
    resp = _openai_response("你好")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)):
        result = await deepseek.translate("Hello", "en", "zh")
    assert result == "你好"


@pytest.mark.asyncio
async def test_deepseek_strips_markdown(deepseek):
    resp = _openai_response('"""你好"""')
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp)):
        result = await deepseek.translate("Hello", "en", "zh")
    assert result == "你好"


def test_deepseek_raises_without_api_key():
    with pytest.raises(ValueError, match="TRANSLATION_API_KEY"):
        DeepSeekProvider(model="deepseek-chat", api_key="")
