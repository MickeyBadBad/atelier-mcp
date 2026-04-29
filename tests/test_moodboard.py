"""Tests for moodboard prompt builder."""
from __future__ import annotations

import pytest

from blender_mcp._moodboard import (
    MoodboardError,
    build_moodboard_prompts,
    moodboard_dir,
)
from blender_mcp._project import write_taste_profile
from blender_mcp._style_vocab import parse_style_chapter


def _profile_with_style(style):
    return {
        "version": 1,
        "depth": "deep",
        "feeling_anchors": ["warm", "calm"],
        "style_axes": {
            "warmth": 0.8, "complexity": -0.3, "natural_vs_polished": 0.6,
            "contrast": 0.2, "aged_vs_new": 0.3, "symmetric_vs_organic": 0.1,
        },
        "material_pull": ["wood", "linen"],
        "material_avoid": ["chrome"],
        "style_match": {style: 0.85},
        "recommended_style": style,
    }


def test_build_returns_n_prompts():
    profile = _profile_with_style("scandinavian")
    vocab = parse_style_chapter("scandinavian")
    prompts = build_moodboard_prompts(profile, vocab, n=4, space_type="living_room")
    assert len(prompts) == 4


def test_build_prompts_are_distinct():
    profile = _profile_with_style("scandinavian")
    vocab = parse_style_chapter("scandinavian")
    prompts = build_moodboard_prompts(profile, vocab, n=5, space_type="living_room")
    assert len(set(prompts)) == 5  # all distinct


def test_build_prompts_include_palette_hex():
    profile = _profile_with_style("scandinavian")
    vocab = parse_style_chapter("scandinavian")
    prompts = build_moodboard_prompts(profile, vocab, n=2)
    # At least one hex from the palette should appear in each prompt
    palette_hexes = []
    for entry in vocab.palette_60_30_10:
        palette_hexes.extend(entry["hex"])
    assert palette_hexes
    for prompt in prompts:
        assert any(h.lower() in prompt.lower() for h in palette_hexes), \
            f"prompt missing palette hex: {prompt[:120]}..."


def test_build_prompts_mention_kelvin():
    profile = _profile_with_style("scandinavian")
    vocab = parse_style_chapter("scandinavian")
    prompts = build_moodboard_prompts(profile, vocab, n=2)
    for prompt in prompts:
        assert "K" in prompt or "kelvin" in prompt.lower()


def test_build_prompts_mention_space_type():
    profile = _profile_with_style("scandinavian")
    vocab = parse_style_chapter("scandinavian")
    prompts = build_moodboard_prompts(profile, vocab, n=2, space_type="bedroom")
    for prompt in prompts:
        assert "bedroom" in prompt.lower()


def test_build_prompts_cite_style_anchor():
    profile = _profile_with_style("scandinavian")
    vocab = parse_style_chapter("scandinavian")
    prompts = build_moodboard_prompts(profile, vocab, n=1)
    # Should include the style slug for traceability
    assert "scandinavian" in prompts[0].lower() or "scandinavi" in prompts[0].lower()


def test_n_clamped_to_reasonable_range():
    profile = _profile_with_style("scandinavian")
    vocab = parse_style_chapter("scandinavian")
    # n=0 → at least 1
    assert len(build_moodboard_prompts(profile, vocab, n=0)) == 1
    # n=20 → capped to 8
    assert len(build_moodboard_prompts(profile, vocab, n=20)) == 8


def test_moodboard_dir_under_project(tmp_path):
    proj = tmp_path / "p"
    proj.mkdir()
    d = moodboard_dir(proj, "scandinavian")
    assert "moodboards" in str(d)
    assert "scandinavian" in str(d)
    # Doesn't create the dir until the caller wants
    assert not d.exists()
