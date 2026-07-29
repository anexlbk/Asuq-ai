"""Security input node — fail-closed: returns safe=False on any error.

This is a SHOWCASE implementation. Production patterns differ significantly.
"""
from typing import Any, Dict

from app.graph.state import AsuqState

BLOCKLIST_PATTERNS = [
    r"illustrative\.pattern\.one",
    r"illustrative\.pattern\.two",
]


async def security_input_node(state: AsuqState) -> Dict[str, Any]:
    try:
        text = state.get("raw_input", "")
        import re
        for pattern in BLOCKLIST_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "security_input_result": {
                        "safe": False,
                        "reason": "Blocklist match",
                        "block_category": "prompt_injection",
                    }
                }
        return {
            "security_input_result": {
                "safe": True,
                "reason": "",
            }
        }
    except Exception as e:
        return {
            "security_input_result": {
                "safe": False,
                "reason": "Security check error",
                "error": str(e),
            }
        }
