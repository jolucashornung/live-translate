import ora from 'ora';
import { stopServices } from '../services/processes.js';
import { logger } from '../utils/logger.js';

export async function runStop(): Promise<void> {
  const spinner = ora('Stopping translation services...').start();

  try {
    await stopServices();
    spinner.succeed('Services stopped.');
  } catch (err) {
    spinner.fail('Failed to stop services');
    logger.error((err as Error).message);
    process.exitCode = 1;
  }
}
