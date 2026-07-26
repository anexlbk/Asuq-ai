"""
Graph routing functions — reference implementation.

Public reference reflecting the decision logic described in docs/architecture.md, written for
this showcase rather than copy-pasted production source. Pure functions: state in, next-node
name out, no I/O, no LLM calls, no side effects — routing decisions are cheap by design.
"""

from .state import AsuqState


def route_after_input_security(state: AsuqState) -> str:
    result = state.get("security_input_result", {})
    if result.get("blocked"):
        return "response_formatter"
    return "prompt_rating"


def route_after_prompt_rating(state: AsuqState) -> str:
    rating = state.get("routing_confidence", 4)  # defaults conservative on missing data
    if rating <= 3:
        return "principal_synthesize"
    return "preprocess"


def route_after_router(state: AsuqState) -> str:
    if state.get("is_simple"):
        return "principal_synthesize"
    if state.get("routing_confidence", 1.0) < 0.3:
        return "clarify"
    intent = state.get("intent", "")
    if intent in {"competitor", "trend_radar", "pdf"}:
        return "clarify"
    if intent in {"content", "market_intel", "general"}:
        return "rag_load"
    return "rag_load"


def route_after_clarify(state: AsuqState) -> str:
    if state.get("clarification_questions"):
        return "memory_write"
    return "rag_load"


def route_after_memory(state: AsuqState) -> str:
    if state.get("error"):
        return "response_formatter"
    return "requirements_check"


def route_after_requirements(state: AsuqState) -> str:
    if state.get("clarification_questions"):
        return "memory_write"
    return "skill_dispatcher"


def route_after_skill(state: AsuqState) -> str:
    skill_output = state.get("skill_output", {})
    if skill_output.get("requires_llm"):
        return "llm_backbone"
    if state.get("is_simple_content"):
        return "simple_content_plan"
    return "principal_plan"


def route_after_plan(state: AsuqState) -> str:
    if not state.get("plan"):
        return "principal_synthesize"
    return "slave_executor"


# Intent-aware quality thresholds — content generation is cheap to redo, competitive analysis
# is expensive and gets more retry budget.
QUALITY_THRESHOLDS = {
    "content": 6.0,
    "ad_copy": 6.0,
    "lead_magnet": 6.5,
    "trend_radar": 7.0,
    "competitor": 7.5,
}
MAX_RETRIES = {
    "content": 1,
    "competitor": 3,
    "trend_radar": 3,
    "market_intel": 3,
}


def quality_gate_route(state: AsuqState) -> str:
    intent = state.get("intent", "general")
    threshold = QUALITY_THRESHOLDS.get(intent, 6.0)
    max_retries = MAX_RETRIES.get(intent, 1)

    score = state.get("reviewer_score", 0.0)
    retries = state.get("retry_count", 0)

    if score < threshold and retries < max_retries:
        return "slave_executor"
    return "principal_synthesize"
