"""Legal document retriever for Algerian law queries.

Two-round-trip retrieval:
  1. Vector search via match_dz_knowledge RPC (category="regulations")
  2. Separate legal_metadata fetch for citation verification

Ensures cited articles can be verified against stored metadata
before the LegalExpertSlave uses them in its response.
"""

from typing import Any, Dict, List, Optional

from supabase import Client as SupabaseClient


def retrieve_legal_documents(
    supabase: SupabaseClient,
    query: str,
    embedding: List[float],
    top_k: int = 10,
    similarity_threshold: float = 0.65,
) -> List[Dict[str, Any]]:
    """Retrieve relevant legal documents via vector similarity search.

    Uses the match_dz_knowledge RPC with moderation_status='approved'
    and category='regulations' filters.
    """
    result = supabase.rpc(
        "match_dz_knowledge",
        {
            "query_embedding": embedding,
            "match_threshold": similarity_threshold,
            "match_count": top_k,
            "filter_category": "regulations",
        },
    ).execute()

    docs = result.data or []
    return docs


def fetch_legal_metadata(
    supabase: SupabaseClient,
    doc_ids: List[int],
) -> Dict[int, Dict[str, Any]]:
    """Fetch legal_metadata for the given document IDs.

    Returns dict mapping id -> legal_metadata JSON for citation verification.
    """
    if not doc_ids:
        return {}
    result = (
        supabase.table("dz_knowledge")
        .select("id, legal_metadata")
        .in_("id", doc_ids)
        .execute()
    )
    return {row["id"]: row.get("legal_metadata", {}) for row in (result.data or [])}


def retrieve_for_legal_query(
    supabase: SupabaseClient,
    query: str,
    embedding: List[float],
    top_k: int = 10,
) -> Dict[str, Any]:
    """Full two-round-trip retrieval for a legal query.

    Returns both the documents and their verified metadata.
    """
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
