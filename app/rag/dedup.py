"""Deterministic deduplication using hashlib.sha256.

Replaces non-deterministic hash() for cross-run stable dedup.
"""

import hashlib
from typing import Any, Dict, List, Set


def content_hash(content: str) -> str:
    """Return a stable SHA-256 hex digest for a content string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def dedup_documents(
    docs: List[Dict[str, Any]],
    key: str = "content",
) -> List[Dict[str, Any]]:
    """Deduplicate a list of document dicts by SHA-256 hash of `key` field.

    First occurrence wins; order is preserved.
    """
    seen: Set[str] = set()
    result: List[Dict[str, Any]] = []
    for doc in docs:
        content = doc.get(key, "")
        if not content:
            continue
        h = content_hash(str(content))
        if h not in seen:
            seen.add(h)
            result.append(doc)
    return result
