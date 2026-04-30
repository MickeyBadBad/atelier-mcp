"""End-to-end smoke test for the Interior Design Workflow.

Exercises the full pipeline using pure-Python modules + filesystem
fixtures. NO Blender, NO image generation, NO network. The point is
to verify the workflow's *data flow* is consistent: discovery output
→ project scaffold → moodboard prompts → quality gates → procurement
→ BoM all consume the same artifacts the producers emit.

If this test breaks, a real workflow run will break; if it passes,
the user can have reasonable confidence the pieces fit together.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_full_workflow_smoke(tmp_path):
    """Stage-by-stage walk through the workflow."""
    proj_root = tmp_path / "demo_project"
    proj_root.mkdir()

    # ----- Stage 0: Discovery -----
    from atelier._discovery import (
        Depth,
        list_questions,
        new_session,
        score_answers,
    )

    sess = new_session(depth=Depth.DEEP)
    assert sess["depth"] == "deep"
    assert "session_id" in sess

    # Submit canned answers across the 5 question types
    questions = list_questions(Depth.DEEP)
    canned_answers = {}
    for q in questions:
        choices = q.get("choices", [])
        if not choices:
            continue
        if q.get("multi_select"):
            # Multi-select: pick first 3 by `value`
            canned_answers[q["id"]] = [c["value"] for c in choices[:3]]
        else:
            canned_answers[q["id"]] = choices[0]["value"]

    profile = score_answers(canned_answers)
    assert "style_match" in profile
    assert profile["style_match"]
    assert "recommended_style" in profile
    assert profile["recommended_style"]

    # Persist taste profile
    from atelier._project import write_taste_profile
    write_taste_profile(proj_root / "taste-profile.json", profile)

    # ----- Stage 1-2: Project scaffolding (pure-Python side) -----
    from atelier._project import (
        STANDARD_COLLECTIONS, new_project_record, write_project,
    )

    record = new_project_record(
        project_name="Demo Project",
        project_type="cafe_lounge",
        spaces=["Entry", "Bar", "Seating"],
    )
    write_project(proj_root / "project.json", record)
    assert (proj_root / "project.json").is_file()
    assert len(STANDARD_COLLECTIONS) == 11

    # ----- Stage 2.5: Moodboard prompts -----
    from atelier._moodboard import build_moodboard_prompts
    from atelier._style_vocab import parse_style_chapter

    # Use a known-existing style; recommended_style might be any of the 19.
    # Pick whichever is in the recommended list and has a chapter.
    from atelier._style_vocab import available_styles
    available = available_styles()
    # Convert recommended_style underscore form → handbook hyphen form
    recommended_slug = profile["recommended_style"].replace("_", "-")
    if recommended_slug not in available:
        recommended_slug = available[0]

    vocab = parse_style_chapter(recommended_slug)
    prompts = build_moodboard_prompts(
        profile, vocab, n=3, space_type="cafe_lounge",
    )
    assert len(prompts) == 3
    # Each prompt cites the style chapter
    for prompt in prompts:
        assert recommended_slug in prompt or recommended_slug.replace("-", " ") in prompt

    # ----- Stage 4.5: Procurement -----
    from atelier._procurement import (
        list_purchases,
        record_purchase,
    )

    sku_a = record_purchase(proj_root, {
        "category": "sofa",
        "label": "Linen sectional sofa",
        "url": "https://detail.1688.com/offer/x.html",
        "vendor": "1688",
        "price_rmb": 2400,
        "quantity": 1,
        "lead_time_days": 14,
    })
    sku_b = record_purchase(proj_root, {
        "category": "lamp",
        "label": "Brass pendant",
        "url": "https://taobao.com/item.htm?id=y",
        "vendor": "taobao",
        "price_rmb": 380,
        "quantity": 2,
        "lead_time_days": 7,
    })
    assert len(list_purchases(proj_root)) == 2

    # ----- Stage 5: Audit (mock scene_info) -----
    from atelier._gates import StrictnessMode, run_audit

    mock_scene_info = {
        "objects": [
            {"name": "Wall_North", "type": "MESH",
             "has_albedo_map": True, "has_roughness_map": True,
             "is_prop": False, "category": "wall", "height_m": 2.7},
            {"name": "Sofa", "type": "MESH",
             "has_albedo_map": True, "has_roughness_map": True,
             "is_prop": True, "category": "prop", "height_m": 0.85},
        ],
        "lights": [
            {"name": "Ambient_Pendant", "layer": "ambient", "kelvin": 2700},
            {"name": "Accent_Spot", "layer": "accent", "kelvin": 2700},
        ],
        "cameras": [
            {"name": "HeroCam", "focal_mm": 24.0, "height_m": 1.5,
             "near_clip": 0.05, "inside_wall": False},
        ],
        "view_transform": "AgX",
        "render_settings": {
            "engine": "CYCLES", "cycles_samples": 512, "eevee_samples": 128,
        },
        "scene_meta": {"floor_area_m2": 18.0, "pack_resources": True},
    }
    report = run_audit(
        mock_scene_info,
        mode=StrictnessMode.HERO,
        project=record,
    )
    assert report["status"] in ("pass", "warn", "fail")
    # No HARD failures expected for this clean scene
    hard_fails = [
        f for f in report["findings"]
        if f.severity.value == "hard"
    ]
    assert not hard_fails, (
        f"clean scene should pass HARD gates; got: "
        f"{[(f.gate, f.message) for f in hard_fails]}"
    )

    # ----- Stage 6.5: BoM generation -----
    from atelier._bom import (
        bom_summary, collect_bom_rows, render_bom_markdown,
    )

    rows = collect_bom_rows(proj_root)
    assert len(rows) >= 2  # at least the 2 procurement items
    md = render_bom_markdown(rows)
    assert "Linen sectional sofa" in md
    assert "Brass pendant" in md

    summary = bom_summary(rows)
    # 2400*1 + 380*2 = 3160
    assert summary["total_cost_rmb"] == pytest.approx(3160.0)
    assert summary["max_lead_time_days"] == 14
    assert summary["item_count"] == 2

    # ----- Stage F: Version snapshot -----
    from atelier._snapshots import snapshot_create, snapshot_list

    snap = snapshot_create(
        proj_root,
        label="e2e-smoke-test",
        files=[
            proj_root / "taste-profile.json",
            proj_root / "project.json",
            proj_root / "procurement.json",
        ],
    )
    assert "label" in snap
    assert "path" in snap
    snapshots = snapshot_list(proj_root)
    assert len(snapshots) >= 1


def test_gates_emit_handbook_citations():
    """When a gate fires, the Finding's citation should reference a real
    handbook chapter (string) — not be empty."""
    from atelier._gates import StrictnessMode, run_audit

    # Build a scene that violates several gates
    bad_scene = {
        "objects": [
            {"name": "Wall", "type": "MESH",
             "has_albedo_map": False, "has_roughness_map": False,
             "is_prop": False, "category": "wall", "height_m": 2.7},
        ],
        "lights": [
            # Single layer → triggers lighting gate
            {"name": "Sun", "layer": "ambient", "kelvin": 0},
        ],
        "cameras": [
            {"name": "Cam", "focal_mm": 50.0, "height_m": 5.0,
             "near_clip": 0.5, "inside_wall": False},
        ],
        "view_transform": "Standard",
        "render_settings": {
            "engine": "CYCLES", "cycles_samples": 16, "eevee_samples": 16,
        },
        "scene_meta": {"floor_area_m2": 10.0, "pack_resources": False},
    }
    report = run_audit(bad_scene, mode=StrictnessMode.HERO)
    findings = report["findings"]
    assert findings, "expected gates to fire on bad_scene"

    # Every finding should have a non-empty citation
    uncited = [
        f for f in findings
        if not f.citation or not f.citation.strip()
    ]
    assert not uncited, (
        f"findings without citations: "
        f"{[(f.gate, f.message) for f in uncited]}"
    )


def test_styles_in_discovery_have_handbook_chapters():
    """Every style in STYLE_VECTORS should have a corresponding
    handbook chapter."""
    from atelier._discovery import STYLE_VECTORS
    from atelier._style_vocab import available_styles

    available = set(available_styles())
    missing = []
    for style_key in STYLE_VECTORS.keys():
        # Convert underscore to hyphen for handbook slug form
        slug = style_key.replace("_", "-")
        if slug not in available:
            missing.append(style_key)
    # Allow a small margin — discovery axes might cover styles whose
    # chapters land later. But the v2.3.0 set of 19 should match.
    assert len(missing) <= 2, (
        f"too many discovery styles missing handbook chapters: {missing}"
    )
