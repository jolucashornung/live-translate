import * as os from 'node:os';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { pipeline, env } from '@huggingface/transformers';
import { createServer, wavBase64ToFloat32 } from './shared.js';
import type { Routes } from './shared.js';

env.cacheDir = path.join(os.homedir(), '.live-translate', 'models');

const MODEL = 'onnx-community/whisper-base';
const PORT = parseInt(process.env['PORT'] ?? '8001', 10);

const transcriber = await pipeline('automatic-speech-recognition', MODEL, { dtype: 'q8' });

export function detectLanguage(text: string): 'en' | 'zh' {
  const chinese = (text.match(/[一-鿿㐀-䶿]/g) ?? []).length;
  const total = text.replace(/\s/g, '').length;
  return total > 0 && chinese / total > 0.3 ? 'zh' : 'en';
}

export const routes: Routes = {
  'GET /health': async () => ({
    status: 'ok',
    model: MODEL,
    device: 'cpu',
  }),

  'POST /transcribe': async (body) => {
    const req = body as { audio_base64: string; sample_rate: number };
    if (!req.audio_base64) {
      throw new Error('Invalid request: audio_base64 is required');
    }

    const { samples } = wavBase64ToFloat32(req.audio_base64);

    const result = await transcriber(samples);
    const output = Array.isArray(result) ? result[0] : result;
    const text = (output as { text: string }).text?.trim() ?? '';
    const language = detectLanguage(text);

    return { text, language, confidence: 0.95 };
  },
};

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  createServer(routes, PORT);
}
