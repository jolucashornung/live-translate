import { spawn, type ChildProcess } from 'child_process';
import { MIN_RECORDING_MS, MAX_RECORDING_MS } from '../utils/constants.js';

export function buildRecordArgs(outputPath: string): string[] {
  return ['-q', '-t', 'wav', '-r', '16000', '-c', '1', '-b', '16', outputPath];
}

export function startRecording(outputPath: string): ChildProcess {
  return spawn('rec', buildRecordArgs(outputPath));
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
