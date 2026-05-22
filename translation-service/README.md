# Translation Service

Text-to-text translation microservice for the waxberry live speech translator project. Translates between English and Mandarin Chinese using a pluggable backend — local models (Opus-MT, M2M-100, Ollama) or cloud APIs (Anthropic, OpenAI, DeepSeek).

## What it does

- Exposes a simple HTTP API consumed by the orchestrator service
- Supports English → Chinese and Chinese → English
- Auto-detects GPU (CUDA) and falls back to CPU
- Loads models on startup and keeps them in memory for low-latency inference

## Choosing a provider

| Provider | Quality | Setup | Notes |
|----------|---------|-------|-------|
| `ollama` | Best | Requires Ollama + `qwen2.5:7b` pull | Recommended for best local quality |
| `m2m100` | Good | ~1.6 GB model download | MIT-licensed; no extra software |
| `opus-mt` | Basic | ~600 MB model download | Default; fast startup |
| `anthropic` / `openai` / `deepseek` | Best | API key required | Cloud; not fully local |

Set `TRANSLATION_PROVIDER` in `.env` (see `.env.example`).

## Run locally

### Prerequisites

- Python 3.11+
- ~600 MB disk space for model downloads (cached after first run)

### Install and start

```bash
cd translation-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

The service downloads the Opus-MT models on first startup. Subsequent starts load from the HuggingFace cache (`~/.cache/huggingface/`).

## Run with Docker

```bash
docker build -t translation-service .
docker run -p 8002:8002 translation-service
```

To use a GPU:

```bash
docker run --gpus all -p 8002:8002 translation-service
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRANSLATION_PROVIDER` | `opus-mt` | Provider: `ollama`, `m2m100`, `anthropic`, `openai`, `deepseek`, `opus-mt` |
| `TRANSLATION_MODEL` | — | Model name (required for `anthropic`; optional for others) |
| `TRANSLATION_API_KEY` | — | API key for cloud providers |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `M2M_MODEL` | `facebook/m2m100_418M` | M2M-100 HuggingFace model ID |
| `MODEL_EN_ZH` | `Helsinki-NLP/opus-mt-en-zh` | Opus-MT model for English → Chinese |
| `MODEL_ZH_EN` | `Helsinki-NLP/opus-mt-zh-en` | Opus-MT model for Chinese → English |
| `DEVICE` | auto | Force `cpu` or `cuda`; auto-detects if unset |

Copy `.env.example` to `.env` and edit as needed.

## Run tests

Models are downloaded once and reused across all tests in the session.

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

First run takes a few minutes while models download. Subsequent runs are fast.

## REST API

### GET /health

Returns service status and loaded model pairs.

**Response 200:**
```json
{
  "status": "ok",
  "device": "cpu",
  "loaded_pairs": ["en→zh", "zh→en"],
  "license": "Apache-2.0 (Opus-MT models)"
}
```

**Response 503:** Models not yet loaded.

---

### POST /translate

Translate text between English and Mandarin Chinese.

**Request:**
```json
{
  "text": "Hello, how are you?",
  "source_lang": "en",
  "target_lang": "zh"
}
```

**Response 200:**
```json
{
  "translated_text": "你好，你好吗？",
  "source_lang": "en",
  "target_lang": "zh"
}
```

**Response 400:** Unsupported language pair (only `en↔zh` supported).

**Response 503:** Models not yet loaded.

Supported `source_lang` / `target_lang` values: `en`, `zh`.

Empty `text` returns an empty `translated_text` without error.

## Model licenses

| Model | License |
|-------|---------|
| Opus-MT (`Helsinki-NLP/opus-mt-*`) | Apache 2.0 |
| M2M-100 (`facebook/m2m100_418M`) | MIT |

This service code is MIT licensed.
