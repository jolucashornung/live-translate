# 001 — MCP Server

## Context

Waxberry is fully local and MIT licensed. The goal is to expand its reach into the Claude ecosystem for reputation building, without abandoning the "fully local, fully private" selling point.

## Decision

Add waxberry as an MCP server so Claude agents (Claude Code, Claude Desktop, custom agents) can call it as a tool. Claude is never in waxberry's runtime path — it remains the *caller*, not a component.

**Why this over alternatives:**
- Claude agents (Option 1): puts Claude in the pipeline, breaks local/private guarantee
- Waxberry as MCP server (Option 2): Claude calls waxberry, waxberry stays dumb and local
- Claude can't do real-time audio I/O at all — waxberry fills a genuine gap

## Design

### New file: `mcp/server.py`

A thin FastMCP wrapper (~50 lines) that proxies calls to the orchestrator's existing REST API. The Docker services — or native TypeScript processes — don't change.

```
Claude agent
    │  calls tool
    ▼
mcp/server.py  (FastMCP, stdio transport)
    │  HTTP POST
    ▼
Orchestrator :8000  (existing, unchanged)
```

### Tools exposed

```python
@mcp.tool()
async def translate_speech(audio_base64: str, sample_rate: int = 16000) -> TranslationResult:
    """Translate speech audio. Returns original text, translation, and synthesised audio."""

@mcp.tool()
async def health_check() -> dict:
    """Check whether all waxberry services are running."""
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
    "waxberry": {
      "command": "uvx",
      "args": ["waxberry-mcp"]
    }
  }
}
```

## Distribution plan

1. Publish `waxberry-mcp` as a minimal PyPI package (just `mcp/` + dependencies)
2. Submit to Anthropic's official MCP server list (PR to docs repo)
3. Submit to `punkpeye/awesome-mcp-servers`
4. Post a demo (GIF or short video) to Anthropic Discord + Claude subreddit

## Acceptance criteria

- [ ] `uvx waxberry-mcp` starts the MCP server without cloning the repo
- [ ] Claude Desktop can call `translate_speech` and receive a valid `TranslationResult`
- [ ] `health_check` returns degraded status if services are not running
- [ ] README has a "Use as MCP server" section with the config snippet
- [ ] Listed in at least one public MCP server registry
