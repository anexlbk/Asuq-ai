# Architecture

## Request flow

```
CLIENT (browser / API client)
        │ HTTP (REST / SSE)
        ▼
FastAPI Application
  /auth/*   /chat/*   /upload   /admin/*
        │
        ▼
LangGraph State Machine (19 nodes)
  START → security_input → prompt_rating → preprocess → router
    → clarify / rag_load → memory_load → requirements_check
    → skill_dispatcher → llm_backbone → principal_plan
    → slave_executor → quality_gate → principal_synthesize
    → security_output → memory_write → reflection → END
        │
        ▼
Skills (9)  |  Slaves (11)  |  RAG Pipeline  |  Memory Manager  |  Collectors (4)
        │
        ▼
Redis (session cache) | Supabase (auth + vector) | Postgres (LangGraph checkpoint)
```

Every node updates a single shared state object as it moves through the graph, and state is
checkpointed to Postgres after each node - so a crash mid-request is recoverable and debuggable
node-by-node, not a black box.

## Node execution flow

```
SECURITY_INPUT
  ├─ Blocked → RESPONSE_FORMATTER → END
  └─ Safe → PROMPT_RATING
              ├─ Rating ≤3 → PRINCIPAL_SYNTHESIZE → SECURITY_OUTPUT → MEMORY_WRITE → REFLECTION → END
              └─ Rating >3 → PREPROCESS → ROUTER
                     ├─ CLARIFY → (questions?) → MEMORY_WRITE → END
                     │            (no questions) → RAG_LOAD → MEMORY_LOAD
                     ├─ RAG_LOAD → MEMORY_LOAD
                     └─ PRINCIPAL_SYNTHESIZE (simple queries)

    MEMORY_LOAD → REQUIREMENTS_CHECK
       ├─ missing info → MEMORY_WRITE → END
       └─ complete → SKILL_DISPATCHER
              ├─ requires_llm → LLM_BACKBONE
              ├─ simple_content → SIMPLE_CONTENT_PLAN
              └─ no LLM → PRINCIPAL_PLAN

    LLM_BACKBONE → PRINCIPAL_PLAN
    SIMPLE_CONTENT_PLAN → SLAVE_EXECUTOR
    PRINCIPAL_PLAN
       ├─ empty plan → PRINCIPAL_SYNTHESIZE
       └─ has tasks → SLAVE_EXECUTOR → QUALITY_GATE
              ├─ score < threshold & retries < max → SLAVE_EXECUTOR (loop)
              └─ score ≥ threshold or exhausted → PRINCIPAL_SYNTHESIZE

    PRINCIPAL_SYNTHESIZE → SECURITY_OUTPUT → MEMORY_WRITE → REFLECTION → END
```

## Routing logic

| Decision point | Routes to | Logic |
|---|---|---|
| after input security | `prompt_rating` / `response_formatter` | Blocked → formatter; safe → rating |
| after prompt rating | `preprocess` / `principal_synthesize` | Rating > 3 → preprocess; ≤ 3 → straight to synthesis |
| after router | `rag_load` / `memory_load` / `clarify` / `principal_synthesize` | Simple query → synthesize; low-detail intent → clarify; confidence < 0.3 → clarify; knowledge intent → rag_load |
| after clarify | `rag_load` / `memory_load` / `memory_write` | Questions generated → memory_write (ask user); else → rag_load |
| after memory load | `requirements_check` / `response_formatter` | Error → formatter; else → requirements |
| after requirements check | `skill_dispatcher` / `memory_write` | Missing info → memory_write (ask user); else → dispatcher |
| after skill dispatch | `llm_backbone` / `principal_plan` / `simple_content_plan` | `requires_llm` → backbone; `is_simple_content` → fast lane; else → planner |
| after principal plan | `slave_executor` / `principal_synthesize` | Empty plan → synthesize directly; has tasks → execute |
| quality gate | `slave_executor` / `principal_synthesize` | Score < threshold and retries remain → loop back; else → synthesize |

A node's output shape change ripples through whichever routing function reads it - that
dependency is checked before any node edit, not after.

> **Note:** This is an architecture showcase. File contents are reference implementations and illustrative examples, not production code.

## Design principles

1. **Fail-closed by default** - security gates block on internal errors (fail-closed, logged),
   never allow potentially harmful content through during a dependency failure.
2. **Token efficiency** - keyword routing before LLM calls; simple-content detection short-
   circuits the planner entirely for low-complexity requests.
3. **Resilience** - every node wrapped in try/except; a single node failure never crashes the
   graph.
4. **Self-correction** - the quality gate loops back to the slave executor with intent-aware
   thresholds and retry caps, not a fixed one-shot generation.
5. **Memory-first** - the clarify node always loads memory before asking questions, so the
   system never re-asks something the user already told it.
6. **Defense in depth** - input security → moderation → output security, three independent
   checkpoints rather than one.
