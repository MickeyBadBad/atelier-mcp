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


def test_generate_image_openai_extension_matches_content_type(tmp_path, monkeypatch):
    """When Comfly returns image/jpeg, the saved file must end in .jpg
    (or .jpeg) — not the .png the user requested. The path is rewritten
    based on Content-Type and the new path is reported in the response."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    # Stub the downloader to write 100 bytes of JPEG-magic content
    def fake_download(url, target_path, max_retries=3):
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 96)  # JPEG SOI
        return target_path

    monkeypatch.setattr(addon, "_resilient_download_to_file", fake_download)

    # Stub _content_type_for_url to return image/jpeg
    monkeypatch.setattr(addon.BlenderMCPServer, "_content_type_for_url",
                        staticmethod(lambda url: "image/jpeg"))

    requested_path = str(tmp_path / "render.png")
    rewritten = addon.BlenderMCPServer._save_image_with_extension_check(
        url="https://example/image.bin",
        requested_path=requested_path,
    )

    # The rewritten path must end in .jpg
    assert rewritten.endswith(".jpg"), f"got {rewritten}"
    assert os.path.exists(rewritten)
    # The originally-requested .png path must NOT be created
    assert not os.path.exists(requested_path)


def test_get_scene_info_full_returns_all_objects(monkeypatch):
    """With full=True, get_scene_info returns every object in the scene
    (no 10-item cap), each with name + type + bbox_center summary."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    # Build 30 fake scene objects
    class FakeObj:
        def __init__(self, name, otype="MESH"):
            self.name = name
            self.type = otype
            class V:
                x = y = z = 0.0
            self.location = V()
            self.data = type("Data", (), {"polygons": [object()] * 5})()
            self.bound_box = [(0, 0, 0)] * 8
            self.matrix_world = None
            self.children = []

    objects = [FakeObj(f"Obj_{i:02d}") for i in range(30)]
    addon.bpy.context.scene.objects = objects
    addon.bpy.context.scene.name = "TestScene"
    addon.bpy.data.materials = [object(), object()]
    addon.bpy.app.version = (5, 1, 1)
    addon.bpy.app.version_string = "5.1.1 Release"

    server = addon.BlenderMCPServer.__new__(addon.BlenderMCPServer)
    short = server.get_scene_info(full=False)
    assert len(short["objects"]) == 10, "default cap should remain 10"
    assert short["object_count"] == 30

    full = server.get_scene_info(full=True)
    assert len(full["objects"]) == 30, "full=True must return all 30"
    assert full["object_count"] == 30
    # Each entry has type + poly count + name (lighter than vertices/materials)
    for o in full["objects"]:
        assert "name" in o
        assert "type" in o
        assert "poly_count" in o


def test_get_object_info_batch_returns_dict_keyed_by_name(monkeypatch):
    """A list-of-names input returns a dict {name: info_or_error}.
    Single-name input still returns a flat info dict (BC-preserving)."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    class FakeObj:
        def __init__(self, name):
            self.name = name
            self.type = "MESH"
            class V:
                x = y = z = 0.0
            self.location = V()
            self.rotation_euler = V()
            self.scale = V()
            self.scale.x = self.scale.y = self.scale.z = 1.0
            self.visible_get = lambda: True
            self.material_slots = []
            self.bound_box = [(0, 0, 0)] * 8
            self.data = type("Data", (), {
                "vertices": [], "edges": [], "polygons": [],
            })()
            self.matrix_world = None

    pool = {n: FakeObj(n) for n in ("Cube", "Sphere", "Light")}
    addon.bpy.data.objects.get = lambda n: pool.get(n)

    server = addon.BlenderMCPServer.__new__(addon.BlenderMCPServer)

    # Single name (BC) — flat dict with "name" key
    flat = server.get_object_info("Cube")
    assert flat["name"] == "Cube"
    assert "objects" not in flat

    # Batch — dict keyed by name
    batch = server.get_object_info(names=["Cube", "Sphere", "Missing"])
    assert isinstance(batch, dict)
    assert "objects" in batch
    assert set(batch["objects"].keys()) == {"Cube", "Sphere", "Missing"}
    assert batch["objects"]["Cube"]["name"] == "Cube"
    assert batch["objects"]["Sphere"]["name"] == "Sphere"
    assert "error" in batch["objects"]["Missing"]
