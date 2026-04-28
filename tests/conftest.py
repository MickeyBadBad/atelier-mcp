"""Shared pytest fixtures for blender-mcp tests.

Mocks the socket layer so we can test server.py tool wrappers without a
running Blender instance.
"""
import sys
from unittest.mock import MagicMock

# Stub Blender-only modules at import time so addon.py (top-level module
# at the repo root, not part of the blender_mcp package) can be imported
# in unit tests without a running Blender. addon.py does
#   import bpy
#   import mathutils
#   import requests
#   from bpy.props import IntProperty, BoolProperty
# all of which only exist inside Blender's embedded Python (requests is
# vendored by Blender but not declared in our pyproject deps).
for _name in ("bpy", "bpy.types", "bpy.props", "mathutils", "requests"):
    sys.modules.setdefault(_name, MagicMock())

import pytest


@pytest.fixture
def mock_blender_connection(monkeypatch):
    """Replace get_blender_connection() with a fake that returns whatever
    we set via .send_command.return_value."""
    fake = MagicMock()
    fake.send_command = MagicMock(return_value={"some": "result"})
    from blender_mcp import server
    monkeypatch.setattr(server, "get_blender_connection", lambda: fake)
    return fake
