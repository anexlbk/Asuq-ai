# Darija NLP

Text preprocessing for Algeria's multilingual, multi-script input landscape.

## Challenge

Algerian users communicate in a mix of:
- **Arabic script** (Standard Arabic or Darija)
- **Franco-Arab** (Arabic written in Latin characters with numerals, e.g., "labas" for "lbaraka")
- **French** (widely used in business/education)
- **English** (increasingly common in tech/business)
- **Mixed** (code-switching within a single message)

## Preprocessing Pipeline

Defined in `app/preprocessing/darija_tokenizer.py` (SHOWCASE implementation):

1. **Script classification** - Detect the dominant script type: `arabic`, `franco`, `french`, `english`, or `mixed`
2. **Normalization** - Convert Franco-Arab to standardized form, normalize Unicode, handle common misspellings
3. **Language detection** - Determine response language for the output

The `script_type` is stored in `AsuqState` and used by:
- The router (to select the appropriate skill)
- The clarify node (to generate questions in the right language)
- The response formatter (to set output language)
- Error messages (to respond in the user's language)

## Language Override

Sticky facts can include a `language_override` field (`en` | `fr` | `ar` | `darija`) that forces the response language regardless of input script detection. "darija" is a distinct value from "ar" (MSA) — the LLM backbone, memory manager, and synthesizer all handle it separately to ensure register-aware responses.

## Confidence Scoring

Every utterance receives a `darija_confidence` score (0.0–1.0) computed during preprocessing:
- Franco-Arabic digit presence, known Darija vocabulary matches, and short-utterance boost (≤3 words)
- Phone numbers and prices are preserved (not normalized)
- The score is injected into the LLM system prompt so the model can adjust its register accordingly

## Normalization

Multi-character numerals (3', 7', 9') are processed before single-character mappings to prevent partial replacement. Duplicate numeral mappings are resolved in favor of the most common Darija phoneme.

## Supported Scripts

| Script Type | Detection | Example Input |
|-------------|-----------|---------------|
| `arabic` | Unicode Arabic range | "مرحبا، كيفاش نبداو؟" |
| `franco` | Latin chars + Arabic phonetic patterns | "labas, kifach nbda?" |
| `french` | French keywords/patterns | "Bonjour, comment commencer?" |
| `english` | English keywords/patterns | "Hello, how do I start?" |
| `mixed` | Multiple scripts detected | "Bonjour, labas? كيفاش" |
