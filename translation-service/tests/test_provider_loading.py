import os
import pytest
from unittest.mock import patch

from app.main import create_provider, Settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.m2m100_provider import M2M100Provider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.opus_mt_provider import OpusMTProvider


def _settings(**kwargs) -> Settings:
    defaults = {
        "translation_provider": "opus-mt",
        "translation_model": "",
        "translation_api_key": "",
        "ollama_url": "http://localhost:11434",
        "model_en_zh": "Helsinki-NLP/opus-mt-en-zh",
        "model_zh_en": "Helsinki-NLP/opus-mt-zh-en",
        "device": None,
    }
    defaults.update(kwargs)
    return Settings.model_construct(**defaults)


def test_default_provider_is_opus_mt(opus_mt_provider):
    """conftest loads opus-mt by default — verify provider_name."""
    assert opus_mt_provider.provider_name() == "opus-mt"


def test_opus_mt_settings_loads_opus_mt_provider():
    with patch.object(OpusMTProvider, "load", return_value=None):
        p = create_provider(_settings(translation_provider="opus-mt"))
    assert isinstance(p, OpusMTProvider)


def test_anthropic_settings_loads_anthropic_provider():
    p = create_provider(_settings(
        translation_provider="anthropic",
        translation_model="claude-haiku-4-5-20251001",
        translation_api_key="sk-ant-x",
    ))
    assert isinstance(p, AnthropicProvider)


def test_anthropic_without_model_raises():
    with pytest.raises(ValueError, match="TRANSLATION_MODEL"):
        create_provider(_settings(translation_provider="anthropic", translation_api_key="sk-ant-x"))


def test_anthropic_without_api_key_raises():
    with pytest.raises(ValueError, match="TRANSLATION_API_KEY"):
        create_provider(_settings(
            translation_provider="anthropic",
            translation_model="claude-haiku-4-5-20251001",
            translation_api_key="",
        ))


def test_openai_settings_loads_openai_provider():
    p = create_provider(_settings(translation_provider="openai", translation_api_key="sk-x"))
    assert isinstance(p, OpenAIProvider)


def test_openai_without_api_key_raises():
    with pytest.raises(ValueError, match="TRANSLATION_API_KEY"):
        create_provider(_settings(translation_provider="openai", translation_api_key=""))


def test_deepseek_settings_loads_deepseek_provider():
    p = create_provider(_settings(translation_provider="deepseek", translation_api_key="sk-ds"))
    assert isinstance(p, DeepSeekProvider)


def test_deepseek_without_api_key_raises():
    with pytest.raises(ValueError, match="TRANSLATION_API_KEY"):
        create_provider(_settings(translation_provider="deepseek", translation_api_key=""))


def test_ollama_settings_loads_ollama_provider():
    p = create_provider(_settings(translation_provider="ollama"))
    assert isinstance(p, OllamaProvider)


def test_m2m100_settings_loads_m2m100_provider():
    with patch.object(M2M100Provider, "load", return_value=None):
        p = create_provider(_settings(translation_provider="m2m100"))
    assert isinstance(p, M2M100Provider)


def test_invalid_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        create_provider(_settings(translation_provider="invalid"))


def test_unset_provider_defaults_to_opus_mt():
    with patch.object(OpusMTProvider, "load", return_value=None):
        p = create_provider(_settings())
    assert p.provider_name() == "opus-mt"
