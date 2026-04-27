"""Shared pytest fixtures for blender-mcp tests.

Mocks the socket layer so we can test server.py tool wrappers without a
running Blender instance.
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_blender_connection(monkeypatch):
    """Replace get_blender_connection() with a fake that returns whatever
    we set via .send_command.return_value."""
    fake = MagicMock()
    fake.send_command = MagicMock(return_value={"some": "result"})
    from blender_mcp import server
    monkeypatch.setattr(server, "get_blender_connection", lambda: fake)
    return fake
