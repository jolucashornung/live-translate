import { describe, it, expect } from 'vitest';
import { buildRecordCommand, isRecordingTooShort, isRecordingTooLong } from '../src/services/recorder.js';

describe('buildRecordCommand', () => {
  it('produces correct sox rec flags', () => {
    const cmd = buildRecordCommand('/tmp/test.wav');
    expect(cmd).toBe('rec -q -t wav -r 16000 -c 1 -b 16 /tmp/test.wav');
  });

  it('includes the output path', () => {
    const cmd = buildRecordCommand('/custom/output.wav');
    expect(cmd).toContain('/custom/output.wav');
  });
});

describe('isRecordingTooShort', () => {
  it('returns true for 300ms (below 500ms threshold)', () => {
    expect(isRecordingTooShort(300)).toBe(true);
  });

  it('returns false for 600ms (above 500ms threshold)', () => {
    expect(isRecordingTooShort(600)).toBe(false);
  });

  it('returns false exactly at threshold (500ms)', () => {
    expect(isRecordingTooShort(500)).toBe(false);
  });

  it('returns true for 0ms', () => {
    expect(isRecordingTooShort(0)).toBe(true);
  });
});

describe('isRecordingTooLong', () => {
  it('returns true for 31000ms (above 30s limit)', () => {
    expect(isRecordingTooLong(31000)).toBe(true);
  });

  it('returns false for 29000ms (below 30s limit)', () => {
    expect(isRecordingTooLong(29000)).toBe(false);
  });

  it('returns false exactly at threshold (30000ms)', () => {
    expect(isRecordingTooLong(30000)).toBe(false);
  });
});
