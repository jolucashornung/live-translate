"""Shared test fixtures for TTS service tests."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

VOICE_DIR = Path(os.environ.get("PIPER_VOICE_DIR", "./voices"))
REQUIRED_VOICES = [
    "en_US-lessac-medium.onnx",
    "en_US-lessac-medium.onnx.json",
    "zh_CN-huayan-medium.onnx",
    "zh_CN-huayan-medium.onnx.json",
]


def voices_present() -> bool:
    return all((VOICE_DIR / v).exists() for v in REQUIRED_VOICES)


SKIP_IF_NO_VOICES = pytest.mark.skipif(
    not voices_present(),
    reason=(
        "Piper voice models not found. "
        "Run `python scripts/download_voices.py` to download them first."
    ),
)


@pytest.fixture(scope="session")
def client():
    if not voices_present():
        pytest.skip(
            "Piper voice models not found. "
            "Run `python scripts/download_voices.py` to download them first."
        )
    from app.main import app
    with TestClient(app) as c:
        yield c
