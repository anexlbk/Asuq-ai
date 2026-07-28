"""Principal synthesize node — combines slave results into final response."""

from typing import Any, Dict

from app.graph.state import AsuqState


async def principal_synthesize_node(state: AsuqState) -> Dict[str, Any]:
    if state.get("error"):
        return {"error": state["error"]}

    slave_results = state.get("slave_results", {})

    # Legal expert fast-path: pass through output verbatim to preserve disclaimers + citations
    if "legal_expert" in slave_results:
        legal_output = slave_results["legal_expert"]
        if not legal_output.get("error") and legal_output.get("result"):
            return {
                "llm_response": legal_output["result"],
                "response_type": "text",
            }

    from app.prompts.principal import PRINCIPAL_SYNTHESIZER_SYSTEM

    slaves_used = list(slave_results.keys())
    context_parts = []
    for slave_name, output in slave_results.items():
        if output.get("result"):
            context_parts.append(f"=== {slave_name} ===\n{output['result']}")

    combined = "\n\n".join(context_parts)
    prompt = PRINCIPAL_SYNTHESIZER_SYSTEM.format(
        slaves_used=", ".join(slaves_used),
    ) + f"\n\nSlave outputs:\n{combined}"

    llm = state.get("llm")
    if not llm:
        return {"error": "No LLM available for synthesis"}

    response = await llm.agenerate([prompt])

    return {
        "llm_response": response.generations[0][0].text,
        "response_type": "text",
    }
