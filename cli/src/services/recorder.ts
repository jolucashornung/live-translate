import { spawn, type ChildProcess } from 'child_process';
import fs from 'node:fs';
import { MIN_RECORDING_MS, MAX_RECORDING_MS } from '../utils/constants.js';
import { resolveBinary } from '../utils/binaries.js';

// Resolved once during startup via ensureRecorderReady(); synchronous after that.
let resolvedRec = 'rec';

export function buildRecordArgs(outputPath: string): string[] {
  return ['-q', '-t', 'wav', '-r', '16000', '-c', '1', '-b', '16', outputPath];
}

export async function ensureRecorderReady(
  onProgress?: (msg: string) => void
): Promise<void> {
  const sox = await resolveBinary('sox', onProgress);
  // sox ships a 'rec' symlink alongside the main binary — prefer it.
  const recPath = sox.replace(/([/\\])sox$/, '$1rec');
  try {
    fs.accessSync(recPath, fs.constants.X_OK);
    resolvedRec = recPath;
  } catch {
    // sox binary used directly with --default-device flag
    resolvedRec = sox;
  }
}

export function startRecording(outputPath: string): ChildProcess {
  const isSoxDirect = !resolvedRec.endsWith('rec');
  const args = isSoxDirect
    ? ['-q', '--default-device', '-t', 'wav', '-r', '16000', '-c', '1', '-b', '16', outputPath]
    : ['-q', '-t', 'wav', '-r', '16000', '-c', '1', '-b', '16', outputPath];
  return spawn(resolvedRec, args);
}

export function stopRecording(proc: ChildProcess): void {
  proc.kill('SIGTERM');
}

export function isRecordingTooShort(durationMs: number): boolean {
  return durationMs < MIN_RECORDING_MS;
}

export function isRecordingTooLong(durationMs: number): boolean {
  return durationMs > MAX_RECORDING_MS;
}
