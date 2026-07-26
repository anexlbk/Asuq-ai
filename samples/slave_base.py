"""Abstract base class for slave agents in the multi-agent system.

Slaves are specialized workers invoked by the principal planner.
Each slave receives a task definition and shared context, performs
its work, and returns a structured output.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SlaveOutput:
    """Standard output from a slave agent."""
    result: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseSlave(ABC):
    """Abstract base class all slave agents must implement.

    Subclasses set `name` and `description` for registration in the
    slave executor, and implement `run()` to perform their specific task.
    """
    name: str = ""
    description: str = ""

    @abstractmethod
    async def run(self, task: Dict[str, Any], context: Dict[str, Any]) -> SlaveOutput:
        """Execute the slave's task.

        Args:
            task: The task definition from the planner (instructions, depends_on, etc.)
            context: Shared context including RAG docs, memory, and results from upstream slaves.

        Returns:
            SlaveOutput with the result text, optional metadata, and optional error.
        """
        ...
