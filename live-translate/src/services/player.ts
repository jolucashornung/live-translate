import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

export async function playAudio(audioBase64: string): Promise<void> {
  const audioBytes = Buffer.from(audioBase64, 'base64');
  const tmpPath = path.join(os.tmpdir(), `live-translate-play-${Date.now()}.wav`);

  fs.writeFileSync(tmpPath, audioBytes);

  return new Promise((resolve, reject) => {
    const proc = spawn('play', ['-q', tmpPath]);

    proc.on('close', (code) => {
      fs.rmSync(tmpPath, { force: true });
      if (code === 0) resolve();
      else reject(new Error(`play exited with code ${code}`));
    });

    proc.on('error', (err) => {
      fs.rmSync(tmpPath, { force: true });
      reject(err);
    });
  });
}
