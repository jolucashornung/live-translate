# Orchestrator Service

Coordinates the full English ↔ Mandarin translation pipeline by chaining ASR → Translation → TTS.

Listens on **port 8000**. No models or dependencies to load at startup — it is a pure coordination layer.

## Pipeline

```
POST /translate
  │
  ├─► ASR :8001 /transcribe       (audio → text + language)
  │
  ├─► Translation :8002 /translate (text → translated text)
  │
  └─► TTS :8003 /synthesize        (translated text → audio)
```

Language routing: `en` → target `zh`, `zh` → target `en`. Anything else returns a structured error at HTTP 200.

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

With Docker:
```bash
docker build -t orchestrator-service .
docker run -p 8000:8000 orchestrator-service
```

The three downstream services must be running (or set `ASR_URL`, `TRANSLATION_URL`, `TTS_URL` to point at them).

## Running tests

Tests mock all downstream services with `respx` — no other services needed.

```bash
pip install -r requirements-dev.txt
pytest
```

## Environment variables

| Variable           | Default                   | Description              |
|--------------------|---------------------------|--------------------------|
| `ASR_URL`          | `http://localhost:8001`   | ASR service base URL     |
| `TRANSLATION_URL`  | `http://localhost:8002`   | Translation service URL  |
| `TTS_URL`          | `http://localhost:8003`   | TTS service base URL     |

## REST API

### GET /health

Pings all three downstream services and aggregates their status.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "services": {
    "asr": {"status": "ok", "model": "base", "device": "cpu"},
    "translation": {"status": "ok", "device": "cpu", "loaded_pairs": ["en→zh", "zh→en"]},
    "tts": {"status": "ok", "engine": "piper", "loaded_voices": ["en", "zh"]}
  }
}
```

If a downstream service is unreachable, `status` becomes `"degraded"` and the affected service entry shows `{"status": "error", "detail": "..."}`. HTTP status is always 200.

### POST /translate

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"audio_base64": "<base64-encoded WAV>", "sample_rate": 16000}'
```

Success response (HTTP 200):
```json
{
  "original_text": "Hello, how are you?",
  "detected_language": "en",
  "translated_text": "你好，你好吗？",
  "target_language": "zh",
  "audio_base64": "<base64-encoded WAV>",
  "mime_type": "audio/wav"
}
```

Error — unsupported language (HTTP 200):
```json
{
  "error": "Unsupported language detected: 'fr'. This translator supports English and Mandarin only.",
  "detected_language": "fr",
  "original_text": "Bonjour"
}
```

Error — no speech detected (HTTP 200):
```json
{
  "error": "No speech detected in the audio.",
  "detected_language": "en"
}
```

Error — downstream service unavailable (HTTP 503):
```json
{"detail": "ASR service unreachable: ..."}
```

Error — downstream service returned an error (HTTP 502):
```json
{"detail": "Translation service error: ..."}
```
