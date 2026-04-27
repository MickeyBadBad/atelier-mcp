"""Unit tests for the tool envelope helpers."""
import json
from blender_mcp._envelope import (
    ErrorCode,
    ToolError,
    _tool_response,
    tool_envelope,
)


def test_tool_response_ok():
    out = _tool_response(ok=True, data={"x": 1})
    assert json.loads(out) == {"ok": True, "data": {"x": 1}}


def test_tool_response_error():
    out = _tool_response(
        ok=False,
        error={"code": ErrorCode.NO_API_KEY, "hint": "Set key", "detail": "Missing TRIPO key"},
    )
    parsed = json.loads(out)
    assert parsed == {
        "ok": False,
        "error": {"code": "NO_API_KEY", "hint": "Set key", "detail": "Missing TRIPO key"},
    }


def test_tool_error_carries_code_and_hint():
    err = ToolError(ErrorCode.STATE_REQUIRED, hint="Load HDRI first", detail="No TexEnvironment node")
    assert err.code is ErrorCode.STATE_REQUIRED
    assert err.hint == "Load HDRI first"
    assert err.detail == "No TexEnvironment node"
    assert "STATE_REQUIRED" in str(err)
