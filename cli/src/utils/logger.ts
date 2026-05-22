import chalk from 'chalk';

export const logger = {
  success: (label: string, detail?: string): void => {
    const text = detail ? `${label.padEnd(14)} ${detail}` : label;
    console.log(`  ${chalk.green('✓')} ${text}`);
  },
  error: (label: string, detail?: string): void => {
    const text = detail ? `${label.padEnd(14)} ${detail}` : label;
    console.log(`  ${chalk.red('✗')} ${text}`);
  },
  info: (msg: string): void => {
    console.log(`  ${chalk.blue('ℹ')} ${msg}`);
  },
  warn: (msg: string): void => {
    console.log(`  ${chalk.yellow('⚠')} ${msg}`);
  },
  plain: (msg: string): void => {
    console.log(msg);
  },
  dim: (msg: string): void => {
    console.log(chalk.dim(msg));
  },
  header: (title: string): void => {
    console.log('');
    console.log(chalk.bold(`  ${title}`));
    console.log('');
  },
};
