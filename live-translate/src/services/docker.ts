import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { type Config } from '../utils/constants.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function getComposePath(): string {
  return path.resolve(__dirname, '../../docker/docker-compose.yml');
}

export function buildStartCommand(composePath: string, config: Config): string {
  const env: Record<string, string> = {
    TRANSLATION_PROVIDER: config.provider,
  };

  if (config.model) env['TRANSLATION_MODEL'] = config.model;
  if (config.apiKey) env['TRANSLATION_API_KEY'] = config.apiKey;
  if (config.ollamaUrl) env['OLLAMA_URL'] = config.ollamaUrl;

  const envPrefix = Object.entries(env)
    .map(([k, v]) => `${k}=${v}`)
    .join(' ');

  return `${envPrefix} docker compose -f ${composePath} up -d`;
}

export function buildStopCommand(composePath: string): string {
  return `docker compose -f ${composePath} down`;
}

export async function startServices(config: Config): Promise<void> {
  const composePath = getComposePath();
  const env: NodeJS.ProcessEnv = { ...process.env, TRANSLATION_PROVIDER: config.provider };

  if (config.model) env['TRANSLATION_MODEL'] = config.model;
  if (config.apiKey) env['TRANSLATION_API_KEY'] = config.apiKey;
  if (config.ollamaUrl) env['OLLAMA_URL'] = config.ollamaUrl;

  return new Promise((resolve, reject) => {
    const proc = spawn('docker', ['compose', '-f', composePath, 'up', '-d'], {
      env,
      stdio: 'pipe',
    });

    let stderr = '';
    proc.stderr?.on('data', (chunk: Buffer) => { stderr += chunk.toString(); });

    proc.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`docker compose up failed (exit ${code}): ${stderr}`));
    });

    proc.on('error', reject);
  });
}

export async function stopServices(): Promise<void> {
  const composePath = getComposePath();

  return new Promise((resolve, reject) => {
    const proc = spawn('docker', ['compose', '-f', composePath, 'down'], { stdio: 'pipe' });

    proc.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`docker compose down failed (exit ${code})`));
    });

    proc.on('error', reject);
  });
}
