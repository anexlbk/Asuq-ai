"""Darija NLP tokenizer — script detection, normalization, confidence scoring.

Externalized term dictionary at franco_dict.json — non-devs can add business terms
without touching Python.
"""
import json
import os
import re
from typing import Dict, List, Optional, Tuple

_FRANCO_DICT: Optional[Dict[str, Dict[str, str]]] = None
_INIT_LOCK = None
_INIT_LOCK_CREATED = False


async def _ensure_loaded():
    global _FRANCO_DICT, _INIT_LOCK, _INIT_LOCK_CREATED
    if _FRANCO_DICT is not None:
        return
    if not _INIT_LOCK_CREATED:
        import asyncio
        _INIT_LOCK = asyncio.Lock()
        _INIT_LOCK_CREATED = True
    async with _INIT_LOCK:
        if _FRANCO_DICT is not None:
            return
        path = os.path.join(os.path.dirname(__file__), "franco_dict.json")
        with open(path, "r", encoding="utf-8") as f:
            _FRANCO_DICT = json.load(f)


def _get_numeral_mappings() -> Dict[str, str]:
    d = _FRANCO_DICT or {}
    return d.get("numeral_mappings", {})


def _get_darija_phrases() -> Dict[str, str]:
    d = _FRANCO_DICT or {}
    return d.get("darija_phrases", {})


PHONE_RE = re.compile(r"(\+?2?1?3?9?\s*[567]\s*\d[\s\d]{6,})")
PRICE_RE = re.compile(r"(\d+[\s,]*[دجدا dinar]{1,5})")


def normalize_franco_text(text: str) -> Tuple[str, float]:
    """Normalize Franco-Arabic text and return (normalized, darija_confidence)."""
    if _FRANCO_DICT is None:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
        except RuntimeError:
            pass
    numerals = _get_numeral_mappings()
    phrases = _get_darija_phrases()

    phone_spans = [(m.start(), m.end()) for m in PHONE_RE.finditer(text)]
    price_spans = [(m.start(), m.end()) for m in PRICE_RE.finditer(text)]
    protected = phone_spans + price_spans

    confidence = 0.0
    matched_terms = 0

    for phrase in phrases:
        if phrase.lower() in text.lower():
            matched_terms += 1
            confidence += 0.15

    short_utterance_boost = 0.0
    word_count = len(text.split())
    if 1 <= word_count <= 3:
        short_utterance_boost = 0.2

    result = []
    i = 0
    while i < len(text):
        protected_span = None
        for ps, pe in protected:
            if i >= ps and i < pe:
                protected_span = (ps, pe)
                break
        if protected_span:
            result.append(text[protected_span[0]:protected_span[1]])
            i = protected_span[1]
            continue

        multi = {k: v for k, v in numerals.items() if len(k) > 1}
        single = {k: v for k, v in numerals.items() if len(k) == 1}
        substituted = False
        for dig, letter in {**multi, **single}.items():
            if text[i:i+len(dig)] == dig:
                result.append(letter)
                i += len(dig)
                confidence += 0.1
                substituted = True
                break
        if not substituted:
            result.append(text[i])
            i += 1

    confidence = min(1.0, confidence + short_utterance_boost)
    return "".join(result), round(confidence, 2)


def detect_script(text: str) -> str:
    """Classify input into arabic, franco, french, english, or mixed."""
    if not text.strip():
        return "unknown"
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06ff' or '\u0750' <= c <= '\u077f')
    latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    numerals_in_text = bool(re.search(r'[37925]', text))
    total = arabic_chars + latin_chars or 1
    arabic_ratio = arabic_chars / total
    if arabic_ratio > 0.3 and latin_chars > 0:
        return "mixed"
    if arabic_ratio > 0.5:
        return "arabic"
    if numerals_in_text and latin_chars > 3:
        return "franco"
    return "english"
