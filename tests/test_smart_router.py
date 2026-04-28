"""Mock-based tests for generate_3d_smart routing logic.

We don't actually invoke providers — we patch the underlying
generate_*_text_to_3d methods on BlenderMCPServer and assert the right
one was called with the right args."""
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def server_with_hyper3d_only():
    """Return a fake server where only Hyper3D is configured."""
    from addon import BlenderMCPServer
    s = BlenderMCPServer.__new__(BlenderMCPServer)
    s.check_services = lambda: {
        "summary": {"ready": ["polyhaven", "hyper3d"]},
        "services": {},
    }
    s.generate_hyper3d_text_to_3d = MagicMock(return_value={"imported_objects": ["A"]})
    s.generate_tripo3d_text_to_3d = MagicMock()
    s.generate_meshy_text_to_3d = MagicMock()
    return s


def test_smart_router_actually_invokes_hyper3d(server_with_hyper3d_only):
    """Regression: pre-v2 the router silently bailed with fallback_required."""
    from addon import BlenderMCPServer
    result = BlenderMCPServer.generate_3d_smart(
        server_with_hyper3d_only,
        prompt="brass door knocker",
        quality="fast",
    )
    server_with_hyper3d_only.generate_hyper3d_text_to_3d.assert_called_once()
    assert "fallback_required" not in (result or {})
    assert result.get("imported_objects") == ["A"]


def test_smart_router_cost_estimate_tripo_best_is_six_not_ten():
    """Regression: pre-v2 'best' Tripo3D was estimated at 10 credits,
    skipping Tripo when max_credits=8 even though typical cost is ~6."""
    from addon import BlenderMCPServer
    s = BlenderMCPServer.__new__(BlenderMCPServer)
    s.check_services = lambda: {
        "summary": {"ready": ["tripo3d", "meshy"]},
        "services": {},
    }
    s.generate_tripo3d_text_to_3d = MagicMock(return_value={"imported_objects": ["X"]})
    s.generate_meshy_text_to_3d = MagicMock()
    result = BlenderMCPServer.generate_3d_smart(
        s, prompt="x", quality="best", max_credits=8,
    )
    s.generate_tripo3d_text_to_3d.assert_called_once()
    s.generate_meshy_text_to_3d.assert_not_called()


def test_smart_router_routes_to_image_to_3d_when_ref_provided():
    from addon import BlenderMCPServer
    s = BlenderMCPServer.__new__(BlenderMCPServer)
    s.check_services = lambda: {
        "summary": {"ready": ["tripo3d"]},
        "services": {},
    }
    s.generate_tripo3d_image_to_3d = MagicMock(return_value={"imported_objects": ["I"]})
    s.generate_tripo3d_text_to_3d = MagicMock()
    BlenderMCPServer.generate_3d_smart(
        s,
        prompt="brass knob",
        quality="standard",
        reference_image_url="https://example.com/x.jpg",
    )
    s.generate_tripo3d_image_to_3d.assert_called_once()
    s.generate_tripo3d_text_to_3d.assert_not_called()
