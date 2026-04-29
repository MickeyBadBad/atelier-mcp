"""Per-tool phase tags + a list_tools_by_phase MCP helper.

Phases group the ~58 fork tools into the workflow stages an LLM client
typically traverses: discovery -> assets -> materials -> geometry -> camera
-> lighting -> render. The mapping is metadata-only — it doesn't change
behavior, only helps clients build mental maps.
"""
from __future__ import annotations
from typing import Iterable


# (tool_name -> phase). Tools not listed default to "uncategorized".
PHASES: dict[str, list[str]] = {
    "discovery": [
        "get_scene_info", "get_object_info", "asset_query_help",
    ],
    "diagnostics": [
        "check_services",
        "get_polyhaven_status", "get_sketchfab_status",
        "get_hyper3d_status", "get_hunyuan3d_status",
        "get_tripo3d_status", "get_meshy_status",
        "get_ambientcg_status", "get_openai_status", "get_codex_status",
        "verify_object_grounded", "get_viewport_screenshot",
    ],
    "asset_search": [
        "search_polyhaven_assets", "get_polyhaven_categories",
        "search_sketchfab_models", "get_sketchfab_model_preview",
        "search_ambientcg_assets",
    ],
    "asset_download": [
        "download_polyhaven_asset", "download_sketchfab_model",
        "download_ambientcg_asset", "set_texture",
    ],
    "asset_generation": [
        "generate_3d_smart",
        "generate_tripo3d_text_to_3d", "generate_tripo3d_image_to_3d",
        "generate_meshy_text_to_3d", "generate_meshy_image_to_3d",
        "generate_hyper3d_text_to_3d", "generate_hyper3d_image_to_3d",
        "poll_hyper3d_job_status", "import_hyper3d_asset",
        "generate_hunyuan3d_model", "poll_hunyuan_job_status",
        "import_hunyuan3d_asset",
        "generate_image_codex", "generate_image_openai",
    ],
    "material": [
        "apply_material_color", "apply_archviz_material",
        "list_archviz_genres", "apply_glass_material",
    ],
    "geometry": [
        "boolean_cutout", "mesh_cleanup", "place_on_ground",
        "scatter_on_surface", "array_duplicate", "curve_extrude_profile",
    ],
    "camera": [
        "set_camera_view", "frame_camera_to_objects",
    ],
    "lighting": [
        "setup_lighting", "set_world_hdri_rotation",
    ],
    "render": [
        "render_image",
    ],
    "export": [
        "quick_export",
    ],
    "scene_management": [
        "delete_objects", "execute_blender_code",
    ],
    "config": [
        "get_usage_report", "set_usage_budget", "reset_usage_counters",
    ],
}


def phase_for_tool(tool_name: str) -> str:
    """Return the phase key for a given tool name, or 'uncategorized'."""
    for phase, tools in PHASES.items():
        if tool_name in tools:
            return phase
    return "uncategorized"


def list_tools_by_phase() -> dict[str, list[str]]:
    """Return a copy of the phase -> [tools] mapping."""
    return {phase: list(tools) for phase, tools in PHASES.items()}
