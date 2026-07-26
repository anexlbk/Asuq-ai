"""Routing / conditional-edge functions for the LangGraph state machine.

These are pure control-flow functions: state in, next-node string out, no I/O.
They determine which graph node runs next based on the current state.
"""
from app.graph.state import AsuqState

# Intent sets used by routing decisions
DETAIL_INTENTS = frozenset(["content", "competitor", "ad_copy", "trend_radar", "lead_magnet"])
KNOWLEDGE_INTENTS = frozenset(["competitor", "trend_radar", "market_intel", "research"])


def _prior_clarification_in_chat(chat_history: list[str]) -> bool:
    """Check if chat_history has a prior clarification exchange (user Q -> assistant questions)."""
    if len(chat_history) < 2:
        return False
    for i in range(len(chat_history) - 1, -1, -1):
        if chat_history[i].startswith("assistant:") and "?" in chat_history[i]:
            return i > 0 and chat_history[i - 1].startswith("user:")
    return False


def _needs_clarification(state: AsuqState) -> str:
    """After router: route to clarify for detail-needing intents or low confidence.

    - confidence < 0.3 and non-general intent -> clarify
    - 0.3 <= confidence < 0.5 and non-general intent -> rag_load with low_confidence_flag
    - confidence >= 0.5 or general -> proceed normally

    Simple queries (greetings, thanks) route directly to principal_synthesize,
    bypassing planner, slave executor, quality gate, and RAG.
    """
    if state.get("error"):
        return "response_formatter"

    # Fast-path: simple greetings bypass the full pipeline
    if state.get("is_simple"):
        return "principal_synthesize"

    confidence = state.get("routing_confidence", 1.0)
    intent = state.get("selected_skill", "general")
    chat_history = state.get("chat_history", [])

    # User is answering prior clarification questions - always clarify
    if _prior_clarification_in_chat(chat_history):
        return "clarify"

    if intent in DETAIL_INTENTS:
        return "clarify"
    if confidence < 0.3 and intent != "general":
        return "clarify"
    if confidence < 0.5 and intent != "general":
        state["low_confidence_flag"] = True
        return "rag_load"
    if intent in KNOWLEDGE_INTENTS:
        return "rag_load"
    return "memory_load"


def _route_after_clarify(state: AsuqState) -> str:
    """After clarify: if questions were generated, route to memory_write before END; otherwise continue."""
    if state.get("error"):
        return "response_formatter"
    if state.get("clarification_questions"):
        return "memory_write"
    intent = state.get("selected_skill", "general")
    if intent in KNOWLEDGE_INTENTS:
        return "rag_load"
    return "memory_load"


def _should_write_memory(state: AsuqState) -> str:
    """After principal_synthesize: always route through security_output.

    security_output_node handles errors gracefully (returns state unchanged),
    preventing content in final_output from reaching the user without leak detection.
    """
    return "security_output"


def _route_after_input_security(state: AsuqState) -> str:
    """After security_input: route to prompt_rating if safe, response_formatter if blocked."""
    if state.get("error") == "security_block":
        return "response_formatter"
    return "prompt_rating"


def _route_after_prompt_rating(state: AsuqState) -> str:
    """After prompt_rating: route based on prompt quality.

    If rating > 3 (good quality), proceed to router for normal pipeline.
    If rating <= 3 (poor quality), route to principal_synthesize for quick response.
    Preprocess has ALREADY run before this point, so normalized_input
    and script_type are always populated on both branches.
    """
    if state.get("error"):
        return "response_formatter"

    rating = state.get("prompt_rating")
    if rating is not None and rating <= 3:
        return "principal_synthesize"
    return "router"


def _route_after_skill(state: AsuqState) -> str:
    """After skill_dispatcher: format skill output via LLM backbone when needed.

    Two paths after skill execution:
    - llm_backbone fast-path: skills that return structured data needing
      LLM formatting into user-friendly text. Skill sets requires_llm=True,
      then llm_backbone formats -> principal_plan.
    - principal_plan direct: skills that return ready-to-use results
      (requires_llm=False) or no result. Goes straight to planning.
    Simple content requests use a pre-built 2-task plan (bypasses planner LLM).
    """
    if state.get("error"):
        return "response_formatter"
    skill_output = state.get("skill_output", {})
    if skill_output.get("requires_llm", False) and skill_output.get("result", ""):
        return "llm_backbone"
    if state.get("is_simple_content"):
        return "simple_content_plan"
    return "principal_plan"


def _route_after_plan(state: AsuqState) -> str:
    """After principal_plan: skip slave execution for simple queries (empty plan)."""
    if state.get("error"):
        return "response_formatter"
    plan = state.get("plan", [])
    if not plan:
        return "principal_synthesize"
    return "slave_executor"


def _route_after_memory(state: AsuqState) -> str:
    """After memory_load: route to requirements_check or handle errors."""
    if state.get("error"):
        return "response_formatter"
    return "requirements_check"


def _route_after_requirements(state: AsuqState) -> str:
    """After requirements_check: route based on info completeness.

    If clarification_questions are set, route to memory_write first
    (preserving extracted facts). Otherwise, proceed to skill_dispatcher.
    """
    if state.get("error"):
        return "response_formatter"
    if state.get("clarification_questions"):
        return "memory_write"
    return "skill_dispatcher"


def _quality_gate_route(state: AsuqState) -> str:
    """After quality_gate: route based on needs_retry flag.

    quality_gate_node sets needs_retry=True when reviewer score < threshold
    and retries haven't been exhausted. The retry_count increment happens
    in slave_executor_node (single place that owns the counter).
    """
    if state.get("error"):
        return "response_formatter"

    if state.get("needs_retry"):
        return "slave_executor"

    from app.graph.nodes.quality_gate import get_effective_max_passes, get_quality_threshold
    score = state.get("reviewer_score", 0.0)
    retries = state.get("retry_count", 0)
    max_passes = get_effective_max_passes(state)
    threshold = get_quality_threshold(state)

    if score < threshold and retries >= max_passes:
        state["quality_exhausted"] = True

    return "principal_synthesize"
