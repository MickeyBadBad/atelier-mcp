"""Smoke tests confirming the new MCP tools register correctly."""
from __future__ import annotations

from blender_mcp import server


def test_discovery_mcp_tools_registered():
    """All 7 new Slice 2 MCP tools must be present on the server module."""
    expected = (
        "run_discovery_questionnaire",
        "submit_questionnaire_answers",
        "read_taste_profile_tool",
        "update_taste_profile_tool",
        "create_interior_project",
        "version_snapshot",
        "version_log_entry",
    )
    missing = [name for name in expected if not hasattr(server, name)]
    assert not missing, f"missing tools: {missing}"


def test_create_interior_project_has_signature():
    """The tool wrapper should be callable with the spec'd parameters."""
    import inspect
    sig = inspect.signature(server.create_interior_project)
    expected_params = {
        "ctx", "project_name", "project_type", "spaces",
        "project_root", "units",
    }
    assert expected_params.issubset(set(sig.parameters.keys()))
