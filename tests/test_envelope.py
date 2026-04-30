"""Unit tests for the tool envelope helpers."""
import json
import pytest
from atelier._envelope import (
    ErrorCode,
    ToolError,
    _tool_response,
    tool_envelope,
    _check_addon_result,
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


def test_get_polyhaven_status_envelope_shape(mock_blender_connection):
    """All get_*_status tools should return the canonical envelope."""
    import json
    from atelier.server import get_polyhaven_status
    mock_blender_connection.send_command.return_value = {
        "enabled": True,
        "message": "PolyHaven ready",
    }
    out = get_polyhaven_status(None)
    parsed = json.loads(out)
    assert parsed["ok"] is True
    assert parsed["data"]["enabled"] is True


def test_get_polyhaven_status_handles_addon_disconnect(mock_blender_connection):
    import json
    from atelier.server import get_polyhaven_status
    mock_blender_connection.send_command.side_effect = ConnectionRefusedError("[Errno 61]")
    out = get_polyhaven_status(None)
    parsed = json.loads(out)
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "STATE_REQUIRED"
    assert "Connect to Claude" in parsed["error"]["hint"]


def test_check_addon_result_passes_through_normal_dict():
    result = {"foo": "bar", "count": 3}
    out = _check_addon_result(result)
    assert out is result


def test_check_addon_result_passes_through_non_dict():
    out = _check_addon_result(["a", "b"])
    assert out == ["a", "b"]


def test_check_addon_result_raises_state_required_on_load_first():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "Call download_polyhaven_asset to load an HDRI first"})
    assert exc_info.value.code is ErrorCode.STATE_REQUIRED
    assert "load" in exc_info.value.hint.lower()


def test_check_addon_result_raises_bad_input_on_required_param():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "custom_hex='#RRGGBB' is required"})
    assert exc_info.value.code is ErrorCode.BAD_INPUT


def test_check_addon_result_raises_internal_on_generic_error():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "Something went sideways"})
    assert exc_info.value.code is ErrorCode.INTERNAL


def test_check_addon_result_ignores_empty_error_field():
    result = {"error": "", "data": {"x": 1}}
    out = _check_addon_result(result)
    assert out is result  # empty string is falsy


# ----- NETWORK heuristic regression tests (v2.0.1 polish) -----
# These cover transient upstream failures that should map to NETWORK
# so LLM clients know to retry vs. ask the user to fix input.

def test_check_addon_result_http_503_maps_to_network():
    """HTTP 5xx from OpenAI-compat endpoint = transient upstream issue.

    Surfaced during Sprint 5 Task 17 live verification: a Comfly call
    for a model the user's plan didn't cover came back as
    'OpenAI HTTP 503: ...' and was incorrectly classified INTERNAL.
    """
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "OpenAI HTTP 503: {'error': {'message': 'upstream busy'}}"})
    assert exc_info.value.code is ErrorCode.NETWORK


def test_check_addon_result_http_502_maps_to_network():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "OpenAI HTTP 502: bad gateway"})
    assert exc_info.value.code is ErrorCode.NETWORK


def test_check_addon_result_http_504_maps_to_network():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "OpenAI HTTP 504: gateway timeout"})
    assert exc_info.value.code is ErrorCode.NETWORK


def test_check_addon_result_comfly_chinese_no_channel_maps_to_network():
    """Comfly returns Chinese error '当前分组下对于模型 [...] 无可用渠道'
    when the user's plan lacks a relay for the requested model alias.
    Treat as NETWORK — retry/fallback semantics, not user-input error."""
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "OpenAI HTTP 503: {'error': {'message': '当前分组 [default] 下对于模型 [gemini-3.1-flash-image-preview-2k] 无可用渠道'}}"})
    assert exc_info.value.code is ErrorCode.NETWORK


def test_check_addon_result_socket_timeout_string_maps_to_network():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "OpenAI request failed: HTTPSConnectionPool(host='api.openai.com', port=443): Read timed out."})
    assert exc_info.value.code is ErrorCode.NETWORK


def test_check_addon_result_unreachable_maps_to_network():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "Sketchfab unreachable"})
    assert exc_info.value.code is ErrorCode.NETWORK


# ----- RATE_LIMITED heuristic -----

def test_check_addon_result_429_maps_to_rate_limited():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "Tripo3D HTTP 429: Too many requests"})
    assert exc_info.value.code is ErrorCode.RATE_LIMITED


def test_check_addon_result_quota_exceeded_maps_to_rate_limited():
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "Meshy: monthly quota exceeded the limit"})
    assert exc_info.value.code is ErrorCode.RATE_LIMITED


# ----- Confirm BAD_INPUT still wins over NETWORK when both signals
# are present — keeps existing tests' semantics. -----

def test_check_addon_result_unsupported_model_maps_to_bad_input():
    """Even though the message contains 'unsupported', it's a user
    input problem (wrong model name), not a transient network issue."""
    with pytest.raises(ToolError) as exc_info:
        _check_addon_result({"error": "Unsupported model 'foo-bar'. Use 'dall-e-3' or 'gpt-image-1'."})
    assert exc_info.value.code is ErrorCode.BAD_INPUT


def test_telemetry_default_is_opt_in():
    """In the v2 fork, telemetry_consent defaults to False (opt-in)."""
    import re
    from pathlib import Path
    addon_text = Path(__file__).resolve().parent.parent.joinpath("addon.py").read_text()
    # Match the telemetry_consent property block — default must be False
    m = re.search(
        r"telemetry_consent:\s*BoolProperty\([^)]*?default\s*=\s*(\w+)",
        addon_text,
        re.DOTALL,
    )
    assert m, "could not find telemetry_consent property in addon.py"
    assert m.group(1) == "False", \
        f"telemetry default is {m.group(1)}; should be False (opt-in)"
