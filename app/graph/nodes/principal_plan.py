"""Principal planner node — decomposes user request into slave tasks."""

from typing import Any, Dict

from app.graph.state import AsuqState

APPROVED_SLAVES = [
    "general",
    "research",
    "content_writer",
    "legal_expert",
]


async def principal_plan_node(state: AsuqState) -> Dict[str, Any]:
    if state.get("error"):
        return {"error": state["error"]}

    llm = state.get("llm")
    if not llm:
        return {"error": "No LLM available for planning"}

    from app.prompts.principal import PRINCIPAL_PLANNER_SYSTEM

    query = state.get("current_normalized_input", state.get("normalized_input", ""))
    prompt = PRINCIPAL_PLANNER_SYSTEM + f"\n\nUser request: {query}\n\nAvailable slaves: {', '.join(APPROVED_SLAVES)}\n\nReturn a JSON plan."

    response = await llm.agenerate([prompt])
    plan_text = response.generations[0][0].text

    import json
    try:
        plan = json.loads(plan_text)
    except json.JSONDecodeError:
        plan = []

    return {"plan": plan}
