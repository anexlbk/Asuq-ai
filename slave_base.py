"""
BaseSlave contract - reference implementation.

Public reference reflecting the agent interface described in docs/architecture.md, written for
this showcase rather than copy-pasted production source.

11 specialist slaves (researcher, strategist, creator, localizer, reviewer, searcher,
requirements, reflection, security_input, security_output, rag_browser) implement this contract.
The Principal planner selects from a fixed allowlist of "approved" slaves per task - adding a new
slave means implementing this ABC, registering it, and deciding whether it belongs in that
allowlist. Slaves outside the allowlist exist but aren't planner-selectable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SlaveOutput:
    result: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    requires_llm: bool = False
    status_message: Optional[str] = None
    # Deliberately no `status` or `data` fields - every consumer reads `result` /
    # `metadata`. Reaching for `.status` or `.data` on this object is a field-name bug,
    # not a missing feature.


class BaseSlave(ABC):
    """
    Every slave is a single-purpose async unit the Principal can schedule as part of a plan.
    Slaves execute in dependency-ordered batches (asyncio.gather within a batch), each batch
    bounded by a fixed timeout - one slow slave doesn't block unrelated ones.
    """

    name: str

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> SlaveOutput:
        """
        Execute this slave's task.

        `context` includes the task description from the plan, relevant state slices
        (rag_context, memory_context, prior slave_results for self-correction), and
        the language/script the response must be produced in.
        """
        raise NotImplementedError
