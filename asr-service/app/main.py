import asyncio
import base64
import binascii
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from faster_whisper import WhisperModel
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "auto")


def _detect_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def _resolve_device() -> str:
    if WHISPER_DEVICE != "auto":
        return WHISPER_DEVICE
    return _detect_device()


def _resolve_compute_type(device: str) -> str:
    if WHISPER_COMPUTE_TYPE != "auto":
        return WHISPER_COMPUTE_TYPE
    return "float16" if device == "cuda" else "int8"


# Primes Whisper toward correct Mandarin character/tone selection while keeping
# English segments recognised. Critical for tonal pairs like 马/妈 and 虎/乎.
_INITIAL_PROMPT = "以下是普通话和英语的双语对话，包含成语、俚语和日常用语。"


def _transcribe(model: WhisperModel, audio_path: str) -> tuple[str, str, float]:
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        initial_prompt=_INITIAL_PROMPT,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    text = " ".join(segment.text for segment in segments).strip()
    return text, info.language, info.language_probability


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = _resolve_device()
    compute_type = _resolve_compute_type(device)
    logger.info("Loading Whisper model '%s' on %s (%s)", WHISPER_MODEL_SIZE, device, compute_type)
    app.state.model = WhisperModel(WHISPER_MODEL_SIZE, device=device, compute_type=compute_type)
    app.state.device = device
    logger.info("Model loaded successfully")
    yield


app = FastAPI(lifespan=lifespan)


class TranscribeRequest(BaseModel):
    audio_base64: str
    sample_rate: int = 16000


class TranscribeResponse(BaseModel):
    text: str
    language: str
    confidence: float


@app.get("/health")
async def health():
    if not hasattr(app.state, "model"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ok", "model": WHISPER_MODEL_SIZE, "device": app.state.device}


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(request: TranscribeRequest):
    if not hasattr(app.state, "model"):
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        audio_bytes = base64.b64decode(request.audio_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Invalid base64 audio data")

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = Path(tmp.name)

    try:
        loop = asyncio.get_running_loop()
        text, language, confidence = await loop.run_in_executor(
            None, _transcribe, app.state.model, str(tmp_path)
        )
    except Exception as e:
        logger.error("Transcription failed: %s", e)
        raise HTTPException(status_code=422, detail="Audio processing failed")
    finally:
        tmp_path.unlink(missing_ok=True)

    return TranscribeResponse(text=text, language=language, confidence=confidence)
