# waxberry — English ↔ 中文

Fully local, real-time speech translator between English and Mandarin Chinese.
No cloud APIs. No data leaves your machine. MIT licensed.

## Install

```bash
npm install -g waxberry
```

## Quick Start

```bash
waxberry doctor   # check prerequisites
waxberry start    # start the translation backend
waxberry          # hold SPACE to speak, release to translate
waxberry stop     # stop the backend when done
```

## How It Works

```
CLI (TypeScript) → Orchestrator → ASR (faster-whisper) → Translation (Opus-MT) → TTS (Piper) → CLI
```

Speech is recorded locally, sent to the orchestrator which chains ASR → translation → TTS, and the
translated audio is played back — all on your machine.

## Prerequisites

- Node.js 18+
- Docker
- Sox (`brew install sox` / `sudo apt install sox`)

Run `waxberry doctor` to verify everything is in place.

## Architecture

| Component    | Language   | License    | Purpose                      |
|--------------|------------|------------|------------------------------|
| CLI          | TypeScript | MIT        | User interface + Docker mgmt |
| Orchestrator | Python     | MIT        | Pipeline coordination        |
| ASR          | Python     | MIT        | Speech → text (Whisper)      |
| Translation  | Python     | Apache 2.0 | Text → text (Opus-MT)        |
| TTS          | Python     | MIT        | Text → speech (Piper)        |

### Service Ports

| Service      | Port |
|--------------|------|
| Orchestrator | 8000 |
| ASR          | 8001 |
| Translation  | 8002 |
| TTS          | 8003 |

## Development

```bash
# Start all backend services (builds images locally)
docker compose up --build

# CLI in dev mode
cd cli && npm run dev
```

### Testing

```bash
make test-unit   # each service independently (no Docker required)
make test-int    # end-to-end pipeline (all services must be running)
make test-all    # both
```

### Project Structure

```
waxberry/
├── cli/                     # TypeScript CLI (npm package)
│   ├── src/
│   ├── docker/
│   │   └── docker-compose.yml   # bundled with npm (uses pre-built images)
│   └── package.json
├── services/
│   ├── asr/                 # faster-whisper, port 8001
│   ├── translation/         # Opus-MT, port 8002
│   ├── tts/                 # Piper TTS, port 8003
│   └── orchestrator/        # FastAPI pipeline, port 8000
├── shared/
│   └── models.py            # Pydantic contracts (source of truth)
├── tests/
│   └── integration/         # end-to-end tests (requires running services)
├── docker-compose.yml       # development: builds from source
└── Makefile
```

## Adding Languages

Each service reads its language configuration from environment variables at startup.
To add a language pair:

1. Add an Opus-MT model for the new pair to `services/translation`
2. Add a Piper voice model to `services/tts/voices/`
3. Update `shared/models.py` if the language enum changes
4. Update the supported pairs set in the orchestrator

## Hardware

| Tier        | RAM   | GPU              | Latency |
|-------------|-------|------------------|---------|
| Minimum     | 8 GB  | None (CPU only)  | ~5 s    |
| Recommended | 16 GB | 6+ GB VRAM       | < 1 s   |

Disk: ~5 GB for models + Docker images.

## License

MIT — see [LICENSE](LICENSE). All model dependencies use MIT or Apache 2.0 licenses.
