"""TTS microservice — converts text to speech using Piper ONNX models (offline, MIT licensed).

Uses onnxruntime + espeak-ng subprocess to replicate the piper-tts synthesis pipeline
without the piper-phonemize C extension (which lacks macOS ARM wheels).
"""

import asyncio
import base64
import io
import json
import logging
import os
import subprocess
import wave
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VOICE_DIR = Path(os.environ.get("PIPER_VOICE_DIR", "./voices"))

LANGUAGE_VOICE_MAP: dict[str, str] = {
    "en": "en_US-lessac-medium.onnx",
    "zh": "zh_CN-huayan-medium.onnx",
}

MAX_WAV_VALUE = 32767.0


@dataclass
class VoiceConfig:
    sample_rate: int
    espeak_voice: str
    phoneme_id_map: dict[str, list[int]]
    noise_scale: float
    length_scale: float
    noise_w: float
    bos: str | None
    eos: str | None
    pad: str | None


@dataclass
class PiperVoice:
    session: ort.InferenceSession
    config: VoiceConfig

    def synthesize(self, text: str, wav_file: wave.Wave_write) -> None:
        phoneme_ids = _text_to_phoneme_ids(text, self.config)
        audio_bytes = _infer(phoneme_ids, self.session, self.config)
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(self.config.sample_rate)
        wav_file.writeframes(audio_bytes)


class SynthesizeRequest(BaseModel):
    text: str
    language: str
    voice: str | None = None


class SynthesizeResponse(BaseModel):
    audio_base64: str
    mime_type: str


class HealthResponse(BaseModel):
    status: str
    engine: str
    license: str
    loaded_voices: list[str]


class VoicesResponse(BaseModel):
    loaded: dict[str, str]
    available_models: list[str]


def _load_voice_config(config_path: Path) -> VoiceConfig:
    with open(config_path) as f:
        data = json.load(f)
    inference = data.get("inference", {})
    return VoiceConfig(
        sample_rate=data["audio"]["sample_rate"],
        espeak_voice=data["espeak"]["voice"],
        phoneme_id_map=data["phoneme_id_map"],
        noise_scale=inference.get("noise_scale", 0.667),
        length_scale=inference.get("length_scale", 1.0),
        noise_w=inference.get("noise_w", 0.8),
        bos=data.get("bos", "^"),
        eos=data.get("eos", "$"),
        pad=data.get("pad", "_"),
    )


def _load_voices(voice_dir: Path) -> dict[str, PiperVoice]:
    loaded: dict[str, PiperVoice] = {}
    for lang, filename in LANGUAGE_VOICE_MAP.items():
        model_path = voice_dir / filename
        config_path = voice_dir / f"{filename}.json"
        if not model_path.exists() or not config_path.exists():
            logger.warning(f"Voice model not found for '{lang}': {model_path}")
            continue
        logger.info(f"Loading voice for '{lang}': {filename}")
        config = _load_voice_config(config_path)
        session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )
        loaded[lang] = PiperVoice(session=session, config=config)
    return loaded


def _phonemize(text: str, espeak_voice: str) -> str:
    result = subprocess.run(
        ["espeak-ng", "-v", espeak_voice, "--ipa", "-q", "--", text],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"espeak-ng error: {result.stderr.strip()}")
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return " ".join(lines)


def _text_to_phoneme_ids(text: str, config: VoiceConfig) -> list[int]:
    ipa = _phonemize(text, config.espeak_voice)
    ids: list[int] = []

    if config.bos and config.bos in config.phoneme_id_map:
        ids.extend(config.phoneme_id_map[config.bos])

    for char in ipa:
        if char not in config.phoneme_id_map:
            continue
        ids.extend(config.phoneme_id_map[char])
        if config.pad and config.pad in config.phoneme_id_map:
            ids.extend(config.phoneme_id_map[config.pad])

    if config.eos and config.eos in config.phoneme_id_map:
        ids.extend(config.phoneme_id_map[config.eos])

    return ids


def _audio_float_to_int16(audio: np.ndarray) -> np.ndarray:
    # Normalize to [-1, 1] range before converting to int16
    audio_norm = audio * (MAX_WAV_VALUE / max(0.01, float(np.abs(audio).max())))
    return np.clip(audio_norm, -MAX_WAV_VALUE, MAX_WAV_VALUE).astype(np.int16)


def _infer(phoneme_ids: list[int], session: ort.InferenceSession, config: VoiceConfig) -> bytes:
    if not phoneme_ids:
        return np.zeros(1, dtype=np.int16).tobytes()

    text = np.expand_dims(np.array(phoneme_ids, dtype=np.int64), 0)
    text_lengths = np.array([text.shape[1]], dtype=np.int64)
    scales = np.array(
        [config.noise_scale, config.length_scale, config.noise_w],
        dtype=np.float32,
    )

    output = session.run(
        None,
        {
            "input": text,
            "input_lengths": text_lengths,
            "scales": scales,
        },
    )

    audio = output[0].squeeze((0, 1))
    return _audio_float_to_int16(audio).tobytes()


def _synthesize_to_wav(voice: PiperVoice, text: str) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        voice.synthesize(text, wav_file)
    return buf.getvalue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.voices = _load_voices(VOICE_DIR)
    logger.info(f"TTS service ready. Loaded voices: {list(app.state.voices.keys())}")
    yield


app = FastAPI(title="TTS Service", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        engine="piper",
        license="MIT",
        loaded_voices=list(app.state.voices.keys()),
    )


@app.get("/voices", response_model=VoicesResponse)
async def list_voices() -> VoicesResponse:
    loaded = {lang: LANGUAGE_VOICE_MAP[lang] for lang in app.state.voices}
    available_models = [f.name for f in VOICE_DIR.glob("*.onnx")] if VOICE_DIR.exists() else []
    return VoicesResponse(loaded=loaded, available_models=available_models)


@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(request: SynthesizeRequest) -> SynthesizeResponse:
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")

    voices: dict[str, PiperVoice] = app.state.voices

    if request.voice:
        voice = _find_voice_by_filename(voices, request.voice)
        if voice is None:
            raise HTTPException(status_code=400, detail=f"Voice '{request.voice}' is not loaded")
    else:
        voice = voices.get(request.language)
        if voice is None:
            raise HTTPException(
                status_code=400,
                detail=f"No voice loaded for language '{request.language}'",
            )

    loop = asyncio.get_event_loop()
    wav_bytes = await loop.run_in_executor(None, _synthesize_to_wav, voice, request.text)
    return SynthesizeResponse(
        audio_base64=base64.b64encode(wav_bytes).decode("utf-8"),
        mime_type="audio/wav",
    )


def _find_voice_by_filename(voices: dict[str, PiperVoice], filename: str) -> PiperVoice | None:
    for lang, onnx_name in LANGUAGE_VOICE_MAP.items():
        if onnx_name == filename and lang in voices:
            return voices[lang]
    return None
