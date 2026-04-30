"""Smoke tests for the Atelier CLI."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from atelier.cli import build_parser, main


def test_parser_builds():
    parser = build_parser()
    assert parser.prog == "atelier"


def test_parser_subcommands():
    parser = build_parser()
    expected = {
        "init", "discover", "audit", "bom",
        "moodboard", "handbook", "styles", "version",
    }
    sub = next(
        a for a in parser._actions
        if isinstance(a, getattr(__import__("argparse"), "_SubParsersAction"))
    )
    assert expected.issubset(set(sub.choices.keys()))


def test_styles_runs(capsys):
    rc = main(["styles"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "scandinavian" in out
    assert "Kelvin" in out


def test_handbook_list(capsys):
    rc = main(["handbook"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "lighting" in out  # one of the chapters


def test_handbook_read_chapter(capsys):
    rc = main(["handbook", "codes"])
    assert rc == 0
    out = capsys.readouterr().out
    # Chapter starts with markdown title
    assert out.lstrip().startswith("#")


def test_handbook_search(capsys):
    rc = main(["handbook", "--query", "Kelvin"])
    # 0 = matches found; 1 = none found. Either way the call shouldn't crash
    assert rc in (0, 1)


def test_init_creates_project(tmp_path, capsys):
    proj = tmp_path / "demo"
    rc = main([
        "init", "demo",
        "--type", "cafe_lounge",
        "--root", str(proj),
        "--spaces", "Entry", "Bar",
    ])
    assert rc == 0
    assert (proj / "project.json").is_file()
    assert (proj / "taste-profile.json").is_file()
    record = json.loads((proj / "project.json").read_text())
    assert record["project_type"] == "cafe_lounge"


def test_init_rejects_bad_type(tmp_path, capsys):
    rc = main([
        "init", "x",
        "--type", "spaceship",
        "--root", str(tmp_path / "x"),
    ])
    assert rc == 2


def test_discover_auto_writes_profile(tmp_path):
    out = tmp_path / "profile.json"
    rc = main(["discover", "--depth", "quick", "--auto", "--out", str(out)])
    assert rc == 0
    assert out.is_file()
    profile = json.loads(out.read_text())
    assert "style_match" in profile
    assert "recommended_style" in profile


def test_audit_runs_with_clean_scene(tmp_path):
    scene_info = {
        "objects": [
            {"name": "Wall", "type": "MESH",
             "has_albedo_map": True, "has_roughness_map": True,
             "is_prop": False, "category": "wall", "height_m": 2.7},
        ],
        "lights": [
            {"name": "Amb", "layer": "ambient", "kelvin": 2700},
            {"name": "Acc", "layer": "accent", "kelvin": 2700},
        ],
        "cameras": [
            {"name": "Cam", "focal_mm": 24.0, "height_m": 1.5,
             "near_clip": 0.05, "inside_wall": False},
        ],
        "view_transform": "AgX",
        "render_settings": {
            "engine": "CYCLES", "cycles_samples": 512, "eevee_samples": 128,
        },
        "scene_meta": {"floor_area_m2": 18.0, "pack_resources": True},
    }
    info_path = tmp_path / "scene.json"
    info_path.write_text(json.dumps(scene_info), encoding="utf-8")
    rc = main(["audit", str(info_path), "--mode", "exploration"])
    assert rc == 0


def test_bom_empty_project(tmp_path, capsys):
    proj = tmp_path / "empty"
    proj.mkdir()
    rc = main(["bom", str(proj), "--format", "markdown"])
    assert rc == 0


def test_moodboard_requires_style_or_profile(tmp_path):
    proj = tmp_path / "p"
    proj.mkdir()
    # Write a profile WITHOUT recommended_style
    (proj / "taste-profile.json").write_text(json.dumps({"version": 1}), encoding="utf-8")
    rc = main(["moodboard", str(proj)])
    assert rc == 2  # error: no style


def test_moodboard_with_explicit_style(tmp_path, capsys):
    proj = tmp_path / "p"
    proj.mkdir()
    (proj / "taste-profile.json").write_text(
        json.dumps({"version": 1, "feeling_anchors": ["warm"]}),
        encoding="utf-8",
    )
    rc = main(["moodboard", str(proj), "--style", "scandinavian", "-n", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "scandinavian" in out.lower()


def test_no_command_prints_help(capsys):
    rc = main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atelier" in out.lower()


def test_version_flag(capsys):
    rc = main(["--version"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atelier" in out.lower()
