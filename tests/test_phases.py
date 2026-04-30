"""Sprint 6 — tool phase taxonomy tests."""
from atelier._phases import PHASES, phase_for_tool, list_tools_by_phase


def test_phase_keys_match_curated_list():
    expected = {
        "discovery", "diagnostics", "asset_search",
        "asset_download", "asset_generation",
        "material", "geometry", "camera", "lighting",
        "render", "export", "scene_management", "config",
    }
    assert set(PHASES.keys()) == expected


def test_phase_for_known_tools():
    assert phase_for_tool("get_scene_info") == "discovery"
    assert phase_for_tool("check_services") == "diagnostics"
    assert phase_for_tool("search_polyhaven_assets") == "asset_search"
    assert phase_for_tool("download_polyhaven_asset") == "asset_download"
    assert phase_for_tool("generate_3d_smart") == "asset_generation"
    assert phase_for_tool("apply_material_color") == "material"
    assert phase_for_tool("apply_glass_material") == "material"
    assert phase_for_tool("place_on_ground") == "geometry"
    assert phase_for_tool("delete_objects") == "scene_management"
    assert phase_for_tool("frame_camera_to_objects") == "camera"
    assert phase_for_tool("setup_lighting") == "lighting"
    assert phase_for_tool("render_image") == "render"
    assert phase_for_tool("quick_export") == "export"


def test_phase_for_unknown_tool_returns_uncategorized():
    assert phase_for_tool("definitely_not_a_real_tool_name") == "uncategorized"


def test_list_tools_by_phase_groups_correctly():
    grouped = list_tools_by_phase()
    assert "discovery" in grouped
    assert "get_scene_info" in grouped["discovery"]
    assert "render_image" in grouped["render"]
