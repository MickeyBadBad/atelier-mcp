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


def test_tool_envelope_wraps_normal_dict_return():
    """Normal dict return becomes ok=True envelope."""
    @tool_envelope
    def my_tool():
        return {"foo": "bar"}
    out = my_tool()
    parsed = json.loads(out)
    assert parsed == {"ok": True, "data": {"foo": "bar"}}


def test_tool_envelope_catches_tool_error():
    """ToolError raises become structured ok=False envelopes."""
    @tool_envelope
    def my_tool():
        raise ToolError(ErrorCode.NO_API_KEY, hint="Set key", detail="Missing X")
    out = my_tool()
    parsed = json.loads(out)
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "NO_API_KEY"
    assert parsed["error"]["hint"] == "Set key"
    assert parsed["error"]["detail"] == "Missing X"


def test_tool_envelope_catches_generic_exception_via_format_error():
    """Generic exceptions go through _format_error stub (returns INTERNAL)."""
    @tool_envelope
    def my_tool():
        raise RuntimeError("boom")
    out = my_tool()
    parsed = json.loads(out)
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "INTERNAL"
    assert "RuntimeError" in parsed["error"]["detail"]


def test_tool_envelope_passes_through_real_envelope_string():
    """A genuine envelope JSON string is passed through unchanged."""
    @tool_envelope
    def my_tool():
        return json.dumps({"ok": True, "data": {"x": 1}})
    out = my_tool()
    parsed = json.loads(out)
    assert parsed == {"ok": True, "data": {"x": 1}}


def test_tool_envelope_does_not_pass_through_fake_ok_string():
    """Fake-looking envelope (ok is not bool) gets re-wrapped as data."""
    @tool_envelope
    def my_tool():
        return json.dumps({"ok": "truthy-but-fake", "malformed": True})
    out = my_tool()
    parsed = json.loads(out)
    # The fake string becomes the data of a real envelope:
    assert parsed["ok"] is True
    assert "truthy-but-fake" in parsed["data"]
