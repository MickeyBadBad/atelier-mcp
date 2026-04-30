"""Tests for style chapter parsing."""
from __future__ import annotations

import pytest

from atelier._style_vocab import (
    StyleVocabError,
    available_styles,
    parse_style_chapter,
)


def test_available_styles_includes_known():
    styles = available_styles()
    expected = {
        "scandinavian", "japanese-wabi-sabi", "modern-minimal",
        "speakeasy", "industrial-loft",
    }
    missing = expected - set(styles)
    assert not missing, f"missing: {missing}"


def test_parse_unknown_style_raises():
    with pytest.raises(StyleVocabError):
        parse_style_chapter("not-a-real-style")


def test_parse_scandinavian_kelvin_range():
    vocab = parse_style_chapter("scandinavian")
    lo, hi = vocab.kelvin_range
    # Per the chapter, scandinavian sits at 2200-2700K warm end
    assert 2000 <= lo <= 2500
    assert 2500 <= hi <= 3000


def test_parse_scandinavian_palette_hex_codes():
    vocab = parse_style_chapter("scandinavian")
    # Should have at least one dominant + one accent
    assert len(vocab.palette_60_30_10) >= 2
    for entry in vocab.palette_60_30_10:
        assert "hex" in entry
        # Hex should be valid 6-digit
        for hex_value in entry["hex"]:
            assert hex_value.startswith("#")
            assert len(hex_value) == 7


def test_parse_speakeasy_palette_is_warm():
    vocab = parse_style_chapter("speakeasy")
    # All hex values should not be majority blue
    for entry in vocab.palette_60_30_10:
        for hex_str in entry["hex"]:
            r = int(hex_str[1:3], 16)
            g = int(hex_str[3:5], 16)
            b = int(hex_str[5:7], 16)
            # Warm = R+G dominant; allow some neutral grays
            if r + g + b > 60:  # not pitch-black
                # Speakeasy dark palette OK; just check not strongly blue
                assert b <= max(r, g) + 30, f"{hex_str} reads cool/blue"


def test_parse_materials_has_in_and_out():
    vocab = parse_style_chapter("japanese-wabi-sabi")
    assert vocab.materials_in, "materials_in should not be empty"
    assert vocab.materials_out, "materials_out should not be empty"
    # Materials are short text snippets
    for m in vocab.materials_in:
        assert isinstance(m, str)
        assert len(m) > 2


def test_parse_anchor_description_present():
    vocab = parse_style_chapter("scandinavian")
    assert vocab.anchor_description
    assert len(vocab.anchor_description) > 50  # substantial


def test_parse_extracts_reference_projects():
    vocab = parse_style_chapter("scandinavian")
    assert len(vocab.reference_projects) >= 3


def test_kelvin_range_within_lighting_md_baseline():
    """Every style's Kelvin range must fall within the 2000-6500K
    physical interior range (per lighting.md)."""
    for slug in available_styles():
        vocab = parse_style_chapter(slug)
        lo, hi = vocab.kelvin_range
        assert 1800 <= lo <= 7000, f"{slug}: low={lo} out of bounds"
        assert 1800 <= hi <= 7000, f"{slug}: high={hi} out of bounds"
        assert lo <= hi, f"{slug}: kelvin lo > hi"


def test_parse_all_styles_smoke():
    """Every style chapter must parse without crashing."""
    failures = []
    for slug in available_styles():
        try:
            vocab = parse_style_chapter(slug)
            assert vocab.slug == slug
            assert vocab.palette_60_30_10
            assert vocab.materials_in
        except Exception as e:
            failures.append((slug, str(e)))
    assert not failures, f"parse failures: {failures}"
