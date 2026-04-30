"""Tests for the quality-gate validators (Slice 3)."""
from __future__ import annotations

import pytest

from atelier._gates import (
    Finding,
    Severity,
    StrictnessMode,
    check_materials,
    check_lighting_layers,
    check_kelvin_range,
    check_camera_params,
    check_color_management,
    check_render_samples,
    check_prop_density,
    check_scale_sanity,
    check_texture_packing,
    run_audit,
)


# ----- Helpers -----

def _scene(
    objects=None,
    lights=None,
    cameras=None,
    view_transform="AgX",
    cycles_samples=512,
    eevee_samples=128,
    floor_area_m2=20.0,
    pack_resources=True,
):
    """Build a minimal scene_info dict for tests."""
    return {
        "objects": objects or [],
        "lights": lights or [],
        "cameras": cameras or [],
        "view_transform": view_transform,
        "render_settings": {
            "engine": "CYCLES",
            "cycles_samples": cycles_samples,
            "eevee_samples": eevee_samples,
        },
        "scene_meta": {
            "floor_area_m2": floor_area_m2,
            "pack_resources": pack_resources,
        },
    }


# ----- check_materials -----

def test_materials_pass_when_all_objects_have_pbr():
    scene = _scene(objects=[
        {"name": "Wall", "type": "MESH", "has_albedo_map": True, "has_roughness_map": True},
        {"name": "Floor", "type": "MESH", "has_albedo_map": True, "has_roughness_map": False},
    ])
    findings = check_materials(scene)
    assert findings == []


def test_materials_fail_when_object_lacks_albedo_and_roughness():
    scene = _scene(objects=[
        {"name": "Wall", "type": "MESH", "has_albedo_map": False, "has_roughness_map": False},
    ])
    findings = check_materials(scene)
    assert len(findings) == 1
    assert findings[0].severity == Severity.HARD
    assert "Wall" in findings[0].message
    assert "materials.md" in findings[0].citation.lower()


def test_materials_skips_temp_objects():
    """Temp scaffolds (names starting with _) shouldn't trigger the gate."""
    scene = _scene(objects=[
        {"name": "_temp_helper", "type": "MESH",
         "has_albedo_map": False, "has_roughness_map": False},
    ])
    assert check_materials(scene) == []


# ----- check_lighting_layers -----

def test_lighting_pass_with_two_layers():
    scene = _scene(lights=[
        {"name": "Ambient1", "layer": "ambient"},
        {"name": "Accent1", "layer": "accent"},
    ])
    assert check_lighting_layers(scene) == []


def test_lighting_fail_with_only_one_layer():
    scene = _scene(lights=[{"name": "OnlyLight", "layer": "ambient"}])
    findings = check_lighting_layers(scene)
    assert len(findings) == 1
    assert findings[0].severity == Severity.HARD
    assert "lighting.md" in findings[0].citation.lower()


def test_lighting_fail_with_no_lights():
    scene = _scene(lights=[])
    findings = check_lighting_layers(scene)
    assert len(findings) == 1
    assert findings[0].severity == Severity.HARD


# ----- check_kelvin_range -----

def test_kelvin_pass_within_residential_range():
    scene = _scene(lights=[
        {"name": "L1", "layer": "ambient", "kelvin": 2800},
        {"name": "L2", "layer": "accent", "kelvin": 2700},
    ])
    project = {"project_type": "residential_apartment"}
    assert check_kelvin_range(scene, project) == []


def test_kelvin_fail_when_residential_at_5000k():
    scene = _scene(lights=[{"name": "L1", "layer": "ambient", "kelvin": 5000}])
    project = {"project_type": "residential_apartment"}
    findings = check_kelvin_range(scene, project)
    assert len(findings) == 1
    assert findings[0].severity == Severity.SOFT


def test_kelvin_no_fail_when_no_project_metadata():
    """Without project_type we can't enforce a range — skip the gate."""
    scene = _scene(lights=[{"name": "L1", "layer": "ambient", "kelvin": 5000}])
    assert check_kelvin_range(scene, project=None) == []


# ----- check_camera_params -----

def test_camera_pass_with_sane_params():
    scene = _scene(cameras=[
        {"name": "Hero", "focal_mm": 24, "height_m": 1.5, "near_clip": 0.01, "inside_wall": False},
    ])
    assert check_camera_params(scene) == []


def test_camera_fail_focal_too_long():
    scene = _scene(cameras=[
        {"name": "Hero", "focal_mm": 50, "height_m": 1.5, "near_clip": 0.01, "inside_wall": False},
    ])
    findings = check_camera_params(scene)
    assert any(f.severity == Severity.HARD for f in findings)
    assert any("focal" in f.message.lower() for f in findings)


def test_camera_fail_inside_wall():
    scene = _scene(cameras=[
        {"name": "Hero", "focal_mm": 24, "height_m": 1.5, "near_clip": 0.01, "inside_wall": True},
    ])
    findings = check_camera_params(scene)
    assert len(findings) >= 1
    assert any("wall" in f.message.lower() for f in findings)


def test_camera_no_findings_when_no_cameras():
    """No cameras → no camera findings (other gates may catch it)."""
    assert check_camera_params(_scene(cameras=[])) == []


# ----- check_color_management -----

def test_color_pass_with_agx():
    assert check_color_management(_scene(view_transform="AgX")) == []


def test_color_pass_with_filmic():
    assert check_color_management(_scene(view_transform="Filmic")) == []


def test_color_fail_with_standard():
    findings = check_color_management(_scene(view_transform="Standard"))
    assert len(findings) == 1
    assert findings[0].severity == Severity.HARD
    assert "render-output.md" in findings[0].citation.lower()


# ----- check_render_samples -----

def test_render_samples_pass_for_hero_at_512():
    scene = _scene(cycles_samples=512, eevee_samples=128)
    assert check_render_samples(scene, mode=StrictnessMode.HERO) == []


def test_render_samples_warn_when_below_hero_floor():
    scene = _scene(cycles_samples=64, eevee_samples=32)
    findings = check_render_samples(scene, mode=StrictnessMode.HERO)
    assert len(findings) == 1
    assert findings[0].severity == Severity.SOFT


def test_render_samples_pass_at_64_for_exploration():
    """Exploration mode is lenient on samples."""
    scene = _scene(cycles_samples=64, eevee_samples=32)
    assert check_render_samples(scene, mode=StrictnessMode.EXPLORATION) == []


# ----- check_prop_density -----

def test_prop_density_pass_with_enough_props():
    scene = _scene(
        objects=[{"name": f"Prop{i}", "type": "MESH", "is_prop": True}
                 for i in range(20)],
        floor_area_m2=20.0,  # 1 prop / m² → at default 0.5 threshold pass
    )
    assert check_prop_density(scene) == []


def test_prop_density_warn_when_too_sparse():
    scene = _scene(
        objects=[{"name": "Sofa", "type": "MESH", "is_prop": True}],
        floor_area_m2=40.0,  # 1 prop in 40 m² is too sparse
    )
    findings = check_prop_density(scene)
    assert len(findings) == 1
    assert findings[0].severity == Severity.SOFT


# ----- check_scale_sanity -----

def test_scale_pass_for_normal_sofa():
    scene = _scene(objects=[
        {"name": "Sofa1", "type": "MESH", "category": "sofa", "height_m": 0.85},
    ])
    assert check_scale_sanity(scene) == []


def test_scale_fail_for_giant_sofa():
    scene = _scene(objects=[
        {"name": "Sofa1", "type": "MESH", "category": "sofa", "height_m": 2.5},
    ])
    findings = check_scale_sanity(scene)
    assert len(findings) == 1
    assert findings[0].severity == Severity.HARD


def test_scale_pass_for_door_in_range():
    scene = _scene(objects=[
        {"name": "Door1", "type": "MESH", "category": "door", "height_m": 2.1},
    ])
    assert check_scale_sanity(scene) == []


def test_scale_fail_for_undersized_door():
    scene = _scene(objects=[
        {"name": "Door1", "type": "MESH", "category": "door", "height_m": 1.5},
    ])
    findings = check_scale_sanity(scene)
    assert len(findings) == 1


# ----- check_texture_packing -----

def test_texture_packing_info_when_unpacked_in_exploration():
    scene = _scene(pack_resources=False)
    findings = check_texture_packing(scene, mode=StrictnessMode.EXPLORATION)
    # Exploration mode → INFO-only severity
    if findings:
        assert findings[0].severity == Severity.INFO


def test_texture_packing_hard_when_unpacked_in_construction():
    scene = _scene(pack_resources=False)
    findings = check_texture_packing(scene, mode=StrictnessMode.CONSTRUCTION)
    assert len(findings) == 1
    assert findings[0].severity == Severity.HARD


def test_texture_packing_pass_when_packed():
    scene = _scene(pack_resources=True)
    assert check_texture_packing(scene, mode=StrictnessMode.HERO) == []


# ----- run_audit (integration) -----

def test_run_audit_exploration_mode_only_returns_hard_findings():
    """In exploration mode, soft + info findings are dropped."""
    scene = _scene(
        cycles_samples=32,  # would be SOFT in HERO
        view_transform="Standard",  # HARD always
        objects=[],
        lights=[],
    )
    report = run_audit(scene, mode=StrictnessMode.EXPLORATION)
    severities = {f.severity for f in report["findings"]}
    # EXPLORATION drops SOFT/INFO, keeps HARD
    assert Severity.HARD in severities
    assert Severity.SOFT not in severities


def test_run_audit_hero_mode_includes_soft_findings():
    scene = _scene(
        cycles_samples=32,
        view_transform="AgX",
        objects=[
            {"name": "Wall", "type": "MESH",
             "has_albedo_map": True, "has_roughness_map": True}
        ],
        lights=[
            {"name": "L1", "layer": "ambient"},
            {"name": "L2", "layer": "accent"},
        ],
    )
    report = run_audit(scene, mode=StrictnessMode.HERO)
    severities = {f.severity for f in report["findings"]}
    # Render samples below hero floor → SOFT
    assert Severity.SOFT in severities


def test_run_audit_returns_status_pass_when_no_blockers():
    scene = _scene(
        objects=[
            {"name": "Wall", "type": "MESH",
             "has_albedo_map": True, "has_roughness_map": True}
        ],
        lights=[
            {"name": "L1", "layer": "ambient"},
            {"name": "L2", "layer": "accent"},
        ],
        cameras=[{"name": "Hero", "focal_mm": 24, "height_m": 1.5,
                  "near_clip": 0.01, "inside_wall": False}],
    )
    report = run_audit(scene, mode=StrictnessMode.HERO)
    assert report["status"] in ("pass", "warn")
    assert "findings" in report
    assert "mode" in report


def test_run_audit_status_fail_when_hard_finding():
    scene = _scene(view_transform="Standard")
    report = run_audit(scene, mode=StrictnessMode.HERO)
    assert report["status"] == "fail"


def test_finding_carries_handbook_citation():
    """Every finding must have a non-empty citation per the spec."""
    scene = _scene(view_transform="Standard")
    report = run_audit(scene, mode=StrictnessMode.HERO)
    for f in report["findings"]:
        assert f.citation, f"finding missing citation: {f.message}"
        assert ".md" in f.citation
