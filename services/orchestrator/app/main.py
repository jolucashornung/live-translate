import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASR_URL = os.getenv("ASR_URL", "http://localhost:8001")
TRANSLATION_URL = os.getenv("TRANSLATION_URL", "http://localhost:8002")
TTS_URL = os.getenv("TTS_URL", "http://localhost:8003")

TIMEOUT = httpx.Timeout(60.0, connect=10.0)
SUPPORTED_LANGUAGES = {"en", "zh"}


class TranslateRequest(BaseModel):
    audio_base64: str
    sample_rate: int = 16000


class TranslateResponse(BaseModel):
    original_text: str
    detected_language: str
    translated_text: str
    target_language: str
    audio_base64: str
    mime_type: str


class ErrorResponse(BaseModel):
    error: str
    detected_language: str
    original_text: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Orchestrator service starting")
    yield
    logger.info("Orchestrator service stopping")


app = FastAPI(lifespan=lifespan)


async def _fetch_service_health(client: httpx.AsyncClient, url: str) -> dict:
    try:
        response = await client.get(f"{url}/health")
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "detail": f"HTTP {response.status_code}"}
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        return {"status": "error", "detail": str(e)}


@app.get("/health")
async def health():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        asr_health, translation_health, tts_health = await asyncio.gather(
            _fetch_service_health(client, ASR_URL),
            _fetch_service_health(client, TRANSLATION_URL),
            _fetch_service_health(client, TTS_URL),
        )

    all_ok = all(
        s.get("status") == "ok" for s in [asr_health, translation_health, tts_health]
    )

    return {
        "status": "ok" if all_ok else "degraded",
        "services": {
            "asr": asr_health,
            "translation": translation_health,
            "tts": tts_health,
        },
    }


async def _call_asr(client: httpx.AsyncClient, audio_base64: str, sample_rate: int) -> dict:
    start = time.monotonic()
    try:
        response = await client.post(
            f"{ASR_URL}/transcribe",
            json={"audio_base64": audio_base64, "sample_rate": sample_rate},
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(status_code=503, detail=f"ASR service unreachable: {e}")
    elapsed_ms = int((time.monotonic() - start) * 1000)
    logger.info("ASR step completed in %d ms", elapsed_ms)
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"ASR service error: {response.text}")
    return response.json()


async def _call_translation(
    client: httpx.AsyncClient, text: str, source_lang: str, target_lang: str
) -> dict:
    start = time.monotonic()
    try:
        response = await client.post(
            f"{TRANSLATION_URL}/translate",
            json={"text": text, "source_lang": source_lang, "target_lang": target_lang},
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(status_code=503, detail=f"Translation service unreachable: {e}")
    elapsed_ms = int((time.monotonic() - start) * 1000)
    logger.info("Translation step completed in %d ms", elapsed_ms)
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Translation service error: {response.text}")
    return response.json()


async def _call_tts(client: httpx.AsyncClient, text: str, language: str) -> dict:
    start = time.monotonic()
    try:
        response = await client.post(
            f"{TTS_URL}/synthesize",
            json={"text": text, "language": language, "voice": None},
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(status_code=503, detail=f"TTS service unreachable: {e}")
    elapsed_ms = int((time.monotonic() - start) * 1000)
    logger.info("TTS step completed in %d ms", elapsed_ms)
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TTS service error: {response.text}")
    return response.json()


@app.post("/translate")
async def translate(request: TranslateRequest):
    pipeline_start = time.monotonic()

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        asr_result = await _call_asr(client, request.audio_base64, request.sample_rate)
        original_text: str = asr_result["text"]
        detected_language: str = asr_result["language"]

        if not original_text.strip():
            return ErrorResponse(
                error="No speech detected in the audio.",
                detected_language=detected_language,
            )

        if detected_language not in SUPPORTED_LANGUAGES:
            return ErrorResponse(
                error=(
                    f"Unsupported language detected: '{detected_language}'. "
                    "This translator supports English and Mandarin only."
                ),
                detected_language=detected_language,
                original_text=original_text,
            )

        target_language = "zh" if detected_language == "en" else "en"

        translation_result = await _call_translation(
            client, original_text, detected_language, target_language
        )
        translated_text: str = translation_result["translated_text"]

        tts_result = await _call_tts(client, translated_text, target_language)

    elapsed_ms = int((time.monotonic() - pipeline_start) * 1000)
    logger.info("Full pipeline completed in %d ms", elapsed_ms)

    return TranslateResponse(
        original_text=original_text,
        detected_language=detected_language,
        translated_text=translated_text,
        target_language=target_language,
        audio_base64=tts_result["audio_base64"],
        mime_type=tts_result["mime_type"],
    )
