# TTS Service

Text-to-speech microservice for the waxberry live translator. Converts text to spoken audio using [Piper TTS](https://github.com/rhasspy/piper) ONNX voice models — fully offline, MIT licensed.

Synthesis pipeline: `espeak-ng` (phonemization) → Piper ONNX model (inference via `onnxruntime`). This replicates the piper-tts package without the `piper-phonemize` C extension, which has no macOS ARM wheels.

Supports English and Mandarin Chinese. Returns base64-encoded WAV audio (22050 Hz, mono, 16-bit).

## System dependency

[espeak-ng](https://github.com/espeak-ng/espeak-ng) must be installed before running the service or tests.

```bash
# macOS
brew install espeak-ng

# Linux / Debian/Ubuntu
apt-get install espeak-ng
```

## Voices

| Language | Model |
|----------|-------|
| English  | `en_US-lessac-medium.onnx` |
| Chinese  | `zh_CN-huayan-medium.onnx` |

Both models are hosted on [Hugging Face rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices). Licence: MIT.

## Quick start

```bash
# 1. Install system dependency
brew install espeak-ng   # macOS; see above for Linux

# 2. Install Python dependencies
pip install -r requirements-dev.txt

# 3. Download voice models (~120 MB total)
python scripts/download_voices.py

# 4. Run the service
uvicorn app.main:app --port 8003
```

## Docker

```bash
docker build -t tts-service .
docker run -p 8003:8003 tts-service
```

The Dockerfile installs `espeak-ng` and downloads voice models at build time so the image is fully self-contained.

## Testing

Voices must be downloaded before running tests (`python scripts/download_voices.py`).

```bash
pytest tests/ -v
```

Tests run real synthesis against actual ONNX models — no mocking.

## REST API

### GET /health

```json
{
  "status": "ok",
  "engine": "piper",
  "license": "MIT",
  "loaded_voices": ["en", "zh"]
}
```

### GET /voices

```json
{
  "loaded": {"en": "en_US-lessac-medium.onnx", "zh": "zh_CN-huayan-medium.onnx"},
  "available_models": ["en_US-lessac-medium.onnx", "zh_CN-huayan-medium.onnx"]
}
```

### POST /synthesize

Request:
```json
{"text": "Hello, how are you?", "language": "en", "voice": null}
```

Response:
```json
{"audio_base64": "<base64 WAV>", "mime_type": "audio/wav"}
```

Returns HTTP 400 if text is empty/whitespace or language has no loaded voice.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PIPER_VOICE_DIR` | `./voices` (local), `/app/voices` (Docker) | Directory containing Piper `.onnx` voice files |

## Licence

Project code: MIT. Piper TTS ONNX models: MIT. espeak-ng: GPL-3.0 (system binary, not bundled). See [CLAUDE.md](../CLAUDE.md) for the full licence table.
