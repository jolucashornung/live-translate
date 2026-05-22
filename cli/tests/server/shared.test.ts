import { describe, it, expect } from 'vitest';
import { wavBase64ToFloat32, int16ToWavBase64 } from '../../src/server/shared.js';

function makeWavBase64(samples: Int16Array, sampleRate: number): string {
  return int16ToWavBase64(samples, sampleRate);
}

describe('int16ToWavBase64', () => {
  it('produces a non-empty base64 string', () => {
    const pcm = new Int16Array([0, 100, -100, 32767, -32768]);
    const result = int16ToWavBase64(pcm, 16000);
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });

  it('encodes WAV header with correct sample rate', () => {
    const pcm = new Int16Array([1000, 2000]);
    const b64 = int16ToWavBase64(pcm, 22050);
    const buf = Buffer.from(b64, 'base64');
    // sample rate is at bytes 24-27 (little-endian uint32)
    expect(buf.readUInt32LE(24)).toBe(22050);
  });

  it('encodes mono 16-bit PCM in WAV header', () => {
    const pcm = new Int16Array([500]);
    const b64 = int16ToWavBase64(pcm, 16000);
    const buf = Buffer.from(b64, 'base64');
    // num channels: bytes 22-23
    expect(buf.readUInt16LE(22)).toBe(1);
    // bits per sample: bytes 34-35
    expect(buf.readUInt16LE(34)).toBe(16);
  });

  it('starts with RIFF header', () => {
    const pcm = new Int16Array([0]);
    const b64 = int16ToWavBase64(pcm, 16000);
    const buf = Buffer.from(b64, 'base64');
    expect(buf.slice(0, 4).toString('ascii')).toBe('RIFF');
    expect(buf.slice(8, 12).toString('ascii')).toBe('WAVE');
  });
});

describe('wavBase64ToFloat32', () => {
  it('round-trips through int16ToWavBase64 and back', () => {
    const original = new Int16Array([0, 16384, -16384, 32767, -32768]);
    const b64 = int16ToWavBase64(original, 16000);
    const { samples, sampleRate } = wavBase64ToFloat32(b64);

    expect(sampleRate).toBe(16000);
    expect(samples.length).toBe(original.length);
    // Values should be approximately correct (within floating point precision)
    for (let i = 0; i < original.length; i++) {
      const expected = (original[i] ?? 0) / 32768.0;
      expect(samples[i]).toBeCloseTo(expected, 3);
    }
  });

  it('returns the correct sample rate', () => {
    const pcm = new Int16Array([100, 200]);
    const b64 = int16ToWavBase64(pcm, 44100);
    const { sampleRate } = wavBase64ToFloat32(b64);
    expect(sampleRate).toBe(44100);
  });

  it('throws on invalid base64 (buffer too short)', () => {
    // A base64 string that decodes to fewer than 44 bytes
    const shortBuf = Buffer.from('not a wav').toString('base64');
    expect(() => wavBase64ToFloat32(shortBuf)).toThrow(/Invalid WAV/);
  });

  it('round-trip encode → decode → encode produces the same base64', () => {
    const pcm = new Int16Array([1000, -1000, 500, 0, -500]);
    const b64First = int16ToWavBase64(pcm, 16000);
    const { samples } = wavBase64ToFloat32(b64First);

    // Convert float32 back to int16 (approximate)
    const reconstructed = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
      reconstructed[i] = Math.round((samples[i] ?? 0) * 32768);
    }
    const b64Second = int16ToWavBase64(reconstructed, 16000);
    expect(b64Second).toBe(b64First);
  });
});
