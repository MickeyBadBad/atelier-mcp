"""Moodboard prompt builder.

Given a project's `taste-profile.json` and a parsed `StyleVocab`, build
N distinct image-gen prompts that the AI can feed into existing
`generate_image_codex` / `generate_image_openai` MCP tools to produce
moodboard candidates.

Pure Python; no image generation here. The caller picks an image-gen
backend, runs the prompts, presents the candidates to the user, and
calls `lock_moodboard` once the user picks one.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ._style_vocab import StyleVocab


class MoodboardError(Exception):
    """Raised on prompt-building or filesystem failures."""


_MAX_CANDIDATES = 8

# Variation axes — combine to produce N distinct prompts
_FRAMING_VARIANTS = [
    "3-quarter angle from the entry, eye-level",
    "corner shot showing two walls + ceiling + floor diagonal",
    "looking toward the focal feature wall",
    "wide angle showing main seating cluster",
    "morning daylight wide-angle",
    "evening warm-light hero shot",
    "low-angle showing ceiling + key fixtures",
    "detail mid-zoom on styling vignette",
]

_MOOD_VARIANTS = [
    "soft natural daylight diffused through sheer curtains",
    "warm evening light with practical lamps glowing",
    "cool overcast morning light, contemplative mood",
    "golden-hour light raking across a textured wall",
    "low key lighting, intimate atmosphere",
    "balanced ambient + accent layered lighting",
    "single dramatic key light + soft fill",
    "all practicals on, no daylight",
]


def moodboard_dir(project_root: Path, style_slug: str) -> Path:
    """Canonical path for moodboard images of a project + style."""
    return Path(project_root) / "moodboards" / style_slug


def _format_palette_for_prompt(vocab: StyleVocab) -> str:
    """Render the palette as 'role (hex)' substring chunks for the prompt."""
    parts: List[str] = []
    for entry in vocab.palette_60_30_10[:4]:  # cap at 4 for prompt length
        role = entry.get("role", "").split("—")[-1].strip()
        hexes = ", ".join(entry.get("hex", []))
        if hexes and role:
            parts.append(f"{role} ({hexes})")
        elif hexes:
            parts.append(hexes)
    return "; ".join(parts) if parts else "neutral palette"


def _format_materials_for_prompt(vocab: StyleVocab) -> str:
    """Render up to 4 materials_in entries as a comma-joined snippet."""
    items: List[str] = []
    for raw in vocab.materials_in[:4]:
        # Strip markdown bold and trim to first sentence
        cleaned = raw.replace("**", "")
        # First period or 100 chars, whichever first
        end = min(
            (cleaned.find(".") if cleaned.find(".") > 0 else len(cleaned)),
            100,
        )
        snippet = cleaned[:end].strip()
        if snippet:
            items.append(snippet)
    return "; ".join(items) if items else "natural materials"


def _format_kelvin(vocab: StyleVocab) -> str:
    lo, hi = vocab.kelvin_range
    if lo == hi:
        return f"{lo}K"
    return f"{lo}-{hi}K"


def _space_type_phrase(space_type: str) -> str:
    """Humanize space-type slug for the prompt."""
    return space_type.replace("_", " ").replace("-", " ").strip()


def build_moodboard_prompts(
    taste_profile: Dict[str, Any],
    style_vocab: StyleVocab,
    n: int = 4,
    space_type: str = "living_room",
) -> List[str]:
    """Build N distinct moodboard image-gen prompts.

    Each prompt cites palette hex values, materials, Kelvin temperature
    range, the space-type, and the style slug — so the AI's downstream
    image generation is grounded in the handbook chapter rather than
    generic style memory.
    """
    if not isinstance(taste_profile, dict):
        raise MoodboardError("taste_profile must be a dict")
    n = max(1, min(int(n), _MAX_CANDIDATES))

    palette_str = _format_palette_for_prompt(style_vocab)
    materials_str = _format_materials_for_prompt(style_vocab)
    kelvin_str = _format_kelvin(style_vocab)
    space_phrase = _space_type_phrase(space_type)
    style_slug = style_vocab.slug

    feeling_anchors = ", ".join(taste_profile.get("feeling_anchors", [])[:3])
    feeling_clause = (
        f", evoking '{feeling_anchors}'" if feeling_anchors else ""
    )

    prompts: List[str] = []
    for i in range(n):
        framing = _FRAMING_VARIANTS[i % len(_FRAMING_VARIANTS)]
        mood = _MOOD_VARIANTS[(i + 1) % len(_MOOD_VARIANTS)]
        prompt = (
            f"Photorealistic interior render of a {space_phrase} in "
            f"{style_slug.replace('-', ' ')} style{feeling_clause}. "
            f"Palette: {palette_str}. "
            f"Materials: {materials_str}. "
            f"Lighting: {kelvin_str} layered ambient + accent, {mood}. "
            f"Camera: {framing}, 24-28mm focal length, AgX color "
            f"management, architectural photography style. "
            f"Per docs/handbook/styles/{style_slug}.md."
        )
        prompts.append(prompt)
    return prompts
