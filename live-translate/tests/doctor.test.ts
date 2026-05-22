import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import os from 'os';
import path from 'path';

let testHome: string;

vi.mock('os', async (importOriginal) => {
  const actual = await importOriginal<typeof import('os')>();
  return {
    default: {
      ...actual,
      homedir: () => testHome,
    },
  };
});

const mockExecSync = vi.fn();
vi.mock('child_process', () => ({
  execSync: mockExecSync,
  spawn: vi.fn(),
}));

beforeEach(() => {
  testHome = fs.mkdtempSync(path.join(os.tmpdir(), 'live-translate-doctor-test-'));
  vi.spyOn(console, 'log').mockImplementation(() => undefined);
  mockExecSync.mockReset();
  process.exitCode = 0;
});

afterEach(() => {
  fs.rmSync(testHome, { recursive: true, force: true });
  vi.restoreAllMocks();
  process.exitCode = 0;
});

function stubExecSync(responses: Record<string, string>): void {
  mockExecSync.mockImplementation((cmd: string) => {
    for (const [pattern, response] of Object.entries(responses)) {
      if (cmd.includes(pattern)) return Buffer.from(response);
    }
    throw new Error(`Unexpected command: ${cmd}`);
  });
}

async function setupOpusMtConfig(): Promise<void> {
  const { saveConfig } = await import('../src/services/configStore.js');
  saveConfig({ provider: 'opus-mt', model: '', apiKey: '', ollamaUrl: '' });
}

const FULL_PASS_EXECS: Record<string, string> = {
  'docker --version': 'Docker version 24.0.7, build afdd53b',
  'docker info': 'Server Version: 24.0.7',
  'docker compose version': 'Docker Compose version v2.23.0',
  'sox --version': 'SoX v14.4.2',
  'rec -n': '',
  'play -n': '',
};

describe('runDoctor', () => {
  it('Docker check passes when docker is installed and running', async () => {
    await setupOpusMtConfig();
    stubExecSync(FULL_PASS_EXECS);

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    const output = vi.mocked(console.log).mock.calls.flat().join('\n');
    expect(output).toContain('Docker');
    expect(process.exitCode).not.toBe(1);
  });

  it('Docker check fails when docker is not running', async () => {
    await setupOpusMtConfig();
    stubExecSync({
      'docker --version': 'Docker version 24.0.7',
      // 'docker info' missing → throws → docker marked as not running
      'docker compose version': 'Docker Compose version v2.23.0',
      'sox --version': 'SoX v14.4.2',
      'rec -n': '',
      'play -n': '',
    });

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    expect(process.exitCode).toBe(1);
  });

  it('Sox check passes when sox is installed', async () => {
    await setupOpusMtConfig();
    stubExecSync(FULL_PASS_EXECS);

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    const output = vi.mocked(console.log).mock.calls.flat().join('\n');
    expect(output).toContain('Sox');
    expect(output).toContain('SoX v14.4.2');
  });

  it('Sox check fails when sox is not installed', async () => {
    await setupOpusMtConfig();
    stubExecSync({
      'docker --version': 'Docker version 24.0.7',
      'docker info': 'Server',
      'docker compose version': 'Docker Compose version v2.23.0',
      // 'sox --version' missing → fails
      'rec -n': '',
      'play -n': '',
    });

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    expect(process.exitCode).toBe(1);
  });

  it('Config check shows provider name when config exists', async () => {
    const { saveConfig } = await import('../src/services/configStore.js');
    saveConfig({ provider: 'anthropic', model: 'claude-haiku-4-5-20241022', apiKey: 'sk-ant-test', ollamaUrl: '' });

    stubExecSync(FULL_PASS_EXECS);

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    const output = vi.mocked(console.log).mock.calls.flat().join('\n');
    expect(output).toContain('Anthropic (Claude)');
  });

  it('API Key check shows masked key when cloud provider is configured', async () => {
    const { saveConfig } = await import('../src/services/configStore.js');
    saveConfig({ provider: 'anthropic', model: 'claude-haiku-4-5-20241022', apiKey: 'sk-ant-api03-abcdef', ollamaUrl: '' });

    stubExecSync(FULL_PASS_EXECS);

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    const output = vi.mocked(console.log).mock.calls.flat().join('\n');
    expect(output).toContain('...****');
    expect(output).not.toContain('abcdef');
  });

  it('API Key check fails when cloud provider has no key set', async () => {
    const { saveConfig } = await import('../src/services/configStore.js');
    saveConfig({ provider: 'anthropic', model: 'claude-haiku-4-5-20241022', apiKey: '', ollamaUrl: '' });

    stubExecSync(FULL_PASS_EXECS);

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    expect(process.exitCode).toBe(1);
    const output = vi.mocked(console.log).mock.calls.flat().join('\n');
    expect(output).toContain('Not set');
  });

  it('Ollama check verifies model availability when provider is ollama', async () => {
    const { saveConfig } = await import('../src/services/configStore.js');
    saveConfig({ provider: 'ollama', model: 'qwen2.5:7b', apiKey: '', ollamaUrl: 'http://localhost:11434' });

    stubExecSync({
      ...FULL_PASS_EXECS,
      'ollama --version': 'ollama version 0.3.0',
      'ollama list': 'qwen2.5:7b   abc123   4.7 GB',
    });

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    const output = vi.mocked(console.log).mock.calls.flat().join('\n');
    expect(output).toContain('Ollama');
    expect(output).toContain('qwen2.5:7b');
  });

  it('Ollama check fails when model is not pulled', async () => {
    const { saveConfig } = await import('../src/services/configStore.js');
    saveConfig({ provider: 'ollama', model: 'qwen2.5:7b', apiKey: '', ollamaUrl: 'http://localhost:11434' });

    stubExecSync({
      ...FULL_PASS_EXECS,
      'ollama --version': 'ollama version 0.3.0',
      'ollama list': 'NAME   ID   SIZE', // model not in list
    });

    const { runDoctor } = await import('../src/commands/doctor.js');
    await runDoctor();

    expect(process.exitCode).toBe(1);
    const output = vi.mocked(console.log).mock.calls.flat().join('\n');
    expect(output).toContain('not pulled');
  });
});
