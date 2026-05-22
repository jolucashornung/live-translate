import logging

import httpx

from .base import TranslationProvider
from ._prompts import LANG_NAMES, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AnthropicProvider(TranslationProvider):
    def __init__(self, model: str, api_key: str) -> None:
        if not api_key:
            raise ValueError("TRANSLATION_API_KEY is required for the Anthropic provider")
        self._model = model
        self._api_key = api_key

    def provider_name(self) -> str:
        return "anthropic"

    async def health(self) -> dict:
        return {
            "status": "ok",
            "provider": self.provider_name(),
            "model": self._model,
            "device": "n/a",
            "license": "API (bring your own key)",
        }

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text:
            return ""

        system = SYSTEM_PROMPT.format(
            source=LANG_NAMES.get(source_lang, source_lang),
            target=LANG_NAMES.get(target_lang, target_lang),
        )
        payload = {
            "model": self._model,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": text}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages", json=payload, headers=headers
            )
            if resp.status_code == 429:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages", json=payload, headers=headers
                )
            resp.raise_for_status()

        return _strip_formatting(resp.json()["content"][0]["text"])


def _strip_formatting(text: str) -> str:
    text = text.strip()
    for quote in ('"""', "'''", '"', "'"):
        if text.startswith(quote) and text.endswith(quote):
            text = text[len(quote):-len(quote)].strip()
    return text
