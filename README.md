# Asuq AI

> Marketing intelligence assistant specialized for the Algerian market.

**Asuq AI** is a production-grade, multi-agent AI marketing assistant built on a **LangGraph state machine** with ~18 processing nodes, 9 domain-specific Skill agents, and 11 specialized Slave agents. It features a complete **RAG pipeline** (vector + BM25 + reranker), a **3-tier memory system** (short-term Redis, long-term Supabase/pgvector, sticky facts), **4-layer content moderation**, and **market intelligence collectors** - all tailored for Algeria's multilingual, multi-platform marketing landscape.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-state%20machine-e16462)

---

## How It Works

A user sends a marketing request (in Arabic, French, Darija, or Franco-Arab). The input is normalized and screened for prompt injection. A fast LLM rates query quality - vague queries get quick, direct answers without consuming the full pipeline. Otherwise, the router classifies intent (content creation, competitor analysis, trend monitoring, etc.) and may ask clarifying questions if details are missing. Memory and RAG context are assembled: sticky facts (brand identity, audience) are injected into every LLM call, while semantic search pulls relevant market knowledge from the vector store. A planner decomposes the task into a directed acyclic graph of slave agents (research, strategy, creation, localization, review) that execute in parallel batches via `asyncio.gather`. A quality gate scores the result and loops back for retry on failure - each intent type has its own quality threshold. The synthesized response passes output security screening, facts are persisted to the 3-tier memory system, and a reflection agent extracts lessons for future improvement.

```mermaid
graph TD
    START((START)) --> preprocess
    preprocess --> security_input

    security_input -->|safe| prompt_rating
    security_input -->|blocked| response_formatter

    prompt_rating -->|"rating <= 3"| principal_synthesize
    prompt_rating -->|rating > 3| router

    router -->|simple query| principal_synthesize
    router -->|detail intent| clarify
    router -->|knowledge intent| rag_load
    router -->|low confidence| rag_load
    router -->|default| memory_load

    clarify -->|questions generated| memory_write
    clarify -->|knowledge intent| rag_load
    clarify -->|default| memory_load

    rag_load --> memory_load
    memory_load --> requirements_check

    requirements_check -->|missing info| memory_write
    requirements_check -->|complete| skill_dispatcher

    skill_dispatcher -->|requires_llm| llm_backbone
    skill_dispatcher -->|simple_content| simple_content_plan
    skill_dispatcher -->|direct| principal_plan

    llm_backbone --> principal_plan

    principal_plan -->|has tasks| slave_executor
    principal_plan -->|empty plan| principal_synthesize

    simple_content_plan --> slave_executor

    slave_executor --> quality_gate

    quality_gate -->|"score < threshold<br/>retries < max"| slave_executor
    quality_gate -->|"score >= threshold<br/>or exhausted"| principal_synthesize

    principal_synthesize --> security_output
    security_output --> memory_write
    memory_write --> reflection
    reflection --> END((END))

    response_formatter --> END((END))

    style slave_executor fill:#f9f,stroke:#333,stroke-width:2px
    style quality_gate fill:#f9f,stroke:#333,stroke-width:2px
    style principal_synthesize fill:#bbf,stroke:#333,stroke-width:2px
    style security_input fill:#fbb,stroke:#333,stroke-width:1px
    style security_output fill:#fbb,stroke:#333,stroke-width:1px
```

**Key routing decisions:**

| Edge | Condition | Effect |
|------|-----------|--------|
| `security_input -> response_formatter` | Prompt injection or harmful content detected | Block with polite refusal |
| `prompt_rating -> principal_synthesize` | Rating <= 3 (vague/nonsense query) | Skip full pipeline, quick response |
| `router -> principal_synthesize` | `is_simple=True` (greeting, thanks) | Fast-path, no RAG/planner/agents |
| `router -> clarify` | Detail intent or confidence < 0.3 | Ask user for more information |
| `skill_dispatcher -> llm_backbone` | Skill returns `requires_llm=True` | Format skill output via LLM |
| `skill_dispatcher -> simple_content_plan` | Short content request, no research keywords | Pre-built 2-task plan (bypasses planner LLM) |
| `quality_gate -> slave_executor` | Reviewer score < intent-specific threshold | Retry with feedback from previous pass |
| `quality_gate -> principal_synthesize` | Score OK or max retries exhausted | Proceed (sets `quality_exhausted` flag if retried out) |

---

## Multi-Agent Execution

The planner decomposes a task into a DAG of slave agents. The executor runs each dependency level in parallel via `asyncio.gather`. The quality gate scores the combined output and loops back on failure - this self-correction mechanism is the system's key differentiator.

```mermaid
sequenceDiagram
    participant U as User Request
    participant P as Principal Planner
    participant E as Slave Executor
    participant S as Slave Agents
    participant Q as Quality Gate
    participant Sy as Principal Synthesizer

    U->>P: Intent + context + RAG docs + memory
    P->>P: LLM call to create task plan
    Note over P: Max 5 tasks, approved slaves only,<br/>dependency DAG with auto-repair

    P->>E: Task plan (ordered DAG)

    rect rgb(230, 245, 255)
        Note over E,S: Parallel execution batches
        E->>S: Batch 1: independent tasks (no deps)
        S-->>E: Results
        E->>S: Batch 2: tasks depending on batch 1
        S-->>E: Results
    end

    E->>Q: Combined slave results + reviewer score

    alt Score < threshold AND retries < max
        Q->>E: Retry with feedback from previous pass
        Note over E,S: Re-execute failed tasks with<br/>merged context from prior results
        E->>Q: Updated results
    end

    Q->>Sy: Final results (or quality_exhausted flag)
    Sy->>Sy: LLM synthesis into user response
```

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full graph state machine, node inventory, and routing decisions.

See [docs/rag-pipeline.md](docs/rag-pipeline.md) for multi-strategy retrieval details.

See [docs/moderation.md](docs/moderation.md) for the 4-layer moderation pipeline.

See [docs/darija-nlp.md](docs/darija-nlp.md) for Algerian Arabic NLP preprocessing.

See [docs/landing-pages.md](docs/landing-pages.md) for the landing page generation pipeline.

---

## Code Samples

| Sample | Description |
|--------|-------------|
| [samples/state.py](samples/state.py) | `AsuqState` TypedDict - the shared state definition (~44 fields) |
| [samples/routing_functions.py](samples/routing_functions.py) | Routing / conditional-edge functions - pure control flow, no I/O |
| [samples/slave_base.py](samples/slave_base.py) | `BaseSlave` ABC + `SlaveOutput` dataclass - the slave agent interface |

---

## Skill Agents (9)

| Skill | Purpose | requires_llm |
|-------|---------|:---:|
| `content` | Social media posts, captions, content ideas | Yes |
| `competitor` | Competitor research and market analysis | Yes |
| `ad_copy` | Ad campaigns, marketing scripts, copywriting | Yes |
| `trend_radar` | Market trends, price monitoring, news | Yes |
| `lead_magnet` | Lead generation funnels, offers, landing pages | Yes |
| `pdf` | PDF document analysis with market benchmarks | Yes |
| `web_search` | Web search with domain-specific targeting | No |
| `market_intel` | Market intelligence (runs 4 data collectors in parallel) | No |
| `landing_page` | Product landing pages with copy, layout, and palette | No |

---

## Slave Agents (11)

| Slave | Purpose | Uses LLM |
|-------|---------|:---:|
| `researcher` | Web + RAG research with tool-calling | Yes |
| `strategist` | Marketing strategy development | Yes |
| `creator` | Content creation (primary quality tier) | Yes |
| `localizer` | Cultural adaptation (Arabic/French/Darija mixing) | Yes |
| `reviewer` | Quality rubric scoring (0-10, dimension scores) | Yes |
| `searcher` | Direct web search (no LLM) | No |
| `rag_browser` | Semantic search over curated knowledge base | No |
| `requirements` | Prompt completeness analysis | Yes |
| `reflection` | Post-response quality analysis and lesson extraction | Yes |
| `security_input` | Input safety + prompt injection detection | Conditional |
| `security_output` | Output leak detection (API keys, JWTs, DB URLs) | Conditional |

---

## Quality Thresholds

| Intent | Threshold | Max Passes |
|--------|-----------|------------|
| `content` | 6.0 | 1 |
| `ad_copy` | 6.0 | 1 |
| `competitor` | 7.5 | 1 |
| `trend_radar` | 7.0 | 1 |
| `lead_magnet` | 6.5 | 1 |
| `market_intel` | 7.0 | 1 |

> All max passes are capped by the global `MAX_SELF_CORRECT_PASSES` config (currently 1).

---

## Configuration Numbers

| Setting | Value |
|---------|-------|
| `MAX_RETRIES` | 2 |
| `MAX_SELF_CORRECT_PASSES` | 1 |
| `SHORT_TERM_MEMORY_TTL` | 7200s (2h) |
| `SHORT_TERM_MEMORY_LIMIT` | 10 exchanges |
| `MAX_LONG_TERM_PER_USER` | 200 facts |
| `RAG_THRESHOLD` | 0.6 |
| `RAG_TOP_K` | 3 |
| `MODERATION_LAYER_2_THRESHOLD` | 0.7 |
| `GLOBAL_KNOWLEDGE_TTL_DAYS` | 365 |

---

## License

MIT - see [LICENSE](LICENSE).
