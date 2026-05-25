# waxberry — English ↔ 中文

Fully local speech-to-speech translator between English and Mandarin Chinese.
No cloud APIs required. All audio processing runs on your machine. MIT licensed.

## Install

```bash
npm install -g waxberry
```

## Quick Start

```bash
waxberry config   # choose a translation provider (runs automatically on first start)
waxberry start    # download models and start backend services
waxberry          # press SPACE to record, SPACE again to translate
waxberry stop     # stop services when done
```

## Commands

| Command | Description |
|---------|-------------|
| `waxberry` | Start translating (SPACE to start/stop recording, Q or Ctrl-C to quit) |
| `waxberry config` | Configure your translation provider |
| `waxberry start` | Download models and start backend services |
| `waxberry stop` | Stop all backend services |
| `waxberry status` | Show service health and active provider |
| `waxberry doctor` | Check prerequisites |

## Translation Providers

Run `waxberry config` to choose a backend. The default is Opus-MT (fully local, no API key needed).

| Provider | Type | Quality | Cost |
|----------|------|---------|------|
| **Opus-MT** *(default)* | Local model | Good | Free |
| **Ollama** (Qwen 2.5) | Local LLM | High | Free — needs ~5 GB RAM |
| **Anthropic (Claude)** | Cloud API | Excellent | ~$0.001/translation |
| **OpenAI** | Cloud API | Excellent | ~$0.001/translation |
| **DeepSeek** | Cloud API | Excellent, strong at Chinese | ~$0.0005/translation |

For cloud providers, audio never leaves your machine — only the transcribed text is sent to the API.

```bash
# Interactive setup
waxberry config

# Or pass flags directly
waxberry config --provider anthropic --api-key sk-ant-...
waxberry config --provider ollama --model qwen2.5:14b
waxberry config --provider deepseek --api-key <key>
```

Configuration is saved to `~/.waxberry/config.json`.

## How It Works

```
Microphone → CLI → ASR (Whisper) → Translation → TTS (Piper) → Speaker
```

Speech is recorded locally. Whisper transcribes it, the configured provider translates the text, and Piper synthesises the audio — the full pipeline runs on your machine except for the translation step when using a cloud provider.

### First Run

`waxberry start` automatically:
1. Downloads Piper voice models (~100 MB, English and Mandarin) to `~/.waxberry/voices/`
2. Installs `sox` and `espeak-ng` if they are not already on your system
3. Starts four backend services as local processes
4. Waits up to 3 minutes for all services to become healthy

Logs are written to `~/.waxberry/logs/`.

## Prerequisites

- Node.js 18+

Run `waxberry doctor` to verify your setup. `sox` and `espeak-ng` are downloaded automatically on first run if missing.

## Architecture

| Component | Port | Language | Purpose |
|-----------|------|----------|---------|
| Orchestrator | 8000 | TypeScript | Pipeline coordination |
| ASR | 8001 | TypeScript | Speech → text (Whisper via @huggingface/transformers) |
| Translation | 8002 | TypeScript | Text → text (configurable provider) |
| TTS | 8003 | TypeScript | Text → speech (Piper) |
| CLI | — | TypeScript | User interface and service management |

Services run as local processes managed by the CLI. State and config live in `~/.waxberry/`.

## Development

```bash
# CLI in dev mode (no build step required)
cd cli && npm run dev

# Build
cd cli && npm run build
```

### Testing

```bash
# Unit tests (no running services required)
cd cli && npm test

# Integration tests (requires waxberry start)
python -m pytest tests/integration/ -v
```

### Project Structure

```
waxberry/
├── cli/                     # TypeScript npm package (the whole product)
│   ├── src/
│   │   ├── commands/        # doctor, config, start, stop, status, translate
│   │   ├── server/          # asr.ts, translation.ts, tts.ts, orchestrator.ts
│   │   ├── services/        # api, processes, recorder, player
│   │   └── utils/           # constants, logger, binaries
│   └── package.json
├── tests/
│   └── integration/         # end-to-end tests (requires running services)
└── docs/
    └── records/             # design decisions and feature specs
```

## Hardware

| Tier | RAM | GPU | Latency |
|------|-----|-----|---------|
| Minimum | 8 GB | None (CPU only) | ~5 s |
| Recommended | 16 GB | 6+ GB VRAM | < 1 s |

Disk: ~3 GB for models and voice files.

## License

MIT — see [LICENSE](LICENSE). All model dependencies use MIT or Apache 2.0 licenses.
