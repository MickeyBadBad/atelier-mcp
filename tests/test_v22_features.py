"""Sprint 6 / v2.2.0+fork.1 — Quality of Life additions.

Each task adds tests below in the order they appear in the plan.
"""
import pytest


def test_v22_marker():
    """Smoke marker test — ensures the file is collected."""
    assert True


def test_place_on_ground_flushes_view_layer(monkeypatch):
    """After mutating obj.location, _world_bbox must read the new
    matrix_world. The handler is required to call view_layer.update()
    so descendant children pick up the parent's translation."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    # Track view_layer.update() calls
    update_calls = []
    addon.bpy.context.view_layer.update = lambda: update_calls.append("called")

    # Stub a fake object with a children-walking _world_bbox path
    class FakeVec:
        def __init__(self, x, y, z):
            self.x, self.y, self.z = x, y, z

    class FakeObj:
        def __init__(self):
            self.location = FakeVec(0, 0, 0)

    fake = FakeObj()
    addon.bpy.data.objects.get = lambda name: fake if name == "tgt" else None

    # First call returns bbox before move; second after.
    bbox_returns = iter([
        (FakeVec(-1, -1, -1), FakeVec(1, 1, 1)),
        (FakeVec(2, 2, -1), FakeVec(4, 4, 1)),
    ])
    addon.BlenderMCPServer._world_bbox = staticmethod(
        lambda obj: next(bbox_returns)
    )

    server = addon.BlenderMCPServer.__new__(addon.BlenderMCPServer)
    out = server.place_on_ground("tgt", ground_z=0.0, target_xy=[3.0, 3.0])

    assert update_calls == ["called"], (
        f"view_layer.update() must be called between location write "
        f"and second _world_bbox read; got calls: {update_calls}"
    )
    # Sanity: the post-move bbox should be reflected in the response
    assert out["new_bbox_min"] == [2, 2, -1]
