import asyncio
import logging

import torch
from transformers import MarianMTModel, MarianTokenizer

from .base import TranslationProvider

logger = logging.getLogger(__name__)

MAX_INPUT_TOKENS = 512
MAX_NEW_TOKENS = 256


def _deduplicate_repeated_phrases(text: str) -> str:
    """Remove whole-output repetition artifacts from MarianMT (e.g. '你好 你好 你好' → '你好')."""
    tokens = text.split()
    n = len(tokens)
    for length in range(1, n // 2 + 1):
        if n % length == 0 and tokens == tokens[:length] * (n // length):
            return " ".join(tokens[:length])
    return text


class OpusMTProvider(TranslationProvider):
    def __init__(self, model_en_zh: str, model_zh_en: str, device: str | None = None) -> None:
        self._model_en_zh = model_en_zh
        self._model_zh_en = model_zh_en
        self._device_pref = device
        self._models: dict[str, MarianMTModel] = {}
        self._tokenizers: dict[str, MarianTokenizer] = {}
        self.device: str = "cpu"
        self._ready = False

    def load(self) -> None:
        self.device = self._device_pref or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Using device: %s", self.device)

        pairs = [("en→zh", self._model_en_zh), ("zh→en", self._model_zh_en)]
        for pair_key, model_name in pairs:
            logger.info("Loading model %s for %s", model_name, pair_key)
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name).to(self.device)
            model.eval()
            self._tokenizers[pair_key] = tokenizer
            self._models[pair_key] = model
            logger.info("Loaded %s", pair_key)

        self._ready = True

    def provider_name(self) -> str:
        return "opus-mt"

    @property
    def loaded_pairs(self) -> list[str]:
        return list(self._models.keys())

    @property
    def model_names(self) -> str:
        return f"{self._model_en_zh}, {self._model_zh_en}"

    async def health(self) -> dict:
        if not self._ready:
            raise RuntimeError("Models not yet loaded")
        return {
            "status": "ok",
            "provider": self.provider_name(),
            "model": self.model_names,
            "device": self.device,
            "loaded_pairs": self.loaded_pairs,
            "license": "Apache-2.0 (Opus-MT models)",
        }

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text:
            return ""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._translate_sync, text, source_lang, target_lang
        )

    def _translate_sync(self, text: str, source_lang: str, target_lang: str) -> str:
        pair_key = f"{source_lang}→{target_lang}"
        tokenizer = self._tokenizers[pair_key]
        model = self._models[pair_key]

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_INPUT_TOKENS,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                no_repeat_ngram_size=3,
                repetition_penalty=2.0,
            )

        result = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        result = _deduplicate_repeated_phrases(result)
        # MarianMT sometimes generates multiple synonymous phrases; keep only the first.
        for sep in ("!", "！", "。", "？", "?", "."):
            if sep in result:
                return result.split(sep)[0].strip() + sep
        return result
