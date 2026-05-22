import { execSync } from 'child_process';
import chalk from 'chalk';
import { loadConfig, configExists, maskApiKey, isValidProvider } from '../services/configStore.js';
import { PROVIDERS } from '../utils/constants.js';
import { logger } from '../utils/logger.js';

interface CheckResult {
  label: string;
  passed: boolean;
  detail: string;
}

function tryExec(cmd: string): string | null {
  try {
    return execSync(cmd, { stdio: 'pipe' }).toString().trim();
  } catch {
    return null;
  }
}

function checkNodeVersion(): CheckResult {
  const version = process.version;
  const major = parseInt(version.slice(1).split('.')[0] ?? '0', 10);
  return {
    label: 'Node.js',
    passed: major >= 18,
    detail: `${version} (>= 18 required)`,
  };
}

function checkDocker(): CheckResult {
  const versionOut = tryExec('docker --version');
  if (!versionOut) {
    return { label: 'Docker', passed: false, detail: 'Not installed' };
  }
  const running = tryExec('docker info') !== null;
  const version = versionOut.replace('Docker version ', 'v').split(',')[0] ?? versionOut;
  return {
    label: 'Docker',
    passed: running,
    detail: running ? version : `${version} (not running)`,
  };
}

function checkDockerCompose(): CheckResult {
  const out = tryExec('docker compose version');
  return {
    label: 'Docker Compose',
    passed: out !== null,
    detail: out ? out.replace('Docker Compose version ', 'v') : 'Not available (v2 required)',
  };
}

function checkSox(): CheckResult {
  const out = tryExec('sox --version 2>&1');
  return {
    label: 'Sox',
    passed: out !== null,
    detail: out ?? 'Not installed',
  };
}

function checkMicrophone(): CheckResult {
  const passed = tryExec('rec -n trim 0 0.1 2>&1') !== null;
  return {
    label: 'Microphone',
    passed,
    detail: passed ? 'Default input device found' : 'No input device detected',
  };
}

function checkSpeaker(): CheckResult {
  const passed = tryExec('play -n trim 0 0.1 2>&1') !== null;
  return {
    label: 'Speaker',
    passed,
    detail: passed ? 'Default output device found' : 'No output device detected',
  };
}

function checkConfig(): CheckResult {
  if (!configExists()) {
    return {
      label: 'Config',
      passed: false,
      detail: 'Not configured. Run `live-translate config`',
    };
  }
  const config = loadConfig();
  const providerDef = PROVIDERS[config.provider];
  return {
    label: 'Config',
    passed: true,
    detail: `Provider: ${providerDef.name}${config.model ? ` (${config.model})` : ''}`,
  };
}

function checkApiKey(): CheckResult | null {
  if (!configExists()) return null;
  const config = loadConfig();
  const providerDef = PROVIDERS[config.provider];
  if (!providerDef.requiresApiKey) return null;
  const hasKey = Boolean(config.apiKey);
  return {
    label: 'API Key',
    passed: hasKey,
    detail: hasKey ? maskApiKey(config.apiKey) : `Not set (required for ${providerDef.name})`,
  };
}

function checkOllama(): CheckResult | null {
  if (!configExists()) return null;
  const config = loadConfig();
  if (config.provider !== 'ollama') return null;

  const version = tryExec('ollama --version');
  if (!version) {
    return { label: 'Ollama', passed: false, detail: 'Not installed or not running' };
  }

  const modelList = tryExec('ollama list 2>&1');
  const modelAvailable = modelList?.includes(config.model) ?? false;
  return {
    label: 'Ollama',
    passed: modelAvailable,
    detail: modelAvailable
      ? `${version}, model ${config.model} available`
      : `${version}, model ${config.model} not pulled`,
  };
}

function printResult(result: CheckResult): void {
  const icon = result.passed ? chalk.green('✓') : chalk.red('✗');
  console.log(`  ${icon} ${result.label.padEnd(14)} ${result.detail}`);
}

export async function runDoctor(): Promise<void> {
  logger.header('Live Translator — System Check');

  const checks: CheckResult[] = [
    checkNodeVersion(),
    checkDocker(),
    checkDockerCompose(),
    checkSox(),
    checkMicrophone(),
    checkSpeaker(),
    checkConfig(),
  ];

  const apiKeyCheck = checkApiKey();
  if (apiKeyCheck) checks.push(apiKeyCheck);

  const ollamaCheck = checkOllama();
  if (ollamaCheck) checks.push(ollamaCheck);

  for (const check of checks) {
    printResult(check);
  }

  console.log('');
  const failed = checks.filter(c => !c.passed);

  if (failed.length === 0) {
    console.log(chalk.green('  All checks passed!'));
  } else {
    console.log(chalk.red(`  ${failed.length} check(s) failed.`));
    process.exitCode = 1;
  }

  console.log('');
}
