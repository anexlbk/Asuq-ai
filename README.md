# Asuq AI

Multi-agent AI marketing assistant built for the Algerian market — Darija, French, and Arabic
content generation, backed by a 19-node LangGraph state machine, 9 domain skill agents, 11
specialist slave agents, and a hybrid RAG pipeline.

> **This is a curated architecture showcase, not the production codebase.** The docs describe
> the real system. Code under `samples/` shows interfaces and contracts as public reference
> implementations, written for this repo — not copy-pasted production source.

## Why this exists

Most "AI marketing tools" are a prompt template behind a form. Asuq AI is a stateful multi-agent
system with self-correction, defense-in-depth moderation, and a locale-aware NLP layer for a
market mainstream NLP tooling doesn't serve well — French/Arabic/Darija code-switching,
Franco-Arabic transliteration, marketplace-scale pricing signals.

## Highlights

- **19-node LangGraph state machine** — every request routes through security, quality, and
  self-correction gates instead of a single prompt call. [`docs/architecture.md`](docs/architecture.md)
- **Principal/slave multi-agent orchestration** — a planning agent decomposes work into up to 5
  tasks across 11 specialist slaves (research, strategy, creation, localization, review),
  executed in dependency-ordered batches with a 120s per-batch timeout.
- **Self-correcting quality gate** — intent-aware score thresholds (6.0–7.5 / 10) with bounded
  retry loops; a failed pass's critique feeds directly into the next attempt.
- **Hybrid RAG** — vector (pgvector/HNSW) + BM25 run in parallel, cross-encoder reranked, with a
  3-stage embedding fallback chain so a missing model never breaks ingestion.
  [`docs/rag-pipeline.md`](docs/rag-pipeline.md)
- **4-layer moderation, fail-open by design** — blocklist → toxic classifier → LLM judge →
  injection/credential-leak gate. Security nodes default to allow-through on internal errors
  (logged, never silently swallowed) — a deliberate availability tradeoff, not an oversight.
  [`docs/moderation.md`](docs/moderation.md)
- **Darija-aware NLP** — script detection (Arabic / Franco-Arabic / mixed / French / English) and
  Franco-Arabic digit normalization before anything reaches an LLM.
  [`docs/darija-nlp.md`](docs/darija-nlp.md)
- **3-tier memory** — session (Redis, TTL-bound), long-term (pgvector, relevance-scored, deduped
  at 0.92 similarity), and sticky facts (brand/audience/tone, injected into every call).

## Stack

Python 3.11 · FastAPI · LangGraph · Supabase (Postgres + pgvector) · Redis · Groq + OpenRouter
(multi-provider LLM, tiered by task) · sentence-transformers · BAAI/bge-reranker-v2-m3 ·
Docker Compose

## Repo contents

```
docs/       Architecture, RAG, moderation, and NLP writeups
samples/    Interface-level reference code — state schema, routing logic, agent contracts
LICENSE
```

## Not in this repo

Prompts, skill/slave implementations, database migrations, credentials, and anything touching
real user or market data. This is a showcase of design decisions, not a fork target.
