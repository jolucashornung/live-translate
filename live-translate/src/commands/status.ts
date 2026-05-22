import chalk from 'chalk';
import { checkHealth } from '../services/api.js';
import { loadConfig, configExists } from '../services/configStore.js';
import { PROVIDERS } from '../utils/constants.js';
import { logger } from '../utils/logger.js';

export async function runStatus(): Promise<void> {
  logger.header('Live Translator — Status');

  const status = await checkHealth();

  if (!status.healthy) {
    console.log(chalk.red('  ✗ Services are not running.'));
    console.log('    Run `live-translate start` to start them.');
    console.log('');
    process.exitCode = 1;
    return;
  }

  for (const service of status.services) {
    const icon = service.healthy ? chalk.green('✓') : chalk.red('✗');
    console.log(`  ${icon} ${service.name.padEnd(14)}`);
  }

  console.log('');

  if (configExists()) {
    const config = loadConfig();
    const providerDef = PROVIDERS[config.provider];
    console.log(`  Provider:  ${config.provider}`);
    if (config.model) console.log(`  Model:     ${config.model}`);
    console.log(`  Privacy:   ${providerDef.local ? 'Fully local' : 'Audio local, text via API'}`);
  }

  console.log('');
}
