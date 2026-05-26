# Record 002 — Whisper Native Language Detection

## Problem

Spoken Mandarin was being transcribed as romanised English (e.g. "你好" → "Ni Hao") because
Transformers.js v3 has an unimplemented TODO in `WhisperForConditionalGeneration._retrieve_init_tokens`
(`node_modules/@huggingface/transformers/src/models.js`) that silently defaults to English whenever
no language is specified:

```javascript
if (!language) {
    // TODO: Implement language detection
    console.warn('No language specified - defaulting to English (en).');
    language = 'en';
}
```

The post-hoc character-based `detectLanguage` function then correctly found no Chinese characters
in the romanised output and reported the language as English, so the entire downstream pipeline
(translation, TTS) operated in English mode.

## How Whisper language detection actually works

Whisper's decoder token sequence is:

```
<|startoftranscript|>  <|zh|>  <|transcribe|>  <|notimestamps|>  ...text...
```

To detect language without a full transcription pass, Python Transformers:
1. Runs the encoder on the mel spectrogram features
2. Runs the decoder for **one step** with only `<|startoftranscript|>` as input
3. Reads the logits for the ~100 language-token positions
4. Returns the argmax as the detected language

This costs roughly the same as one encoder pass — far cheaper than a full transcription.

## Solution

We replicate this in `cli/src/server/asr.ts` using the Transformers.js model's existing `generate` API:

```typescript
const output = await pipe.model.generate({
  inputs: input_features,        // encoder input (audio mel spectrogram)
  decoder_input_ids: [SOT],      // [<|startoftranscript|>] — bypasses _retrieve_init_tokens
  max_new_tokens: 1,             // one generate step → the language token
  do_sample: false,
});
const langTokenId = Number(output[0].tolist()[1]);
```

Key mechanism: passing `decoder_input_ids` as a kwarg bypasses `_retrieve_init_tokens` entirely
(checked at `models.js:3479`: `const init_tokens = kwargs.decoder_input_ids ?? this._retrieve_init_tokens(...)`).
With `max_new_tokens: 1`, the loop runs exactly once and the generated token is Whisper's language
prediction. The result is mapped back to `'zh' | 'en'` via `generation_config.lang_to_id`.

The `POST /transcribe` handler then calls `transcriber(samples, { language, task: 'transcribe' })`
**once** with the correct language — no redundant inference pass.

## Alternatives considered

**Two-pass (try Chinese, fall back to English):** Implemented first. Fixed Mandarin recognition but
cost English speakers a full extra Whisper inference pass (~5 s on CPU). Replaced by this approach.

**Dedicated language-ID model:** Would require downloading and loading a separate model.
Not worth the complexity given the single-probe approach works.

## Files changed

- `cli/src/server/asr.ts` — `detectAudioLanguage()` function + updated `POST /transcribe` handler
- `cli/tests/server/asr.test.ts` — mocks for `model.generate`, `processor`, `generation_config`
