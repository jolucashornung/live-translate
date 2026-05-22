# Live Translator — Claude Code Build Prompts

Six self-contained prompts, one per Claude Code session.
Build in order. Don't start the next until the current one's tests pass.

## Build Order

| File | Component | Language | Why this order |
|------|-----------|----------|----------------|
| `01-translation-service.md` | Translation | Python | Pure text→text. No audio. Fastest to validate. |
| `02-tts-service.md` | TTS | Python | Text→audio. Needed to generate test audio for ASR. |
| `03-asr-service.md` | ASR | Python | Audio→text. Can use TTS output as test fixtures. |
| `04-orchestrator-service.md` | Orchestrator | Python | Chains all three. API only. Tests use mocks. |
| `05-cli-client.md` | CLI | TypeScript | npm-distributable tool. Manages Docker + push-to-talk. |
| `06-integration.md` | Integration | Both | Wires everything together end-to-end. |

## How to Use

1. Open a fresh Claude Code session
2. Feed it the prompt file: `claude < prompts/01-translation-service.md`
3. Wait for it to build and test
4. Verify all tests pass
5. Move to the next file

## Model Downloads

First run of each ML service downloads model weights:
- Translation: ~600 MB (two Opus-MT models)
- TTS: ~100 MB (two Piper voices)
- ASR: ~150 MB (Whisper base)

## Ports

| Service | Port |
|---------|------|
| Orchestrator | 8000 |
| ASR | 8001 |
| Translation | 8002 |
| TTS | 8003 |

## End-User Experience

Once published to npm, the end user just runs:

```bash
npm install -g live-translate
live-translate start
live-translate
```

No Python, no Docker Compose files, no git clone. The CLI manages everything.

## See Also

- `COOKBOOK.md` — detailed step-by-step instructions with prerequisite checks
