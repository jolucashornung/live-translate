import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from .providers.base import TranslationProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.deepseek_provider import DeepSeekProvider
from .providers.m2m100_provider import M2M100Provider
from .providers.ollama_provider import OllamaProvider
from .providers.openai_provider import OpenAIProvider
from .providers.opus_mt_provider import OpusMTProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_PAIRS = {("en", "zh"), ("zh", "en")}


class Settings(BaseSettings):
    translation_provider: str = "opus-mt"
    translation_model: str = ""
    translation_api_key: str = ""
    ollama_url: str = "http://localhost:11434"
    model_en_zh: str = "Helsinki-NLP/opus-mt-en-zh"
    model_zh_en: str = "Helsinki-NLP/opus-mt-zh-en"
    m2m_model: str = "facebook/m2m100_418M"
    device: str | None = None

    model_config = {"env_file": ".env"}


class TranslationRequest(BaseModel):
    text: str
    source_lang: Annotated[str, Field(min_length=2, max_length=10)]
    target_lang: Annotated[str, Field(min_length=2, max_length=10)]


class TranslationResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str


def create_provider(settings: Settings) -> TranslationProvider:
    name = settings.translation_provider
    match name:
        case "ollama":
            model = settings.translation_model or "qwen2.5:7b"
            return OllamaProvider(model=model, url=settings.ollama_url)
        case "anthropic":
            if not settings.translation_model:
                raise ValueError("TRANSLATION_MODEL must be set when using the Anthropic provider")
            return AnthropicProvider(model=settings.translation_model, api_key=settings.translation_api_key)
        case "openai":
            model = settings.translation_model or "gpt-4o-mini"
            return OpenAIProvider(model=model, api_key=settings.translation_api_key)
        case "deepseek":
            model = settings.translation_model or "deepseek-chat"
            return DeepSeekProvider(model=model, api_key=settings.translation_api_key)
        case "m2m100":
            provider = M2M100Provider(
                model_name=settings.m2m_model,
                device=settings.device,
            )
            provider.load()
            return provider
        case "opus-mt":
            provider = OpusMTProvider(
                model_en_zh=settings.model_en_zh,
                model_zh_en=settings.model_zh_en,
                device=settings.device,
            )
            provider.load()
            return provider
        case _:
            raise ValueError(
                f"Unknown provider: {name!r}. "
                "Choose from: ollama, m2m100, anthropic, openai, deepseek, opus-mt"
            )


provider: TranslationProvider | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global provider
    settings = Settings()
    logger.info("Starting translation service with provider: %s", settings.translation_provider)
    provider = create_provider(settings)
    health = await provider.health()
    logger.info("Provider ready: %s", health)
    yield
    provider = None


class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


app = FastAPI(title="Translation Service", lifespan=lifespan, default_response_class=UTF8JSONResponse)


@app.get("/health")
async def health() -> dict:
    if provider is None:
        raise HTTPException(status_code=503, detail="Provider not yet loaded")
    return await provider.health()


@app.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest) -> TranslationResponse:
    if provider is None:
        raise HTTPException(status_code=503, detail="Provider not yet loaded")

    pair = (request.source_lang, request.target_lang)
    if pair not in SUPPORTED_PAIRS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language pair: {request.source_lang} → {request.target_lang}. Supported: en↔zh",
        )

    translated = await provider.translate(request.text, request.source_lang, request.target_lang)
    return TranslationResponse(
        translated_text=translated,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
    )
