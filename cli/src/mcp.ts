import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const ORCHESTRATOR_URL = process.env["LIVE_TRANSLATE_URL"] ?? "http://localhost:8000";
const TIMEOUT_MS = 60_000;

function fetchWithTimeout(url: string, options: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timer));
}

const server = new Server(
  { name: "live-translate", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "translate_speech",
      description:
        "Translate speech audio between English and Mandarin Chinese. " +
        "Automatically detects the input language and translates to the other. " +
        "Returns original text, translation, and synthesised audio as base64-encoded WAV.",
      inputSchema: {
        type: "object" as const,
        properties: {
          audio_base64: {
            type: "string",
            description: "Base64-encoded WAV audio (16 kHz, mono, 16-bit recommended)",
          },
          sample_rate: {
            type: "number",
            description: "Sample rate of the input audio in Hz (default: 16000)",
          },
        },
        required: ["audio_base64"],
      },
    },
    {
      name: "health_check",
      description:
        "Check whether all waxberry services (ASR, Translation, TTS, Orchestrator) are running and healthy.",
      inputSchema: {
        type: "object" as const,
        properties: {},
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  if (name === "translate_speech") {
    const audioBase64 = typeof args["audio_base64"] === "string" ? args["audio_base64"] : null;
    const sampleRate = typeof args["sample_rate"] === "number" ? args["sample_rate"] : 16000;

    if (!audioBase64) {
      return {
        isError: true,
        content: [{ type: "text" as const, text: "audio_base64 is required" }],
      };
    }

    try {
      const response = await fetchWithTimeout(`${ORCHESTRATOR_URL}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio_base64: audioBase64, sample_rate: sampleRate }),
      });
      const result = await response.json();
      return {
        content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
      };
    } catch (err) {
      return {
        isError: true,
        content: [
          {
            type: "text" as const,
            text: `Failed to reach waxberry orchestrator at ${ORCHESTRATOR_URL}: ${String(err)}`,
          },
        ],
      };
    }
  }

  if (name === "health_check") {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 5_000);
      const response = await fetch(`${ORCHESTRATOR_URL}/health`, {
        signal: controller.signal,
      }).finally(() => clearTimeout(timer));
      const result = await response.json();
      return {
        content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
      };
    } catch (err) {
      return {
        isError: true,
        content: [
          {
            type: "text" as const,
            text: `Waxberry services are not running or unreachable: ${String(err)}`,
          },
        ],
      };
    }
  }

  return {
    isError: true,
    content: [{ type: "text" as const, text: `Unknown tool: ${name}` }],
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
