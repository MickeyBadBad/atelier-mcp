"""Smoke tests for Slice 8 native MCP tools (Blender-side commands)."""
from __future__ import annotations

import inspect

from blender_mcp import server


def test_native_tools_registered():
    expected = (
        "audit_interior_quality_native",
        "create_interior_project_native",
    )
    missing = [name for name in expected if not hasattr(server, name)]
    assert not missing, f"missing native tools: {missing}"


def test_audit_native_signature():
    sig = inspect.signature(server.audit_interior_quality_native)
    params = set(sig.parameters)
    expected = {"ctx", "mode", "project_root"}
    assert expected.issubset(params)


def test_create_project_native_signature():
    sig = inspect.signature(server.create_interior_project_native)
    params = set(sig.parameters)
    expected = {
        "ctx", "project_name", "project_type",
        "spaces", "project_root", "units",
    }
    assert expected.issubset(params)


def test_addon_command_handlers_registered_in_addon():
    """The addon.py file should have the two new command handlers
    wired into the dispatch table. We grep the source rather than
    importing addon.py (which requires bpy)."""
    import pathlib
    addon_path = pathlib.Path(__file__).parent.parent / "addon.py"
    source = addon_path.read_text(encoding="utf-8")
    assert '"interior_audit_scan"' in source, (
        "interior_audit_scan command not registered in addon dispatch"
    )
    assert '"interior_project_scaffold"' in source, (
        "interior_project_scaffold command not registered in addon dispatch"
    )
    assert "def interior_audit_scan(" in source, (
        "interior_audit_scan method not defined in BlenderMCPServer"
    )
    assert "def interior_project_scaffold(" in source, (
        "interior_project_scaffold method not defined in BlenderMCPServer"
    )
