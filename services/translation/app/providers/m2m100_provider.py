import asyncio
import logging

import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

from .base import TranslationProvider

logger = logging.getLogger(__name__)

MAX_INPUT_TOKENS = 512
MAX_NEW_TOKENS = 256

# M2M-100 uses ISO 639-1 codes that match waxberry's internal lang codes directly.
_M2M_LANG_CODES: dict[str, str] = {"en": "en", "zh": "zh"}


class M2M100Provider(TranslationProvider):
    def __init__(self, model_name: str, device: str | None = None) -> None:
        self._model_name = model_name
        self._device_pref = device
        self._tokenizer: M2M100Tokenizer | None = None
        self._model: M2M100ForConditionalGeneration | None = None
        self.device: str = "cpu"
        self._ready = False

    def load(self) -> None:
        self.device = self._device_pref or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Loading M2M-100 model %s on %s", self._model_name, self.device)
        self._tokenizer = M2M100Tokenizer.from_pretrained(self._model_name)
        self._model = M2M100ForConditionalGeneration.from_pretrained(self._model_name).to(self.device)
        self._model.eval()
        self._ready = True
        logger.info("M2M-100 ready")

    def provider_name(self) -> str:
        return "m2m100"

    async def health(self) -> dict:
        if not self._ready:
            raise RuntimeError("M2M-100 model not yet loaded")
        return {
            "status": "ok",
            "provider": self.provider_name(),
            "model": self._model_name,
            "device": self.device,
            "license": "MIT (facebook/m2m100)",
        }

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text:
            return ""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._translate_sync, text, source_lang, target_lang
        )

    def _translate_sync(self, text: str, source_lang: str, target_lang: str) -> str:
        src = _M2M_LANG_CODES[source_lang]
        tgt = _M2M_LANG_CODES[target_lang]

        self._tokenizer.src_lang = src
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_INPUT_TOKENS,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                forced_bos_token_id=self._tokenizer.get_lang_id(tgt),
                max_new_tokens=MAX_NEW_TOKENS,
                no_repeat_ngram_size=3,
                num_beams=4,
            )

        return self._tokenizer.decode(output_ids[0], skip_special_tokens=True)
