"""Article-based chunker for Algerian Journal Officiel PDFs.

Splits legal text by "Article N" / "المادة N" boundaries into
groups of 3-5 articles (400-800 chars per chunk). Falls back to
fixed-size character chunks if no article markers are detected.
"""
import re
from typing import List


ARTICLE_PATTERNS = [
    re.compile(r"Article\s+(\d+)", re.IGNORECASE),
    re.compile(r"المادة\s+(\d+)"),
]

TARGET_CHUNK_SIZE = 600
MIN_CHUNK_SIZE = 400
MAX_CHUNK_SIZE = 800
ARTICLES_PER_GROUP = (3, 5)


def _detect_article_boundaries(text: str) -> list[tuple[int, int, str]]:
    """Find all article headers and return (start_pos, article_number, header_text)."""
    boundaries = []
    for pattern in ARTICLE_PATTERNS:
        for match in pattern.finditer(text):
            boundaries.append((match.start(), int(match.group(1)), match.group(0)))
    boundaries.sort(key=lambda x: x[0])
    return boundaries


def _group_articles(boundaries: list[tuple[int, int, str]], text_length: int) -> list[tuple[int, int]]:
    """Group consecutive article boundaries into chunks of 3-5 articles."""
    if not boundaries:
        return []
    groups = []
    i = 0
    while i < len(boundaries):
        group_size = min(ARTICLES_PER_GROUP[1], len(boundaries) - i)
        if group_size < ARTICLES_PER_GROUP[0]:
            if groups:
                prev = groups.pop()
                start = prev[0]
                end = boundaries[-1][0]
                groups.append((start, end))
            else:
                groups.append((boundaries[i][0], text_length))
            break
        start = boundaries[i][0]
        end = boundaries[i + group_size - 1][0] if i + group_size < len(boundaries) else text_length
        groups.append((start, end))
        i += group_size
    return groups


def _fixed_size_chunks(text: str) -> list[tuple[int, int]]:
    """Fallback: split text into fixed-size chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_SIZE, len(text))
        if end < len(text):
            break_at = text.rfind("\n", start, end)
            if break_at > start:
                end = break_at + 1
        chunks.append((start, end))
        start = end
    return chunks


def chunk_legal_text(text: str, source_pdf: str = "") -> list[dict]:
    """Split legal PDF text into structured chunks.

    Each chunk covers 3-5 articles (or fixed-size fallback).
    Returns list of dicts with keys: content, chunk_index, metadata.
    """
    boundaries = _detect_article_boundaries(text)
    if boundaries:
        groups = _group_articles(boundaries, len(text))
    else:
        groups = _fixed_size_chunks(text)

    chunks = []
    for idx, (start, end) in enumerate(groups):
        content = text[start:end].strip()
        if len(content) < MIN_CHUNK_SIZE and groups != _fixed_size_chunks(text):
            if idx > 0:
                prev = chunks.pop()
                content = prev["content"] + "\n" + content
                start = prev["metadata"]["char_start"]
        if len(content.strip()) < 50:
            continue
        chunk_meta = {
            "source_pdf": source_pdf,
            "char_start": start,
            "char_end": end,
            "chunk_strategy": "article_group" if boundaries else "fixed_size",
            "total_chunks": len(groups),
        }
        chunks.append({
            "content": content[:MAX_CHUNK_SIZE],
            "chunk_index": idx,
            "metadata": chunk_meta,
        })
    return chunks
