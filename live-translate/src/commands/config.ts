import { select, input, password, confirm } from '@inquirer/prompts';
import chalk from 'chalk';
import { PROVIDERS, type ProviderKey, type Config } from '../utils/constants.js';
import { saveConfig, loadConfig, maskApiKey, isValidProvider } from '../services/configStore.js';
import { logger } from '../utils/logger.js';

interface ConfigOptions {
  provider?: string;
  model?: string;
  apiKey?: string;
}

async function runInteractiveConfig(): Promise<Config> {
  const existing = loadConfig();

  const provider = await select<ProviderKey>({
    message: 'Choose a translation provider:',
    choices: Object.entries(PROVIDERS).map(([key, def]) => ({
      name: `${def.name} — ${def.description}`,
      value: key as ProviderKey,
    })),
    default: existing.provider,
  });

  const providerDef = PROVIDERS[provider];
  let model: string = providerDef.defaultModel;
  let apiKey = '';
  let ollamaUrl = existing.ollamaUrl;

  if (providerDef.models.length > 1) {
    model = await select<string>({
      message: 'Choose a model:',
      choices: [...providerDef.models].map(m => ({ name: m, value: m })),
      default: providerDef.defaultModel,
    });
  }

  if (providerDef.requiresApiKey) {
    apiKey = await password({
      message: `Enter your ${providerDef.name} API key:`,
      mask: '*',
    });
  }

  if (providerDef.requiresOllama) {
    ollamaUrl = await input({
      message: 'Ollama URL:',
      default: ollamaUrl,
    });
  }

  return { provider, model, apiKey, ollamaUrl };
}

function printSummary(config: Config): void {
  const providerDef = PROVIDERS[config.provider];
  console.log('');
  console.log(`    Provider:  ${providerDef.name}`);
  if (config.model) console.log(`    Model:     ${config.model}`);
  if (config.apiKey) console.log(`    API Key:   ${maskApiKey(config.apiKey)}`);
  if (config.provider === 'ollama') console.log(`    Ollama:    ${config.ollamaUrl}`);
  console.log('');
  console.log('  Run `live-translate start` to start translating.');
  console.log('');
}

export async function runConfig(opts: ConfigOptions): Promise<void> {
  logger.header('Live Translator — Configuration');

  let config: Config;

  if (opts.provider) {
    if (!isValidProvider(opts.provider)) {
      logger.error(`Unknown provider: ${opts.provider}. Valid: ${Object.keys(PROVIDERS).join(', ')}`);
      process.exitCode = 1;
      return;
    }

    const providerDef = PROVIDERS[opts.provider];
    config = {
      provider: opts.provider,
      model: opts.model ?? providerDef.defaultModel,
      apiKey: opts.apiKey ?? '',
      ollamaUrl: 'http://localhost:11434',
    };
  } else {
    config = await runInteractiveConfig();
  }

  saveConfig(config);
  console.log(chalk.green('  ✓ Configuration saved to ~/.live-translate/config.json'));
  printSummary(config);
}
