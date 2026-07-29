"""Security output node — fail-closed: returns safe=False on any error.

This is a SHOWCASE implementation. Production patterns differ significantly.
"""
from typing import Any, Dict

from app.graph.state import AsuqState

LEAK_PATTERNS = [
    r"illustrative\.credential\.pattern",
    r"illustrative\.token\.pattern",
]


async def security_output_node(state: AsuqState) -> Dict[str, Any]:
    try:
        text = state.get("llm_response", "") or state.get("proposed_response", "")
        import re
        for pattern in LEAK_PATTERNS:
            if re.search(pattern, text):
                return {
                    "security_output_result": {
                        "safe": False,
                        "reason": "Potential leak matched",
                        "leak_category": "credential",
                    }
                }
        return {
            "security_output_result": {
                "safe": True,
                "reason": "",
            }
        }
    except Exception as e:
        return {
            "security_output_result": {
                "safe": False,
                "reason": "Security check error",
                "error": str(e),
            }
        }
