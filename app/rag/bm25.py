"""BM25 keyword search strategy (SHOWCASE).

Returns both user-owned + global documents when user_id is set,
consistent with vector search behavior. Illustrative implementation.
"""
from typing import Any, Dict, List, Optional

_KNOWLEDGE_TABLE = "knowledge_base"


def _extract_keywords(query: str) -> List[str]:
    words = query.lower().split()
    return [w for w in words if len(w) > 2]


def _score_document(keywords: List[str], content: str) -> int:
    content_lower = content.lower()
    return sum(1 for kw in keywords if kw in content_lower)


def retrieve_bm25(
    supabase: Any,
    query: str,
    top_k: int = 10,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    keywords = _extract_keywords(query)
    if not keywords:
        return []

    result = (
        supabase.table(_KNOWLEDGE_TABLE)
        .select("*")
        .execute()
    )
    docs = result.data or []

    scored = []
    for doc in docs:
        content = doc.get("content", "") or doc.get("text", "")
        score = _score_document(keywords, content)
        if score > 0:
            scored.append((doc, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored[:top_k]]
