"""Tests for the discovery questionnaire module."""
from __future__ import annotations

import pytest

from atelier._discovery import (
    AXES,
    Depth,
    DiscoveryError,
    list_questions,
    midpoint_inferred_style,
    new_session,
    score_answers,
    validate_answer_payload,
)


def test_axes_canonical_set():
    """The 6 style axes are stable contract — downstream skills depend on them."""
    expected = {"warmth", "complexity", "natural_vs_polished",
                "contrast", "aged_vs_new", "symmetric_vs_organic"}
    assert set(AXES) == expected


def test_list_questions_loads_bank():
    qs = list_questions(Depth.DEEP)
    assert len(qs) >= 20
    for q in qs:
        assert "id" in q
        assert "type" in q
        assert q["type"] in (1, 2, 3, 4, 5)
        assert "text_zh" in q
        assert "text_en" in q


def test_list_questions_quick_is_subset():
    quick = list_questions(Depth.QUICK)
    deep = list_questions(Depth.DEEP)
    assert len(quick) < len(deep)
    quick_ids = {q["id"] for q in quick}
    deep_ids = {q["id"] for q in deep}
    assert quick_ids.issubset(deep_ids)


def test_list_questions_standard_includes_quick():
    quick = {q["id"] for q in list_questions(Depth.QUICK)}
    standard = {q["id"] for q in list_questions(Depth.STANDARD)}
    assert quick.issubset(standard)


def test_validate_answer_payload_rejects_unknown_id():
    with pytest.raises(DiscoveryError):
        validate_answer_payload({"q99_does_not_exist": "warm"})


def test_validate_answer_payload_rejects_unknown_choice_when_no_free_input():
    # q02_project_type has free_input=false
    with pytest.raises(DiscoveryError):
        validate_answer_payload({"q02_project_type": "purple_unicorn"})


def test_validate_answer_payload_accepts_free_text_for_free_input_only():
    # q23 is free_input_only — string answer accepted
    out = validate_answer_payload({"q23_reference_place": "Kyoto temple I visited"})
    assert "q23_reference_place" in out
    assert out["q23_reference_place"] == "Kyoto temple I visited"


def test_validate_answer_payload_accepts_free_text_when_free_input_allowed():
    # q01 has free_input=true; an unrecognized string becomes free_text
    out = validate_answer_payload({"q01_who_uses": "I run a co-living space"})
    assert "q01_who_uses" in out
    assert isinstance(out["q01_who_uses"], dict)
    assert "free_text" in out["q01_who_uses"]


def test_score_answers_produces_axes_in_unit_range():
    answers = {
        "q06_first_second_feeling": ["warm_hugged", "relaxed"],
        "q08_movie": ["kikujiro"],
        "q09_textures": ["linen", "rough_wood", "terracotta"],
        "q10_warm_vs_cool": "warm",
        "q11_sparse_vs_full": "sparse",
        "q12_wood_vs_stone": "wood",
        "q14_aged_vs_new": "aged",
        "q16_natural_vs_polished": "natural",
    }
    profile = score_answers(answers)
    assert "style_axes" in profile
    for axis_name, value in profile["style_axes"].items():
        assert -1.0 <= value <= 1.0, (
            f"axis {axis_name} out of unit range: {value}"
        )
    # Heuristic: this answer set should bias toward warmth + natural
    assert profile["style_axes"]["warmth"] > 0.1
    assert profile["style_axes"]["natural_vs_polished"] > 0.1
    assert profile["style_axes"]["complexity"] < 0.0


def test_score_answers_includes_style_match():
    """style_match projects user axes onto style ground-truth vectors."""
    answers = {
        "q10_warm_vs_cool": "warm",
        "q12_wood_vs_stone": "wood",
        "q16_natural_vs_polished": "natural",
        "q11_sparse_vs_full": "sparse",
    }
    profile = score_answers(answers)
    assert "style_match" in profile
    assert isinstance(profile["style_match"], dict)
    assert len(profile["style_match"]) >= 3
    # All scores in [0, 1]
    for name, score in profile["style_match"].items():
        assert 0.0 <= score <= 1.0


def test_score_answers_recommended_style():
    """The top of style_match becomes recommended_style."""
    answers = {
        "q06_first_second_feeling": ["relaxed", "warm_hugged"],
        "q09_textures": ["linen", "rough_wood", "terracotta"],
        "q10_warm_vs_cool": "warm",
        "q11_sparse_vs_full": "sparse",
        "q14_aged_vs_new": "aged",
        "q16_natural_vs_polished": "natural",
    }
    profile = score_answers(answers)
    assert profile["recommended_style"] is not None
    assert profile["recommended_style"] in profile["style_match"]


def test_score_answers_collects_feeling_anchors_and_material_pull():
    answers = {
        "q06_first_second_feeling": ["warm_hugged", "relaxed"],
        "q09_textures": ["linen", "rough_wood"],
    }
    profile = score_answers(answers)
    assert "warm_hugged" in profile["feeling_anchors"]
    assert "linen" in profile["material_pull"]


def test_new_session_returns_session_id_and_first_batch():
    session = new_session(depth=Depth.DEEP)
    assert "session_id" in session
    assert "batch" in session
    assert "depth" in session
    assert "total_questions" in session
    assert "next_index" in session
    assert len(session["batch"]) >= 1


def test_new_session_total_questions_matches_depth():
    deep_session = new_session(depth=Depth.DEEP)
    quick_session = new_session(depth=Depth.QUICK)
    assert deep_session["total_questions"] > quick_session["total_questions"]


def test_midpoint_inferred_style_returns_top_match():
    """At ~12 questions in, AI surfaces a hypothesis."""
    answers = {
        "q10_warm_vs_cool": "warm",
        "q11_sparse_vs_full": "sparse",
        "q12_wood_vs_stone": "wood",
        "q16_natural_vs_polished": "natural",
        "q09_textures": ["linen", "rough_wood"],
    }
    inferred = midpoint_inferred_style(answers)
    assert "top_styles" in inferred
    assert isinstance(inferred["top_styles"], list)
    assert "needs_more_questions" in inferred
    assert isinstance(inferred["needs_more_questions"], bool)
    assert "current_axes" in inferred


def test_midpoint_flags_convergence_when_top_two_close():
    """If top-2 styles are within 0.05 score, needs_more_questions = True."""
    # Empty answers → all style scores are 0.5 (neutral) → very close → needs more
    inferred = midpoint_inferred_style({})
    assert inferred["needs_more_questions"] is True
