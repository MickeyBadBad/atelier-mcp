"""Tests for the per-service query format guide module (v2.1.0).

Coverage:
- All 6 services have a complete guide entry
- Each entry has the same required keys (so LLM clients can rely on
  shape across services)
- `asset_query_help_data` returns sensible structure for 'all', a known
  service, and an unknown service
"""
from __future__ import annotations
import pytest

from blender_mcp._query_guide import (
    _GUIDE,
    asset_query_help_data,
)


REQUIRED_KEYS = {
    "kind", "how_it_searches", "query_format", "categories",
    "pitfalls", "examples", "fallback_ladder",
}

EXPECTED_SERVICES = {
    "polyhaven", "ambientcg", "sketchfab",
    "tripo3d", "meshy", "hyper3d",
}


def test_all_expected_services_present():
    assert set(_GUIDE.keys()) == EXPECTED_SERVICES


def test_every_service_has_required_keys():
    """Shape must be uniform so LLM clients can navigate predictably."""
    for service, guide in _GUIDE.items():
        missing = REQUIRED_KEYS - set(guide.keys())
        assert not missing, (
            f"Service '{service}' is missing required keys: {missing}"
        )


def test_pitfalls_and_fallback_ladder_are_non_empty_lists():
    """Both fields must contain at least one actionable item."""
    for service, guide in _GUIDE.items():
        assert isinstance(guide["pitfalls"], list), service
        assert len(guide["pitfalls"]) >= 1, service
        assert isinstance(guide["fallback_ladder"], list), service
        assert len(guide["fallback_ladder"]) >= 1, service


def test_examples_have_user_intent_and_do_keys():
    """Each example must show what the user wanted and what the right
    call looks like — the do-not field is optional but encouraged."""
    for service, guide in _GUIDE.items():
        for i, ex in enumerate(guide["examples"]):
            assert "user_intent" in ex, f"{service}[{i}] missing user_intent"
            assert "do" in ex, f"{service}[{i}] missing do"


def test_polyhaven_is_documented_as_categories_only():
    """The defining trait of PolyHaven (no free-text search) must be
    surfaced explicitly so the LLM doesn't waste calls on free text."""
    g = _GUIDE["polyhaven"]
    assert "free-text" in g["how_it_searches"].lower() or \
           "categories" in g["how_it_searches"].lower()
    assert isinstance(g["categories"], dict)
    assert {"hdris", "textures", "models"}.issubset(g["categories"].keys())


def test_sketchfab_warns_about_long_queries():
    """Long-sentence queries returning zero is the #1 Sketchfab mistake;
    must be in pitfalls so the LLM sees it."""
    g = _GUIDE["sketchfab"]
    pitfalls_text = " ".join(g["pitfalls"]).lower()
    assert "long" in pitfalls_text or "sentence" in pitfalls_text \
           or "0" in pitfalls_text


def test_ai_gen_services_warn_about_scene_prompts():
    """Tripo3D / Meshy / Hyper3D all share the 'one object only' rule;
    ensure each one mentions it in pitfalls."""
    for ai_service in ("tripo3d", "meshy", "hyper3d"):
        g = _GUIDE[ai_service]
        haystack = (
            " ".join(g["pitfalls"]).lower()
            + " " + g["query_format"].lower()
        )
        assert (
            "one object" in haystack
            or "scene" in haystack
            or "single" in haystack
        ), f"{ai_service} guide should warn against multi-object/scene prompts"


# ----- asset_query_help_data() -----

def test_asset_query_help_data_default_returns_all_services():
    out = asset_query_help_data()
    assert out["service"] == "all"
    assert set(out["available_services"]) == EXPECTED_SERVICES
    assert isinstance(out["guide"], dict)
    assert "polyhaven" in out["guide"]
    assert "tip" in out  # high-level overview hint included


def test_asset_query_help_data_all_alias():
    """'all', '*', '', None, 'ALL' all map to full-guide."""
    for arg in (None, "all", "ALL", "*", "", "  All  "):
        out = asset_query_help_data(arg)
        assert out["service"] == "all", f"alias {arg!r} did not normalize"


def test_asset_query_help_data_known_service_returns_single_guide():
    out = asset_query_help_data("polyhaven")
    assert out["service"] == "polyhaven"
    assert isinstance(out["guide"], dict)
    assert "how_it_searches" in out["guide"]
    assert "examples" in out["guide"]


def test_asset_query_help_data_case_insensitive():
    for arg in ("PolyHaven", "POLYHAVEN", "polyhaven", " polyhaven "):
        out = asset_query_help_data(arg)
        assert out["service"] == "polyhaven", f"alias {arg!r} did not normalize"


def test_asset_query_help_data_unknown_service_returns_error_envelope():
    """Unknown service → returns an error field plus available list,
    not a raise — so an LLM client gets a hint instead of a crash."""
    out = asset_query_help_data("nope-not-a-service")
    assert out["guide"] is None
    assert "error" in out
    assert "available" in out["error"].lower()
    assert isinstance(out["available_services"], list)
