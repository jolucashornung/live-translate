# ASR Service

Speech-to-text transcription for the waxberry live translator. Accepts base64-encoded audio, returns transcribed text and detected language. Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2-optimized Whisper, MIT licensed). Fully local — no cloud APIs.

## What it does

- Accepts any audio format ffmpeg can read (WAV, WebM, MP3, OGG, etc.)
- Transcribes speech using OpenAI Whisper via faster-whisper
- Detects language automatically, returning `"en"` or `"zh"` for English/Mandarin
- Applies Silero VAD to filter silence and improve accuracy

## Quick start

```bash
docker build -t waxberry-asr .
docker run -p 8001:8001 waxberry-asr
```

Model weights (~150 MB for `base`) download on first run. Cache them with a volume:

```bash
docker run -p 8001:8001 -v whisper-cache:/root/.cache/huggingface waxberry-asr
```

## Running locally (without Docker)

**Prerequisites:** Python 3.11+, [ffmpeg](https://ffmpeg.org/download.html) on PATH.

```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

## Model size options

| Size       | VRAM   | CPU speed   | Accuracy |
|------------|--------|-------------|----------|
| `tiny`     | ~1 GB  | Fast        | Low      |
| `base`     | ~1 GB  | Fast        | Good     |
| `small`    | ~2 GB  | Medium      | Better   |
| `medium`   | ~5 GB  | Slow        | High     |
| `large-v3` | ~10 GB | Very slow   | Best     |

Default: `base` — good balance for CPU inference.

## Environment variables

| Variable               | Default | Description                                     |
|------------------------|---------|-------------------------------------------------|
| `WHISPER_MODEL_SIZE`   | `base`  | Model size: tiny, base, small, medium, large-v3 |
| `WHISPER_DEVICE`       | `auto`  | Device: cpu, cuda, auto                         |
| `WHISPER_COMPUTE_TYPE` | `auto`  | Precision: int8, float16, auto                  |

`auto` device selects CUDA if available, otherwise CPU.
`auto` compute type uses `float16` on CUDA and `int8` on CPU.

## REST API

### GET /health

```json
{"status": "ok", "model": "base", "device": "cpu"}
```

### POST /transcribe

**Request:**
```json
{"audio_base64": "<base64-encoded audio bytes>", "sample_rate": 16000}
```

**Response:**
```json
{"text": "Hello, how are you today?", "language": "en", "confidence": 0.95}
```

**Error responses:**
- `400` — invalid base64 input
- `422` — audio decoding failed (not a valid audio file)
- `503` — model not loaded

## Running tests

```bash
# Install dev dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Generate test fixtures
python tests/fixtures/generate_test_audio.py

# Run all tests (downloads Whisper base model ~150 MB on first run)
pytest -v
```

## Generating test fixtures

```bash
# Sine wave fixtures — no dependencies
python tests/fixtures/generate_test_audio.py

# Real speech fixtures — requires gtts and network access
pip install gtts
python tests/fixtures/generate_test_audio.py
```

Generated files in `tests/fixtures/`:

| File                  | Contents                           | Dependencies      |
|-----------------------|------------------------------------|-------------------|
| `tone_1s.wav`         | 1-second 440 Hz sine wave          | none              |
| `tone_short.wav`      | 0.3-second sine wave               | none              |
| `empty.wav`           | Valid WAV header, 0 audio frames   | none              |
| `english_speech.mp3`  | "Hello, this is a test."           | gtts + network    |
| `chinese_speech.mp3`  | "你好世界"                          | gtts + network    |

Language-detection tests skip automatically if speech fixtures are absent.

## License

MIT
