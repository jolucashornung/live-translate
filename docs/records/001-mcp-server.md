# 001 — MCP Server

## Context

live-translate is fully local and MIT licensed. The goal is to expand its reach into the Claude ecosystem for reputation building, without abandoning the "fully local, fully private" selling point.

## Decision

Add live-translate as an MCP server so Claude agents (Claude Code, Claude Desktop, custom agents) can call it as a tool. Claude is never in live-translate's runtime path — it remains the *caller*, not a component.

**Why this over alternatives:**
- Claude agents (Option 1): puts Claude in the pipeline, breaks local/private guarantee
- live-translate as MCP server (Option 2): Claude calls live-translate, the pipeline stays dumb and local
- Claude can't do real-time audio I/O at all — live-translate fills a genuine gap

## Design

### Implementation: `cli/src/mcp.ts` (bin: `live-translate-mcp`)

A thin MCP server using `@modelcontextprotocol/sdk` (stdio transport) that proxies calls to the orchestrator's existing REST API. Bundled in the `live-translate` npm package alongside the CLI.

```
Claude agent
    │  calls tool
    ▼
cli/src/mcp.ts  (@modelcontextprotocol/sdk, stdio transport)
    │  HTTP POST
    ▼
Orchestrator :8000  (existing, unchanged)
```

### Tools exposed

```typescript
// Translate speech audio. Returns original text, translation, and synthesised audio.
async function translateSpeech(audioBase64: string, sampleRate = 16000): Promise<TranslationResult>

// Check whether all live-translate services are running.
async function healthCheck(): Promise<HealthResult>
```

`TranslationResult` mirrors the orchestrator's existing response schema:
- `original_text`
- `detected_language`
- `translated_text`
- `target_language`
- `audio_base64` (WAV, base64)
- `mime_type`

### Claude Desktop config snippet (for README)

```json
{
  "mcpServers": {
    "live-translate": {
      "command": "npx",
      "args": ["-y", "-p", "live-translate", "live-translate-mcp"]
    }
  }
}
```

Note: `-p live-translate` selects the package; `live-translate-mcp` is the bin entry within it. `live-translate` is a two-bin package — `npx live-translate` runs the CLI, not the MCP server.

## Distribution plan

1. Publish `live-translate` to npm (`cli/` package — includes both CLI and MCP server)
2. Submit to Anthropic's official MCP server list (PR to docs repo)
3. Submit to `punkpeye/awesome-mcp-servers`
4. Post a demo (GIF or short video) to Anthropic Discord + Claude subreddit

## Acceptance criteria

- [x] `npx -p live-translate live-translate-mcp` starts the MCP server without cloning the repo
- [ ] Claude Desktop can call `translate_speech` and receive a valid `TranslationResult`
- [ ] `health_check` returns degraded status if services are not running
- [ ] README has a "Use as MCP server" section with the config snippet
- [ ] Listed in at least one public MCP server registry
