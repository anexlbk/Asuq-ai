# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `samples/state.py`: Shared state definition (~44 fields) for the LangGraph state machine
- `samples/routing_functions.py`: Routing / conditional-edge functions (pure control flow)
- `samples/slave_base.py`: BaseSlave ABC + SlaveOutput dataclass interface
- `docs/architecture.md`: Full graph state machine documentation with node inventory and flow diagram
- `docs/rag-pipeline.md`: Multi-strategy retrieval pipeline (vector + BM25 + reranker)
- `docs/moderation.md`: 4-layer content moderation pipeline
- `docs/darija-nlp.md`: Algerian Arabic NLP preprocessing
- `docs/landing-pages.md`: Landing page generation pipeline (3 passes: vision, copy, review)

### Corrected
- Skill count corrected from 8 (in old table) to 9 (added `landing_page` which now has a working implementation)
- All self-correction max passes documented as capped by global `MAX_SELF_CORRECT_PASSES=1` (previously the per-intent values of 3 for competitor/trend_radar/market_intel were misleading)

### Removed
- Deleted `_showcase_reference.md` from project root (was a working reference, not meant to ship)

## [1.0.0] - 2025-01-01

### Added
- Initial release with LangGraph state machine, 9 skills, 11 slaves
- RAG pipeline (vector + BM25 + reranker)
- 3-tier memory system (Redis + Supabase + sticky facts)
- 4-layer moderation pipeline
- Market intelligence collectors
- Multi-format ingestion (PDF, image, video, text)
