#!/usr/bin/env node
import { Command } from 'commander';
import { runDoctor } from './commands/doctor.js';
import { runConfig } from './commands/config.js';
import { runStart } from './commands/start.js';
import { runStop } from './commands/stop.js';
import { runStatus } from './commands/status.js';
import { runTranslate } from './commands/translate.js';

const program = new Command();

program
  .name('waxberry')
  .description('Real-time English ↔ Mandarin speech translator')
  .version('0.1.0')
  .action(runTranslate);

program
  .command('doctor')
  .description('Check prerequisites (Docker, Sox, microphone, config)')
  .action(runDoctor);

program
  .command('config')
  .description('Interactive provider setup')
  .option('--provider <provider>', 'Translation provider (opus-mt, ollama, anthropic, openai, deepseek)')
  .option('--model <model>', 'Model name')
  .option('--api-key <key>', 'API key')
  .action((opts: { provider?: string; model?: string; apiKey?: string }) =>
    runConfig({ provider: opts.provider, model: opts.model, apiKey: opts.apiKey })
  );

program
  .command('start')
  .description('Start Docker backend services')
  .action(runStart);

program
  .command('stop')
  .description('Stop Docker backend services')
  .action(runStop);

program
  .command('status')
  .description('Show service health and active provider')
  .action(runStatus);

program.parse();
