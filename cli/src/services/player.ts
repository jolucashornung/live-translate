import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

// Use platform-native playback where possible to avoid sox dependency for output.
// macOS: afplay (built into every macOS install)
// Linux: sox play (installed as a Homebrew/apt dependency)
function buildPlayArgs(filePath: string): { cmd: string; args: string[] } {
  if (process.platform === 'darwin') {
    return { cmd: 'afplay', args: [filePath] };
  }
  return { cmd: 'play', args: ['-q', filePath] };
}

export async function playAudio(audioBase64: string): Promise<void> {
  const audioBytes = Buffer.from(audioBase64, 'base64');
  const tmpPath = path.join(os.tmpdir(), `waxberry-play-${Date.now()}.wav`);
  fs.writeFileSync(tmpPath, audioBytes);

  const { cmd, args } = buildPlayArgs(tmpPath);

  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args);

    proc.on('close', (code) => {
      fs.rmSync(tmpPath, { force: true });
      if (code === 0) resolve();
      else reject(new Error(`${cmd} exited with code ${code}`));
    });

    proc.on('error', (err) => {
      fs.rmSync(tmpPath, { force: true });
      reject(err);
    });
  });
}
