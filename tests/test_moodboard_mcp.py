"""Smoke tests for Slice 6 MCP tools.

The pure-Python modules (_style_vocab, _moodboard, _sku_parse) have
their own unit-test coverage. These tests only verify that the four
new MCP tools are registered with the expected signatures.
"""
from __future__ import annotations

import inspect

from blender_mcp import server


def test_slice6_tools_registered():
    expected = (
        "generate_moodboard_candidates",
        "lock_moodboard",
        "place_furniture_from_style",
        "extract_sku_from_url",
    )
    missing = [name for name in expected if not hasattr(server, name)]
    assert not missing, f"missing tools: {missing}"


def test_generate_moodboard_candidates_signature():
    sig = inspect.signature(server.generate_moodboard_candidates)
    params = set(sig.parameters)
    expected = {"ctx", "project_root", "style_slug", "space_type", "n"}
    assert expected.issubset(params), (
        f"missing params: {expected - params}"
    )


def test_lock_moodboard_signature():
    sig = inspect.signature(server.lock_moodboard)
    params = set(sig.parameters)
    expected = {
        "ctx", "project_root", "style_slug",
        "selected_image_paths", "palette_override",
    }
    assert expected.issubset(params), (
        f"missing params: {expected - params}"
    )


def test_place_furniture_from_style_signature():
    sig = inspect.signature(server.place_furniture_from_style)
    params = set(sig.parameters)
    expected = {
        "ctx", "style_slug", "furniture_category",
        "target_zone_object", "sketchfab_query_override",
    }
    assert expected.issubset(params), (
        f"missing params: {expected - params}"
    )


def test_extract_sku_from_url_signature():
    sig = inspect.signature(server.extract_sku_from_url)
    params = set(sig.parameters)
    expected = {"ctx", "url", "page_html", "category_hint"}
    assert expected.issubset(params), (
        f"missing params: {expected - params}"
    )
