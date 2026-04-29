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


def test_apply_archviz_material_uv_scale_param_flows_to_handler(monkeypatch):
    """When the user passes uv_scale=4.0, the addon-side handler must
    propagate it to the underlying texture applier (overriding the
    genre's default). When uv_scale is None, the genre's default UV
    scale is used."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    captured = {}

    def fake_polyhaven(self, object_name, asset_id, *,
                      resolution="2k", uv_scale=None, **kwargs):
        captured["object_name"] = object_name
        captured["asset_id"] = asset_id
        captured["uv_scale"] = uv_scale
        return {"object_name": object_name, "asset_id": asset_id,
                "uv_scale_applied": uv_scale}

    # Patch the underlying texture applier — find the actual method name
    # by inspecting BlenderMCPServer for any private method with
    # "polyhaven" in its name. The convention is _apply_polyhaven_texture
    # but if the codebase uses a different name, adapt accordingly.
    candidate_names = [n for n in dir(addon.BlenderMCPServer)
                       if "polyhaven" in n.lower() and "apply" in n.lower()
                       and not n.startswith("__")]
    assert candidate_names, "couldn't find a polyhaven applier — inspect addon.py"
    applier_name = candidate_names[0]
    monkeypatch.setattr(addon.BlenderMCPServer, applier_name, fake_polyhaven)

    server = addon.BlenderMCPServer.__new__(addon.BlenderMCPServer)

    # User-supplied uv_scale overrides the genre default
    out = server.apply_archviz_material(
        object_name="Roof", genre="roof_clay_tiles", uv_scale=4.0)
    assert captured["uv_scale"] == 4.0
    assert out.get("uv_scale_applied") == 4.0

    # uv_scale=None falls through to the genre's default — non-None,
    # specific to the genre. Verify it's not the user override (4.0)
    # and it's a sensible numeric default.
    captured.clear()
    server.apply_archviz_material(
        object_name="Roof", genre="roof_clay_tiles")
    assert captured["uv_scale"] is not None
    assert captured["uv_scale"] != 4.0


def test_frame_camera_camera_xyz_overrides_orbit(monkeypatch):
    """When camera_xyz is provided, the resulting camera location must
    equal that vector exactly — orbit_deg / elevation_deg are ignored."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    class FakeVec:
        def __init__(self, x=0, y=0, z=0):
            self.x, self.y, self.z = x, y, z
        def __getitem__(self, i):
            return [self.x, self.y, self.z][i]
        def __setitem__(self, i, v):
            if i == 0: self.x = v
            elif i == 1: self.y = v
            elif i == 2: self.z = v

    cam = type("Cam", (), {})()
    cam.location = FakeVec()
    cam.rotation_euler = FakeVec()
    cam.data = type("CData", (), {"lens": 50, "sensor_width": 36})()
    cam.name = "Camera"

    def fake_get(name):
        if name == "Camera":
            return cam
        m = type("M", (), {})()
        m.matrix_world = None
        m.bound_box = [(0, 0, 0)] * 8
        m.type = "MESH"
        m.data = type("D", (), {"polygons": []})()
        m.children = []
        return m
    addon.bpy.data.objects.get = fake_get

    server = addon.BlenderMCPServer.__new__(addon.BlenderMCPServer)
    out = server.frame_camera_to_objects(
        targets=["HouseBody"],
        camera_xyz=[9.5, -8.5, 2.6],  # explicit, must be honored
        focal_mm=35,
    )
    assert out["location"] == [9.5, -8.5, 2.6]


def test_delete_objects_by_name_and_pattern(monkeypatch):
    """delete_objects can take names=[...] for explicit names and
    patterns=[...] for fnmatch globs. Returns count + sample of names
    removed."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    fake_objs = {
        "HouseBody": type("Obj", (), {"name": "HouseBody"})(),
        "Roof": type("Obj", (), {"name": "Roof"})(),
        "TestBottle_1": type("Obj", (), {"name": "TestBottle_1"})(),
        "TestBottle_2": type("Obj", (), {"name": "TestBottle_2"})(),
        "Cone.001": type("Obj", (), {"name": "Cone.001"})(),
        "Cone.002": type("Obj", (), {"name": "Cone.002"})(),
    }
    removed_names = []

    def fake_remove(obj, do_unlink=True):
        removed_names.append(obj.name)
        fake_objs.pop(obj.name, None)

    class _FakeObjectsCollection:
        """Mimics bpy.data.objects: iterable + .get(name) + .remove(obj)."""
        def __iter__(self):
            return iter(list(fake_objs.values()))
        def get(self, n):
            return fake_objs.get(n)
        def remove(self, obj, do_unlink=True):
            fake_remove(obj, do_unlink=do_unlink)

    addon.bpy.data.objects = _FakeObjectsCollection()

    server = addon.BlenderMCPServer.__new__(addon.BlenderMCPServer)
    out = server.delete_objects(
        names=["HouseBody"],  # explicit -- should NOT match (it's in keep)
        patterns=["TestBottle_*", "Cone.*"],
        keep=["HouseBody", "Roof"],
    )
    # Keep wins: HouseBody NOT removed even though listed in `names`
    assert "HouseBody" not in removed_names
    assert "Roof" not in removed_names
    # Patterns match: 2 TestBottle + 2 Cone
    assert sorted(removed_names) == ["Cone.001", "Cone.002",
                                     "TestBottle_1", "TestBottle_2"]
    assert out["removed_count"] == 4
    assert sorted(out["removed_sample"][:4]) == sorted(removed_names)


def test_apply_glass_material_routes_to_addon(monkeypatch):
    """apply_glass_material on the server side forwards a complete
    parameter dict to the addon dispatcher."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    captured = {}
    class FakeConn:
        def send_command(self, cmd, params=None):
            captured["cmd"] = cmd
            captured["params"] = params
            return {"object_name": "Window_1", "material": "Glass_Window_1"}

    if "blender_mcp.server" in sys.modules:
        del sys.modules["blender_mcp.server"]
    if "blender_mcp" in sys.modules:
        del sys.modules["blender_mcp"]

    from blender_mcp import server as srv_mod
    srv_mod.get_blender_connection = lambda: FakeConn()

    # Unwrap decorator stack to call the underlying function with kwargs
    fn = srv_mod.apply_glass_material
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    out = fn(ctx=None, object_name="Window_1",
             tint_hex="#ffc77a",
             emission_color="#ffaa55",
             emission_strength=2.0,
             transmission=0.95, roughness=0.05, ior=1.45)
    assert captured["cmd"] == "apply_glass_material"
    assert captured["params"]["object_name"] == "Window_1"
    assert captured["params"]["tint_hex"] == "#ffc77a"
    assert captured["params"]["emission_color"] == "#ffaa55"
    assert captured["params"]["emission_strength"] == 2.0
    assert captured["params"]["transmission"] == 0.95
    assert captured["params"]["roughness"] == 0.05
    assert captured["params"]["ior"] == 1.45


def test_hyper3d_auto_import_polls_until_done_then_imports(monkeypatch):
    """When auto_import=True (default), the tool polls
    poll_hyper3d_job_status until all status entries are 'Done', then
    calls import_hyper3d_asset transparently. Returns the final import
    result, not just the task UUID."""
    import sys, os, time
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if "blender_mcp.server" in sys.modules:
        del sys.modules["blender_mcp.server"]

    poll_state = {"i": 0}
    sequence = [
        {"status_list": ["Generating", "Generating"]},
        {"status_list": ["Done", "Generating"]},
        {"status_list": ["Done", "Done"]},
    ]

    class FakeConn:
        def send_command(self, cmd, params=None):
            if cmd == "create_rodin_job":
                return {"submit_time": "now", "uuid": "u-123",
                        "jobs": {"subscription_key": "sk-fake"}}
            if cmd == "poll_hyper3d_job_status":
                out = sequence[poll_state["i"]]
                poll_state["i"] = min(poll_state["i"] + 1, len(sequence) - 1)
                return out
            if cmd == "import_hyper3d_asset":
                return {"succeed": True, "name": params["name"], "type": "MESH"}
            return {"error": f"unexpected cmd {cmd}"}

    from blender_mcp import server as srv_mod
    srv_mod.get_blender_connection = lambda: FakeConn()
    monkeypatch.setattr(time, "sleep", lambda s: None)  # don't actually wait

    # Unwrap decorator stack to call the underlying function with kwargs
    fn = srv_mod.generate_hyper3d_text_to_3d
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    out = fn(ctx=None, text_prompt="brass cube", auto_import=True,
             import_name="Cube1", max_wait_seconds=10)
    assert out["succeed"] is True
    assert out["name"] == "Cube1"
    assert poll_state["i"] >= 2  # polled at least twice


def test_render_image_returns_preview_when_requested(tmp_path, monkeypatch):
    """render_image with return_preview=True returns a base64
    thumbnail in the response under `preview_b64` (PNG <= 256px)."""
    import sys, os, base64
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "addon" in sys.modules:
        del sys.modules["addon"]
    import addon

    rendered_path = str(tmp_path / "out.png")
    # Stub the actual render to write a small valid PNG (1px transparent)
    PNG_1PX = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYA"
        b"AAAAYAAjCB0C8AAAAASUVORK5CYII=")
    def fake_render(*a, **kw):
        with open(rendered_path, "wb") as f:
            f.write(PNG_1PX)
    monkeypatch.setattr(addon.bpy.ops.render, "render", fake_render)
    addon.bpy.path.abspath = lambda p: p  # mock returns passthrough
    addon.bpy.context.scene.render.filepath = rendered_path
    addon.bpy.context.scene.camera = object()  # truthy

    server = addon.BlenderMCPServer.__new__(addon.BlenderMCPServer)
    out = server.render_image(filepath=rendered_path, return_preview=True,
                              preview_max_dim=128)
    assert out["filepath"] == rendered_path
    assert "preview_b64" in out
    assert isinstance(out["preview_b64"], str)
    assert len(out["preview_b64"]) > 0
    # Should be valid base64
    base64.b64decode(out["preview_b64"])


def test_zero_result_search_includes_query_help_hint(monkeypatch):
    """When a Sketchfab search returns 0 results, the response includes
    a `hint` and a `cheatsheet_call` pointing at asset_query_help.
    Same for PolyHaven + ambientCG."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "blender_mcp.server" in sys.modules:
        del sys.modules["blender_mcp.server"]

    from blender_mcp._filters import attach_zero_result_hint

    sketchfab_zero = {"results": []}
    out = attach_zero_result_hint(sketchfab_zero, service="sketchfab")
    assert out["results"] == []
    assert "hint" in out
    assert "asset_query_help" in out["cheatsheet_call"]
    assert "sketchfab" in out["cheatsheet_call"]

    # PolyHaven
    polyhaven_zero = {"assets": {}, "total_count": 0, "returned_count": 0}
    out = attach_zero_result_hint(polyhaven_zero, service="polyhaven")
    assert "hint" in out
    assert "polyhaven" in out["cheatsheet_call"]

    # ambientCG variants
    ambient_zero_a = {"assets": []}
    ambient_zero_b = {"foundAssets": {}}
    for raw in (ambient_zero_a, ambient_zero_b):
        out = attach_zero_result_hint(raw, service="ambientcg")
        assert "hint" in out

    # Non-zero result is passed through untouched
    nonzero = {"results": [{"uid": "x"}]}
    out = attach_zero_result_hint(nonzero, service="sketchfab")
    assert "hint" not in out

