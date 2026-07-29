"""Main RAG pipeline (SHOWCASE) — multi-strategy retrieval with dedup and rerank.

Combines vector + BM25 results, deduplicates via SHA-256, and optionally
reranks with a cross-encoder before returning formatted context strings.

This is a simplified reference implementation. Production pipeline
has additional strategies, fallbacks, and monitoring.
"""
from typing import Any, Dict, List, Optional

from app.rag.dedup import dedup_documents


def retrieve_with_pipeline(
    supabase: Any,
    query: str,
    embedding: List[float],
    category: str = "regulations",
    top_k: int = 3,
    threshold: float = 0.65,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    docs = _vector_search(supabase, embedding, category, top_k * 2, threshold)
    bm25_docs = _bm25_search(supabase, query, top_k * 2, user_id)

    candidates = docs + bm25_docs
    deduped = dedup_documents(candidates)
    reranked = _rerank_if_needed(deduped, query, top_k)

    return {
        "documents": reranked[:top_k],
        "total_found": len(deduped),
        "total_after_dedup": len(deduped),
    }


def _vector_search(
    supabase: Any,
    embedding: List[float],
    category: str,
    top_k: int,
    threshold: float,
) -> List[Dict[str, Any]]:
    try:
        result = supabase.rpc(
            "match_knowledge",
            {
                "query_embedding": embedding,
                "match_threshold": threshold,
                "match_count": top_k,
                "filter_category": category,
            },
        ).execute()
        return result.data or []
    except Exception:
        return []


def _bm25_search(
    supabase: Any,
    query: str,
    top_k: int,
    user_id: Optional[str],
) -> List[Dict[str, Any]]:
    try:
        from app.rag.bm25 import retrieve_bm25
        return retrieve_bm25(supabase, query, top_k=top_k, user_id=user_id)
    except Exception:
        return []


def _rerank_if_needed(
    docs: List[Dict[str, Any]],
    query: str,
    top_k: int,
) -> List[Dict[str, Any]]:
    if len(docs) <= top_k:
        return docs
    try:
        from sentence_transformers import CrossEncoder
        model_name = "example/reranker-model"
        model = CrossEncoder(model_name)
        pairs = [(query, d.get("content", "") or d.get("text", "")) for d in docs]
        scores = model.predict(pairs)
        scored = list(zip(docs, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored]
    except Exception:
        return docs
