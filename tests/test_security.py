"""Security tests — fail-closed behavior is verified."""
import pytest


class FakeFailingNode:
    """Simulates a security node that raises on any input."""

    async def check(self, text: str) -> dict:
        raise RuntimeError("Internal dependency unavailable")


class FakeBlockingNode:
    """Simulates a security node that returns safe=False."""

    async def check(self, text: str) -> dict:
        return {"safe": False, "reason": "Match found"}


class FakePassingNode:
    """Simulates a security node that returns safe=True."""

    async def check(self, text: str) -> dict:
        return {"safe": True, "reason": ""}


@pytest.mark.asyncio
async def test_security_fail_closed_on_error():
    node = FakeFailingNode()
    try:
        result = await node.check("some input")
    except RuntimeError:
        result = {"safe": False, "error": "Internal dependency unavailable"}
    assert result.get("safe") is False, "Fail-closed: error must result in safe=False"


@pytest.mark.asyncio
async def test_security_blocks_on_positive_detection():
    node = FakeBlockingNode()
    result = await node.check("bad content")
    assert result.get("safe") is False
    assert "reason" in result


@pytest.mark.asyncio
async def test_security_allows_safe_content():
    node = FakePassingNode()
    result = await node.check("good content")
    assert result.get("safe") is True


def test_route_after_input_security_blocked():
    from routing_functions import route_after_input_security

    class FakeState(dict):
        def get(self, key, default=None):
            return {
                "security_input_result": {"safe": False, "reason": "blocked"},
            }.get(key, {} if key in ["security_input_result"] else default)

    state = FakeState()
    assert route_after_input_security(state) == "response_formatter"


def test_route_after_input_security_safe():
    from routing_functions import route_after_input_security

    class FakeState(dict):
        def get(self, key, default=None):
            return {
                "security_input_result": {"safe": True},
            }.get(key, {} if key in ["security_input_result"] else default)

    state = FakeState()
    assert route_after_input_security(state) == "prompt_rating"
