import { execSync, spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Config } from '../utils/constants.js';

// All paths are functions so os.homedir() is evaluated at call time (testable via mocks).
function getWaxberryHome(): string { return path.join(os.homedir(), '.waxberry'); }
function getPidsDir(): string     { return path.join(getWaxberryHome(), 'pids'); }
function getLogsDir(): string     { return path.join(getWaxberryHome(), 'logs'); }
export function getVoicesDir(): string { return path.join(getWaxberryHome(), 'voices'); }

interface ServiceDef {
  name: string;
  port: number;
  extraEnv?: Record<string, string>;
}

const SERVICE_DEFS: ServiceDef[] = [
  { name: 'translation', port: 8002 },
  { name: 'tts', port: 8003 },
  { name: 'asr', port: 8001 },
  {
    name: 'orchestrator',
    port: 8000,
    extraEnv: {
      ASR_URL: 'http://localhost:8001',
      TRANSLATION_URL: 'http://localhost:8002',
      TTS_URL: 'http://localhost:8003',
    },
  },
];

// Locate the Python services directory.
// Priority: WAXBERRY_SERVICES_DIR env var (set by Homebrew wrapper script)
//           → services/ at the monorepo root (development)
function findServicesDir(): string {
  if (process.env['WAXBERRY_SERVICES_DIR']) {
    return process.env['WAXBERRY_SERVICES_DIR'];
  }
  const thisFile = fileURLToPath(import.meta.url);
  // dist/services/processes.js → ../../.. → repo root → services/
  const dev = path.resolve(path.dirname(thisFile), '..', '..', '..', 'services');
  if (fs.existsSync(dev)) return dev;
  throw new Error(
    'Cannot find waxberry services directory. Install via Homebrew or set WAXBERRY_SERVICES_DIR.'
  );
}

// Locate uvicorn.
// Priority: WAXBERRY_UVICORN env var (set by Homebrew wrapper script)
//           → uvicorn on system PATH
function findUvicorn(): string {
  if (process.env['WAXBERRY_UVICORN']) return process.env['WAXBERRY_UVICORN'];
  try {
    return execSync('which uvicorn', { stdio: 'pipe' }).toString().trim();
  } catch {
    throw new Error('uvicorn not found. Install waxberry with Homebrew: brew install waxberry');
  }
}

function pidFile(name: string): string { return path.join(getPidsDir(), `${name}.pid`); }
function logFile(name: string): string { return path.join(getLogsDir(), `${name}.log`); }

function isProcessRunning(pid: number): boolean {
  try { process.kill(pid, 0); return true; } catch { return false; }
}

function readPid(name: string): number | null {
  const file = pidFile(name);
  if (!fs.existsSync(file)) return null;
  const pid = parseInt(fs.readFileSync(file, 'utf8').trim(), 10);
  return isNaN(pid) ? null : pid;
}

export function voicesExist(): boolean {
  const voicesDir = getVoicesDir();
  return ['en_US-lessac-medium.onnx', 'zh_CN-huayan-medium.onnx'].every(
    f => fs.existsSync(path.join(voicesDir, f))
  );
}

function buildTranslationEnv(config: Config): NodeJS.ProcessEnv {
  return {
    TRANSLATION_PROVIDER: config.provider,
    ...(config.model     ? { TRANSLATION_MODEL:   config.model     } : {}),
    ...(config.apiKey    ? { TRANSLATION_API_KEY: config.apiKey    } : {}),
    ...(config.ollamaUrl ? { OLLAMA_URL:           config.ollamaUrl } : {}),
  };
}

export async function startServices(
  config: Config,
  onProgress?: (msg: string) => void
): Promise<void> {
  const servicesDir = findServicesDir();
  const uvicorn = findUvicorn();

  fs.mkdirSync(getPidsDir(), { recursive: true });
  fs.mkdirSync(getLogsDir(), { recursive: true });

  onProgress?.('Starting services...');

  for (const svc of SERVICE_DEFS) {
    const existing = readPid(svc.name);
    if (existing !== null && isProcessRunning(existing)) continue;

    const env: NodeJS.ProcessEnv = {
      ...process.env,
      PIPER_VOICE_DIR: process.env['PIPER_VOICE_DIR'] ?? getVoicesDir(),
      ...(svc.name === 'translation' ? buildTranslationEnv(config) : {}),
      ...(svc.extraEnv ?? {}),
    };

    const logFd = fs.openSync(logFile(svc.name), 'a');
    const proc = spawn(
      uvicorn,
      ['app.main:app', '--host', '0.0.0.0', '--port', String(svc.port)],
      {
        cwd: path.join(servicesDir, svc.name),
        env,
        detached: true,
        stdio: ['ignore', logFd, logFd],
      }
    );
    proc.unref();
    fs.closeSync(logFd);
    fs.writeFileSync(pidFile(svc.name), String(proc.pid));
  }
}

export async function stopServices(): Promise<void> {
  for (const svc of SERVICE_DEFS) {
    const pid = readPid(svc.name);
    if (pid !== null) {
      try { process.kill(pid, 'SIGTERM'); } catch { /* already dead */ }
      fs.rmSync(pidFile(svc.name), { force: true });
    }
  }
}

export function anyServiceRunning(): boolean {
  return SERVICE_DEFS.some(svc => {
    const pid = readPid(svc.name);
    return pid !== null && isProcessRunning(pid);
  });
}
