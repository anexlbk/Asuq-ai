"""Abstract base class for slave agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SlaveOutput:
    result: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseSlave(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    async def run(self, task: Dict[str, Any], context: Dict[str, Any]) -> SlaveOutput:
        ...
