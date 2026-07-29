"""Quality gate node — evaluates slave output and decides on retry (SHOWCASE)."""

from typing import Any, Dict

from app.graph.state import AsuqState

BASE_THRESHOLD = 7.0  # illustrative
LEGAL_THRESHOLD = 7.5  # illustrative


def get_quality_threshold(state: AsuqState) -> float:
    slave_results = state.get("slave_results", {})
    if "legal_expert" in slave_results:
        return LEGAL_THRESHOLD
    return BASE_THRESHOLD


def get_effective_max_passes(state: AsuqState) -> int:
    return 2


async def quality_gate_node(state: AsuqState) -> Dict[str, Any]:
    if state.get("error"):
        return {"error": state["error"]}

    threshold = get_quality_threshold(state)
    score = state.get("reviewer_score", 0.0)
    retries = state.get("retry_count", 0)
    max_passes = get_effective_max_passes(state)

    needs_retry = score < threshold and retries < max_passes

    return {
        "needs_retry": needs_retry,
        "quality_threshold_used": threshold,
    }
