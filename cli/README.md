# waxberry

Real-time English ↔ Mandarin speech translator. Local-first, cloud-optional. Your voice never leaves your machine.

## Install

```bash
npm install -g waxberry
```

## Quick start

```bash
waxberry doctor    # 1. check prerequisites
waxberry config    # 2. choose a provider
waxberry start     # 3. start the backend
waxberry           # 4. start translating (hold SPACE)
```

## Provider comparison

| Provider | Quality | Speed | Cost | Privacy | Needs |
|----------|---------|-------|------|---------|-------|
| Opus-MT | ★★ | ★★★★★ | Free | Fully local | Nothing |
| Ollama | ★★★★ | ★★★ | Free | Fully local | Ollama installed |
| Claude Haiku | ★★★★ | ★★★★ | ~$0.001/use | Text via API | API key |
| Claude Sonnet | ★★★★★ | ★★★ | ~$0.01/use | Text via API | API key |
| GPT-4o-mini | ★★★★ | ★★★★ | ~$0.001/use | Text via API | API key |
| DeepSeek | ★★★★ | ★★★ | ~$0.0005/use | Text via API | API key |

**Privacy model:** ASR (speech-to-text) and TTS (text-to-speech) always run locally. Only the translated *text* is sent to a cloud API when using a cloud provider. Your audio never leaves your machine.

## Commands

```bash
waxberry doctor
  Check Node.js, Docker, Sox, microphone, speaker, and configured provider.

waxberry config
  Interactive provider setup. Saves to ~/.waxberry/config.json.

waxberry config --provider anthropic --model claude-haiku-4-5-20241022 --api-key sk-ant-...
  Non-interactive setup for scripting.

waxberry start
  Start the Docker backend. On first run, downloads ~850 MB of models.

waxberry
  Push-to-talk translation mode. Press SPACE to start/stop recording. Q to quit.

waxberry status
  Show health of all services and active provider.

waxberry stop
  Stop the Docker backend.
```

## Privacy

```
Mic → ASR (local) → text → [Cloud API if configured] → text → TTS (local) → Speaker
                              ↑ only this step is cloud
```

- Opus-MT and Ollama: fully local, nothing leaves your machine.
- Anthropic, OpenAI, DeepSeek: audio stays local; only translated text is sent.

## Prerequisites

- **Node.js** 18+
- **Docker** (with Docker Compose v2)
- **Sox** — `brew install sox` or `apt install sox`

## Troubleshooting

**`waxberry: command not found`** — make sure npm global bin is on your PATH: `npm config get prefix`/bin.

**Sox not found** — install with `brew install sox` (macOS) or `apt install sox` (Ubuntu).

**No microphone detected** — check system permissions for terminal microphone access.

**Services timeout on start** — first run downloads ~850 MB of models. Allow up to 10 minutes.

**Ollama model not pulled** — `waxberry start` will offer to pull it automatically, or run `ollama pull qwen2.5:7b` manually.

## License

MIT
