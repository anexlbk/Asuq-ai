"""Legal document retriever for Algerian law queries (SHOWCASE).

Two-round-trip retrieval:
  1. Vector search via match_knowledge RPC
  2. Separate metadata fetch for citation verification

Table names are illustrative — production uses different naming.
"""
from typing import Any, Dict, List, Optional

from supabase import Client as SupabaseClient

_KNOWLEDGE_TABLE = "knowledge_base"
_MATCH_RPC = "match_knowledge"


def retrieve_legal_documents(
    supabase: SupabaseClient,
    query: str,
    embedding: List[float],
    top_k: int = 10,
    similarity_threshold: float = 0.65,
) -> List[Dict[str, Any]]:
    result = supabase.rpc(
        _MATCH_RPC,
        {
            "query_embedding": embedding,
            "match_threshold": similarity_threshold,
            "match_count": top_k,
            "filter_category": "regulations",
        },
    ).execute()
    return result.data or []


def fetch_legal_metadata(
    supabase: SupabaseClient,
    doc_ids: List[int],
) -> Dict[int, Dict[str, Any]]:
    if not doc_ids:
        return {}
    result = (
        supabase.table(_KNOWLEDGE_TABLE)
        .select("id, doc_metadata")
        .in_("id", doc_ids)
        .execute()
    )
    return {row["id"]: row.get("doc_metadata", {}) for row in (result.data or [])}


def retrieve_for_legal_query(
    supabase: SupabaseClient,
    query: str,
    embedding: List[float],
    top_k: int = 10,
) -> Dict[str, Any]:
    docs = retrieve_legal_documents(supabase, query, embedding, top_k=top_k)
    doc_ids = [d["id"] for d in docs if "id" in d]
    metadata_map = fetch_legal_metadata(supabase, doc_ids)

    for doc in docs:
        doc_id = doc.get("id")
        doc["verified_metadata"] = metadata_map.get(doc_id, {})

    return {
        "documents": docs,
        "metadata_map": metadata_map,
        "total_found": len(docs),
    }
