#!/usr/bin/env python3
"""Generate test audio fixtures for ASR service tests.

Always generated (no dependencies):
  tone_1s.wav     — 1-second 440 Hz sine wave
  tone_short.wav  — 0.3-second sine wave
  empty.wav       — valid WAV header with 0 frames

Generated with gTTS (requires: pip install gtts, and network access):
  english_speech.mp3  — "Hello, this is a test."
  chinese_speech.mp3  — "你好世界"
"""

import math
import struct
import wave
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent
SAMPLE_RATE = 16000


def _sine_pcm(frequency: float, duration: float) -> bytes:
    num_samples = int(SAMPLE_RATE * duration)
    samples = [
        int(0.5 * math.sin(2 * math.pi * frequency * i / SAMPLE_RATE) * 32767)
        for i in range(num_samples)
    ]
    return struct.pack(f"<{num_samples}h", *samples)


def _write_wav(path: Path, pcm_data: bytes) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


def generate_tones() -> None:
    _write_wav(FIXTURES_DIR / "tone_1s.wav", _sine_pcm(440.0, 1.0))
    _write_wav(FIXTURES_DIR / "tone_short.wav", _sine_pcm(440.0, 0.3))
    _write_wav(FIXTURES_DIR / "empty.wav", b"")
    print("Generated sine wave fixtures.")


def generate_speech() -> None:
    try:
        from gtts import gTTS

        gTTS("Hello, this is a test.", lang="en").save(str(FIXTURES_DIR / "english_speech.mp3"))
        gTTS("你好世界", lang="zh").save(str(FIXTURES_DIR / "chinese_speech.mp3"))
        print("Generated speech fixtures with gTTS.")
    except ImportError:
        print("gTTS not installed — skipping speech fixtures. Install with: pip install gtts")
    except Exception as e:
        print(f"gTTS failed (network required): {e}")


if __name__ == "__main__":
    generate_tones()
    generate_speech()
