"""Pure-Python discovery questionnaire engine.

Loads the question bank from docs/handbook/discovery_bank.yaml. Provides:

- list_questions(depth) — return the questions for a given depth
- validate_answer_payload(answers) — schema-check a dict of answers
- score_answers(answers) — compute taste profile (axes + style_match)
- new_session(depth) — create a session, return first batch
- midpoint_inferred_style(answers_so_far) — surface top-style hypothesis

No Blender / MCP dependencies — pure Python so unit tests run fast.

Style axis vector ground-truth lives below as STYLE_VECTORS. In Slice 1
only scandinavian.md exists as a full handbook chapter; the rest of the
v1 style library (per the workflow spec) gets a placeholder vector
here until each style chapter lands and exports its own frontmatter.
"""
from __future__ import annotations

import enum
import math
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class DiscoveryError(Exception):
    """Raised on invalid bank, invalid answer payload, or scoring errors."""


class Depth(str, enum.Enum):
    QUICK = "quick"        # 5–7 questions
    STANDARD = "standard"  # 12–15 questions
    DEEP = "deep"          # 25–30 questions
    ADAPTIVE = "adaptive"  # quick start, extends if convergence is poor


AXES = (
    "warmth",
    "complexity",
    "natural_vs_polished",
    "contrast",
    "aged_vs_new",
    "symmetric_vs_organic",
)


# Style ground-truth vectors. Each style is a 6-axis point in [-1, 1]^6.
# scandinavian is grounded in styles/scandinavian.md (Slice 1); others
# are placeholders pending Slice 5.
STYLE_VECTORS: Dict[str, Dict[str, float]] = {
    "scandinavian": {
        "warmth": 0.5,
        "complexity": -0.3,
        "natural_vs_polished": 0.5,
        "contrast": 0.0,
        "aged_vs_new": -0.1,
        "symmetric_vs_organic": -0.1,
    },
    "japanese_wabi_sabi": {
        "warmth": 0.3,
        "complexity": -0.5,
        "natural_vs_polished": 0.6,
        "contrast": -0.2,
        "aged_vs_new": 0.4,
        "symmetric_vs_organic": -0.3,
    },
    "modern_minimal": {
        "warmth": -0.1,
        "complexity": -0.5,
        "natural_vs_polished": -0.2,
        "contrast": 0.2,
        "aged_vs_new": -0.4,
        "symmetric_vs_organic": 0.3,
    },
    "speakeasy": {
        "warmth": 0.5,
        "complexity": 0.4,
        "natural_vs_polished": 0.0,
        "contrast": 0.5,
        "aged_vs_new": 0.4,
        "symmetric_vs_organic": 0.0,
    },
    "industrial_loft": {
        "warmth": 0.0,
        "complexity": 0.2,
        "natural_vs_polished": 0.3,
        "contrast": 0.4,
        "aged_vs_new": 0.5,
        "symmetric_vs_organic": -0.1,
    },
    "new_chinese": {
        "warmth": 0.3,
        "complexity": 0.2,
        "natural_vs_polished": 0.3,
        "contrast": 0.2,
        "aged_vs_new": 0.4,
        "symmetric_vs_organic": 0.4,
    },
    "french_cream": {
        "warmth": 0.3,
        "complexity": 0.4,
        "natural_vs_polished": -0.1,
        "contrast": 0.1,
        "aged_vs_new": 0.2,
        "symmetric_vs_organic": 0.3,
    },
    "muji_minimal": {
        "warmth": 0.2,
        "complexity": -0.5,
        "natural_vs_polished": 0.3,
        "contrast": -0.2,
        "aged_vs_new": -0.2,
        "symmetric_vs_organic": 0.1,
    },
    "industrial_cafe": {
        "warmth": 0.1,
        "complexity": 0.3,
        "natural_vs_polished": 0.2,
        "contrast": 0.4,
        "aged_vs_new": 0.5,
        "symmetric_vs_organic": -0.2,
    },
    "american_classic": {
        "warmth": 0.3,
        "complexity": 0.3,
        "natural_vs_polished": -0.1,
        "contrast": 0.2,
        "aged_vs_new": 0.3,
        "symmetric_vs_organic": 0.4,
    },
    "mediterranean": {
        "warmth": 0.5,
        "complexity": 0.1,
        "natural_vs_polished": 0.4,
        "contrast": 0.3,
        "aged_vs_new": 0.3,
        "symmetric_vs_organic": -0.1,
    },
    "quiet_luxury": {
        "warmth": 0.2,
        "complexity": -0.2,
        "natural_vs_polished": 0.0,
        "contrast": 0.0,
        "aged_vs_new": 0.1,
        "symmetric_vs_organic": 0.2,
    },
    "mid_century_modern": {
        "warmth": 0.3,
        "complexity": 0.1,
        "natural_vs_polished": 0.2,
        "contrast": 0.3,
        "aged_vs_new": 0.3,
        "symmetric_vs_organic": 0.1,
    },
    "chinese_tea_house": {
        "warmth": 0.4,
        "complexity": 0.3,
        "natural_vs_polished": 0.4,
        "contrast": 0.1,
        "aged_vs_new": 0.4,
        "symmetric_vs_organic": 0.4,
    },
    "insta_cafe": {
        "warmth": 0.0,
        "complexity": -0.4,
        "natural_vs_polished": -0.1,
        "contrast": 0.2,
        "aged_vs_new": -0.4,
        "symmetric_vs_organic": 0.3,
    },
    "japanese_tea_cafe": {
        "warmth": 0.3,
        "complexity": -0.3,
        "natural_vs_polished": 0.5,
        "contrast": -0.1,
        "aged_vs_new": 0.2,
        "symmetric_vs_organic": -0.1,
    },
    "boutique_retail": {
        "warmth": 0.0,
        "complexity": -0.3,
        "natural_vs_polished": -0.1,
        "contrast": 0.4,
        "aged_vs_new": -0.3,
        "symmetric_vs_organic": 0.2,
    },
    "modern_chinese_restaurant": {
        "warmth": 0.3,
        "complexity": 0.4,
        "natural_vs_polished": 0.2,
        "contrast": 0.4,
        "aged_vs_new": 0.3,
        "symmetric_vs_organic": 0.2,
    },
    "coworking_office": {
        "warmth": 0.1,
        "complexity": 0.2,
        "natural_vs_polished": 0.0,
        "contrast": 0.2,
        "aged_vs_new": -0.1,
        "symmetric_vs_organic": -0.1,
    },
}


_BANK_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "docs" / "handbook" / "discovery_bank.yaml"
)


_loaded_bank: Optional[List[Dict[str, Any]]] = None


def _load_bank() -> List[Dict[str, Any]]:
    """Load and cache the question bank YAML."""
    global _loaded_bank
    if _loaded_bank is not None:
        return _loaded_bank
    if not _BANK_PATH.exists():
        raise DiscoveryError(f"discovery_bank.yaml not found at {_BANK_PATH}")
    try:
        data = yaml.safe_load(_BANK_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise DiscoveryError(f"failed to parse discovery_bank.yaml: {e}") from e

    questions = [
        d for d in data
        if isinstance(d, dict) and isinstance(d.get("id"), str)
        and d["id"].startswith("q")
    ]
    if not questions:
        raise DiscoveryError("discovery_bank.yaml contains no questions")
    _loaded_bank = questions
    return questions


# Quick-mode: enough to score a basic taste profile.
_QUICK_IDS = {
    "q01_who_uses",
    "q02_project_type",
    "q06_first_second_feeling",
    "q08_movie",
    "q09_textures",
    "q10_warm_vs_cool",
    "q11_sparse_vs_full",
}

# Standard-mode: Quick + a couple more from each type.
_STANDARD_EXTRA = {
    "q03_total_area", "q04_budget", "q12_wood_vs_stone",
    "q14_aged_vs_new", "q16_natural_vs_polished", "q19_dont_want",
}


def list_questions(depth: Depth = Depth.DEEP) -> List[Dict[str, Any]]:
    """Return the question list for a given depth."""
    bank = _load_bank()
    if depth in (Depth.DEEP, Depth.ADAPTIVE):
        return list(bank)
    quick_ids = _QUICK_IDS
    standard_ids = quick_ids | _STANDARD_EXTRA
    if depth == Depth.QUICK:
        return [q for q in bank if q["id"] in quick_ids]
    if depth == Depth.STANDARD:
        return [q for q in bank if q["id"] in standard_ids]
    raise DiscoveryError(f"unknown depth: {depth}")


def _question_valid_choices(q: Dict[str, Any]) -> set:
    if "choices" in q:
        return {c["value"] for c in q["choices"]}
    if "options" in q:
        return {o["value"] for o in q["options"]}
    return set()


def validate_answer_payload(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Schema-check answers; return a normalized copy."""
    bank = _load_bank()
    by_id = {q["id"]: q for q in bank}
    out: Dict[str, Any] = {}
    for qid, value in answers.items():
        if qid not in by_id:
            raise DiscoveryError(f"unknown question id: {qid}")
        q = by_id[qid]
        if q.get("free_input_only"):
            if not isinstance(value, str):
                raise DiscoveryError(
                    f"{qid} is free_input_only — expected string"
                )
            out[qid] = value.strip()
            continue
        valid_choices = _question_valid_choices(q)
        if isinstance(value, str):
            if value in valid_choices:
                out[qid] = value
                continue
            if q.get("free_input"):
                out[qid] = {"free_text": value}
                continue
            raise DiscoveryError(
                f"{qid}: choice '{value}' not in {sorted(valid_choices)}"
            )
        if isinstance(value, list):
            for v in value:
                if v not in valid_choices and not q.get("free_input"):
                    raise DiscoveryError(
                        f"{qid}: choice '{v}' not in {sorted(valid_choices)}"
                    )
            out[qid] = list(value)
            continue
        out[qid] = value
    return out


def _zero_axes() -> Dict[str, float]:
    return {a: 0.0 for a in AXES}


def _question_axes_for_choice(
    q: Dict[str, Any], choice_value: str,
) -> Dict[str, float]:
    pool = q.get("choices") or q.get("options") or []
    for c in pool:
        if c["value"] == choice_value:
            return c.get("axes", {})
    return {}


def score_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Compute style axes + style match from answers."""
    bank = _load_bank()
    by_id = {q["id"]: q for q in bank}

    axes_sum = _zero_axes()
    axes_count = {a: 0 for a in AXES}

    feeling_anchors: List[str] = []
    material_pull: List[str] = []
    free_text_chunks: List[str] = []

    for qid, value in answers.items():
        if qid not in by_id:
            continue
        q = by_id[qid]
        if isinstance(value, dict) and "free_text" in value:
            free_text_chunks.append(f"{qid}: {value['free_text']}")
            continue
        if q.get("free_input_only"):
            if isinstance(value, str):
                free_text_chunks.append(f"{qid}: {value}")
            continue
        if q.get("type") == 2:
            if isinstance(value, list):
                feeling_anchors.extend(value)
            elif isinstance(value, str):
                feeling_anchors.append(value)
        if q.get("type") == 4:
            if isinstance(value, list):
                material_pull.extend(value)
            elif isinstance(value, str):
                material_pull.append(value)
        choices = value if isinstance(value, list) else [value]
        for choice in choices:
            if not isinstance(choice, str):
                continue
            chosen_axes = _question_axes_for_choice(q, choice)
            for axis, weight in chosen_axes.items():
                if axis in axes_sum:
                    axes_sum[axis] += weight
                    axes_count[axis] += 1

    style_axes = {}
    for axis in AXES:
        n = max(1, axes_count[axis])
        v = axes_sum[axis] / n
        style_axes[axis] = round(max(-1.0, min(1.0, v)), 4)

    style_match = _project_to_styles(style_axes)
    recommended = (
        max(style_match.items(), key=lambda kv: kv[1])[0]
        if style_match else None
    )

    return {
        "feeling_anchors": _dedup(feeling_anchors),
        "style_axes": style_axes,
        "material_pull": _dedup(material_pull),
        "style_match": style_match,
        "recommended_style": recommended,
        "free_text_notes": "\n".join(free_text_chunks),
    }


def _dedup(items: List[str]) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _project_to_styles(axes: Dict[str, float]) -> Dict[str, float]:
    """Cosine similarity between user axes and each style vector.

    Returns a dict mapping style_name -> score in [0, 1] where 1.0 is
    perfect alignment and 0.0 is opposite.
    """
    user_vec = [axes.get(a, 0.0) for a in AXES]
    user_norm = math.sqrt(sum(v * v for v in user_vec))
    out: Dict[str, float] = {}
    for style_name, vec in STYLE_VECTORS.items():
        sv = [vec.get(a, 0.0) for a in AXES]
        sv_norm = math.sqrt(sum(v * v for v in sv)) or 1.0
        if user_norm == 0.0:
            # Neutral user vector → all styles equally close (0.5)
            out[style_name] = 0.5
            continue
        dot = sum(u * v for u, v in zip(user_vec, sv))
        cos = dot / (user_norm * sv_norm)
        out[style_name] = round(0.5 * (cos + 1.0), 4)
    return out


def new_session(
    depth: Depth = Depth.DEEP, batch_size: int = 4,
) -> Dict[str, Any]:
    """Start a discovery session. Returns session_id + first batch."""
    questions = list_questions(depth)
    session_id = secrets.token_urlsafe(8)
    return {
        "session_id": session_id,
        "depth": depth.value,
        "total_questions": len(questions),
        "batch": questions[:batch_size],
        "next_index": min(batch_size, len(questions)),
    }


def midpoint_inferred_style(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Run scoring on partial answers and surface top-2/3 style hypothesis."""
    profile = score_answers(answers)
    sm = profile.get("style_match", {})
    top = sorted(sm.items(), key=lambda kv: kv[1], reverse=True)[:3]
    needs_more = (
        len(top) < 2
        or (len(top) >= 2 and (top[0][1] - top[1][1]) < 0.05)
    )
    return {
        "top_styles": [{"name": n, "score": s} for n, s in top],
        "needs_more_questions": needs_more,
        "current_axes": profile.get("style_axes", {}),
    }
