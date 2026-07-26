# RAG Pipeline

## Retrieval

```
retrieve_with_pipeline(query, category, top_k, threshold, user_id)
  ├─ [vector] Supabase RPC match against pgvector (HNSW index)   ─┐
  ├─ [BM25]   keyword score over the knowledge base                ├─ run in parallel
  │                                                                 ┘
  → 1. Dedup by content hash
  → 2. Rerank with a cross-encoder if candidate count exceeds top_k
  → 3. Summary injection for sources that overflow the context budget
  → Return formatted context strings
```

Vector and keyword search run concurrently rather than one gating the other - a knowledge base
entry with unusual phrasing but the right keywords still surfaces even if the embedding match is
weak, and vice versa. Reranking only kicks in once there are more candidates than the pipeline
needs, so the common case (few, clearly relevant hits) skips the extra model call entirely.

## Embedding fallback chain

```
paraphrase-multilingual-mpnet-base-v2 (768d)
  → multilingual-e5-large (1024d)
    → bge-small-en-v1.5 (384d)
      → deterministic SHA-256 hash fallback
```

The last step matters more than it looks: if no embedding model is cached and none can be
downloaded, ingestion still completes with a deterministic hash-based vector rather than
crashing. It's a degraded fallback - worse retrieval quality - but the system stays available
instead of failing closed on a missing dependency.

## Memory tiers

| Tier | Storage | Behavior |
|---|---|---|
| Session (short-term) | Redis, in-memory fallback | Last N exchanges, 2h TTL, LLM-summarized on overflow |
| Long-term (user) | Supabase + pgvector | Cosine similarity, 0.7 threshold, capped per user, relevance-weighted (business terms and corrections score higher), oldest/lowest-relevance pruned first, deduped at 0.92 similarity |
| Sticky facts | Supabase | Durable identity facts only (brand, audience, tone, constraints) - injected into every LLM call, exact-match deduped, capped per user |

Sticky facts are deliberately narrow in scope. Long-term memory is for episodic recall; sticky
facts are for things that should be true in every single response regardless of what was asked -
conflating the two tiers degrades both.
