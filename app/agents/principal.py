"""Principal agent — orchestrates slave execution and response synthesis."""

from typing import Any, Dict, List

from app.agents.slaves import BaseSlave, LegalExpertSlave

_default_synthesis = ["general", "research", "content_writer", "legal_expert"]

SLAVE_REGISTRY: Dict[str, BaseSlave] = {
    "legal_expert": LegalExpertSlave(),
}


async def execute_slave(
    slave_name: str,
    task: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    slave = SLAVE_REGISTRY.get(slave_name)
    if not slave:
        return {"result": "", "error": f"Unknown slave: {slave_name}"}
    output = await slave.run(task, context)
    return {
        "result": output.result,
        "metadata": output.metadata,
        "error": output.error,
    }


async def principal_agent_run(
    plan: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    results = {}
    for task in plan:
        slave_name = task.get("slave_name")
        if slave_name not in _default_synthesis:
            results[slave_name] = {"result": "", "error": f"Unknown slave: {slave_name}"}
            continue
        result = await execute_slave(slave_name, task, context)
        results[slave_name] = result
    return results
