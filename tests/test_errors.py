import socket
from blender_mcp._errors import _format_error


def test_connection_refused_maps_to_state_required():
    exc = ConnectionRefusedError("[Errno 61] Connection refused")
    out = _format_error("get_scene_info", exc)
    assert out["code"] == "STATE_REQUIRED"
    assert "Connect to Claude" in out["hint"]


def test_socket_timeout_maps_to_network():
    exc = socket.timeout("timed out")
    out = _format_error("render_image", exc)
    assert out["code"] == "NETWORK"
    assert "timeout" in out["hint"].lower() or "busy" in out["hint"].lower()


def test_keyerror_for_api_key_maps_to_no_api_key():
    exc = KeyError("api_key")
    out = _format_error("generate_tripo3d_text_to_3d", exc)
    assert out["code"] == "NO_API_KEY"
    assert "api key" in out["hint"].lower()


def test_value_error_maps_to_bad_input():
    exc = ValueError("Invalid hex color: '#zzz'")
    out = _format_error("apply_material_color", exc)
    assert out["code"] == "BAD_INPUT"


def test_unknown_exception_maps_to_internal():
    exc = RuntimeError("something weird")
    out = _format_error("foo", exc)
    assert out["code"] == "INTERNAL"
