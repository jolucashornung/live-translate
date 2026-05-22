import logging

import httpx

from .base import TranslationProvider
from ._prompts import LANG_NAMES, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OllamaProvider(TranslationProvider):
    def __init__(self, model: str, url: str) -> None:
        self._model = model
        self._url = url.rstrip("/")

    def provider_name(self) -> str:
        return "ollama"

    async def health(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self._url}/api/tags")
                resp.raise_for_status()
                tags = resp.json()
                available = [m["name"] for m in tags.get("models", [])]
                if not any(self._model in name for name in available):
                    raise RuntimeError(
                        f"Model '{self._model}' not found in Ollama. "
                        f"Run: ollama pull {self._model}"
                    )
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Ollama is not running at {self._url}. Start it with: ollama serve"
            ) from exc

        return {
            "status": "ok",
            "provider": self.provider_name(),
            "model": self._model,
            "device": "gpu" if "gpu" in self._url else "cpu",
            "license": "Apache-2.0",
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
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self._url}/api/chat", json=payload)
            if resp.status_code == 429:
                resp = await client.post(f"{self._url}/api/chat", json=payload)
            resp.raise_for_status()

        return _strip_formatting(resp.json()["message"]["content"])


def _strip_formatting(text: str) -> str:
    text = text.strip()
    for quote in ('"""', "'''", '"', "'"):
        if text.startswith(quote) and text.endswith(quote):
            text = text[len(quote):-len(quote)].strip()
    return text
