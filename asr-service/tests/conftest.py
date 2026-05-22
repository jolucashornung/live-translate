import base64
import io
import math
import struct
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_sine_wav(frequency: float = 440.0, duration: float = 1.0, sample_rate: int = 16000) -> bytes:
    num_samples = int(sample_rate * duration)
    samples = [
        int(0.5 * math.sin(2 * math.pi * frequency * i / sample_rate) * 32767)
        for i in range(num_samples)
    ]
    pcm = struct.pack(f"<{num_samples}h", *samples)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def _make_empty_wav(sample_rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"")
    return buf.getvalue()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def sine_wave_b64() -> str:
    return base64.b64encode(_make_sine_wav(440.0, 1.0)).decode()


@pytest.fixture(scope="session")
def short_wav_b64() -> str:
    return base64.b64encode(_make_sine_wav(440.0, 0.3)).decode()


@pytest.fixture(scope="session")
def empty_wav_b64() -> str:
    return base64.b64encode(_make_empty_wav()).decode()


@pytest.fixture(scope="session")
def english_speech_b64() -> str | None:
    path = FIXTURES_DIR / "english_speech.mp3"
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    return None


@pytest.fixture(scope="session")
def chinese_speech_b64() -> str | None:
    path = FIXTURES_DIR / "chinese_speech.mp3"
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    return None
