import { describe, it, expect } from 'vitest';
import path from 'path';
import { buildStartCommand, buildStopCommand, getComposePath } from '../src/services/docker.js';
import { type Config } from '../src/utils/constants.js';

const baseConfig: Config = {
  provider: 'opus-mt',
  model: '',
  apiKey: '',
  ollamaUrl: 'http://localhost:11434',
};

describe('buildStartCommand', () => {
  it('includes TRANSLATION_PROVIDER env var', () => {
    const cmd = buildStartCommand('/path/to/compose.yml', baseConfig);
    expect(cmd).toContain('TRANSLATION_PROVIDER=opus-mt');
  });

  it('omits API key when provider is opus-mt', () => {
    const cmd = buildStartCommand('/path/to/compose.yml', baseConfig);
    expect(cmd).not.toContain('TRANSLATION_API_KEY');
  });

  it('includes API key when provider is cloud-based', () => {
    const config: Config = { ...baseConfig, provider: 'anthropic', model: 'claude-haiku-4-5-20241022', apiKey: 'sk-ant-test' };
    const cmd = buildStartCommand('/path/to/compose.yml', config);
    expect(cmd).toContain('TRANSLATION_API_KEY=sk-ant-test');
  });

  it('includes TRANSLATION_MODEL when model is set', () => {
    const config: Config = { ...baseConfig, provider: 'anthropic', model: 'claude-haiku-4-5-20241022', apiKey: 'sk-ant-test' };
    const cmd = buildStartCommand('/path/to/compose.yml', config);
    expect(cmd).toContain('TRANSLATION_MODEL=claude-haiku-4-5-20241022');
  });

  it('includes OLLAMA_URL when provider is ollama', () => {
    const config: Config = { ...baseConfig, provider: 'ollama', model: 'qwen2.5:7b', ollamaUrl: 'http://localhost:11434' };
    const cmd = buildStartCommand('/path/to/compose.yml', config);
    expect(cmd).toContain('OLLAMA_URL=http://localhost:11434');
  });

  it('includes the compose file path and up -d', () => {
    const composePath = '/some/path/docker-compose.yml';
    const cmd = buildStartCommand(composePath, baseConfig);
    expect(cmd).toContain(`docker compose -f ${composePath} up -d`);
  });
});

describe('buildStopCommand', () => {
  it('produces correct docker compose down command', () => {
    const composePath = '/some/path/docker-compose.yml';
    const cmd = buildStopCommand(composePath);
    expect(cmd).toBe(`docker compose -f ${composePath} down`);
  });
});

describe('getComposePath', () => {
  it('resolves to the bundled docker-compose.yml', () => {
    const composePath = getComposePath();
    expect(composePath).toContain('docker-compose.yml');
    expect(path.isAbsolute(composePath)).toBe(true);
  });
});
