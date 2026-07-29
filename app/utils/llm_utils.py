"""LLM safety utilities — bounds-checked access and safe response helpers."""

from typing import Any, Dict, List, Optional, Sequence, TypeVar

T = TypeVar("T")


def safe_llm_response(
    generations: List[List[Dict[str, Any]]],
    default: str = "",
) -> str:
    """Extract text from an LLM agenerate response with bounds-checked access.

    Returns `default` (empty string) if the response structure is unexpected,
    preventing IndexError from malformed LLM output.
    """
    try:
        if not generations or not isinstance(generations, list):
            return default
        first_gen = generations[0]
        if not first_gen or not isinstance(first_gen, list):
            return default
        first_entry = first_gen[0]
        if not isinstance(first_entry, dict):
            return default
        return first_entry.get("text", default)
    except (IndexError, TypeError, KeyError, AttributeError):
        return default


def safe_choice(seq: Sequence[T], index: int, default: T) -> T:
    """Bounds-checked sequence access — returns default if index is out of range."""
    if not seq:
        return default
    if 0 <= index < len(seq):
        return seq[index]
    return default
