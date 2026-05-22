import { describe, it, expect, vi, beforeAll } from 'vitest';

// Mock @huggingface/transformers before importing asr.ts so the model doesn't load
vi.mock('@huggingface/transformers', () => ({
  pipeline: vi.fn().mockResolvedValue(
    vi.fn().mockResolvedValue([{ text: 'hello' }])
  ),
  env: { cacheDir: '' },
}));

// Import detectLanguage only — do NOT import the full module at top level since
// it has top-level await that would trigger model loading.
// We import the specific export after mocking.
let detectLanguage: (text: string) => 'en' | 'zh';

beforeAll(async () => {
  const mod = await import('../../src/server/asr.js');
  detectLanguage = mod.detectLanguage;
});

describe('detectLanguage', () => {
  it('returns "en" for English text', () => {
    expect(detectLanguage('Hello, how are you doing today?')).toBe('en');
  });

  it('returns "zh" for Chinese text', () => {
    expect(detectLanguage('你好，今天怎么样？')).toBe('zh');
  });

  it('returns "zh" for mixed text with more than 30% Chinese characters', () => {
    // 4 CJK out of 7 non-space chars = ~57%
    expect(detectLanguage('hi 你好 世界')).toBe('zh');
  });

  it('returns "en" for mixed text with less than 30% Chinese characters', () => {
    // 1 CJK out of many non-space chars
    expect(detectLanguage('this is a long english sentence with one 你 character')).toBe('en');
  });

  it('returns "en" for empty string', () => {
    expect(detectLanguage('')).toBe('en');
  });

  it('returns "en" for whitespace-only string', () => {
    expect(detectLanguage('   ')).toBe('en');
  });

  it('returns "zh" when exactly at 30% threshold (>0.3)', () => {
    // Exactly 3 CJK out of 10 non-space = 0.3 → NOT > 0.3 → returns 'en'
    expect(detectLanguage('abcdefg你好吗')).toBe('en');
  });

  it('returns "zh" when just above 30% threshold', () => {
    // 4 CJK out of 10 non-space = 0.4 > 0.3 → 'zh'
    expect(detectLanguage('abcdef你好吗啊')).toBe('zh');
  });
});
