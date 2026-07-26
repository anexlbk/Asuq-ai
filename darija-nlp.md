# Darija-Aware NLP

Algerian users routinely code-switch across Arabic script, French, and Franco-Arabic (Latin
letters with digits standing in for sounds that don't map to the Latin alphabet) — often within
the same message. Standard NLP pipelines built for monolingual or even standard bilingual text
misclassify or mangle this by default.

## Script detection

Every message is classified into one of five categories before it reaches an LLM:

- `arabic` — Arabic script
- `french` — standard French
- `english` — standard English
- `franco` — Franco-Arabic (Latin letters + digit substitutions)
- `mixed` — code-switched across the above within one message

The detected script changes downstream behavior: which language the response is generated in,
which prompt variant is selected, and how chat history gets normalized before it's merged into
the current turn.

## Franco-Arabic digit mapping

Franco-Arabic substitutes digits for Arabic sounds with no Latin equivalent:

| Digit | Arabic letter | Sound |
|---|---|---|
| `3` | ع | ʿayn |
| `7` | ح | ḥa |
| `9` | ق | qaf |
| `2` | أ | hamza |
| `5` | خ | kha |

A message like `3lach ma jawebtch` normalizes through this mapping before intent classification
and RAG retrieval — without it, the digits get treated as literal numbers and the whole
downstream pipeline (routing, retrieval, generation) degrades.

```python
FRANCO_ARABIC_MAP = {
    "3": "ع",
    "7": "ح",
    "9": "ق",
    "2": "أ",
    "5": "خ",
}

def normalize_franco_digits(text: str) -> str:
    """Replace Franco-Arabic digit substitutions with their Arabic letter equivalents."""
    for digit, letter in FRANCO_ARABIC_MAP.items():
        text = text.replace(digit, letter)
    return text
```

This is a simplified illustration of the mapping table, not the production tokenizer — the real
implementation also handles word-boundary detection (so a French message that happens to contain
a digit doesn't get corrupted) and mixed-script segmentation.
