"""Style chapter parser.

Reads `docs/handbook/styles/<slug>.md` (via _handbook.read_chapter) and
extracts a structured `StyleVocab` object that downstream tools
(moodboard, place_furniture_from_style, etc.) consume without
re-parsing the markdown each call.

All chapters follow a known structure (see docs/handbook/README.md
"Chapter Template" + the canonical scandinavian.md example) so
section-walking + targeted regex is sufficient. Where a style chapter
is non-conforming (rare), the parser falls back gracefully and returns
empty fields rather than raising.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

from ._handbook import HandbookError, list_chapters, read_chapter


class StyleVocabError(Exception):
    """Raised when a style chapter cannot be parsed."""


@dataclass
class StyleVocab:
    slug: str
    anchor_description: str = ""
    palette_60_30_10: List[dict] = field(default_factory=list)
    materials_in: List[str] = field(default_factory=list)
    materials_out: List[str] = field(default_factory=list)
    kelvin_range: Tuple[int, int] = (2700, 3000)
    fixture_keywords: List[str] = field(default_factory=list)
    prop_keywords: List[str] = field(default_factory=list)
    reference_projects: List[dict] = field(default_factory=list)


_STYLE_PREFIX = "styles/"


def available_styles() -> List[str]:
    """Return the list of style slugs (without 'styles/' prefix)."""
    out: List[str] = []
    for chapter in list_chapters():
        if chapter.startswith(_STYLE_PREFIX):
            out.append(chapter[len(_STYLE_PREFIX):])
    return sorted(out)


# ----- Section extraction helpers -----

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _split_into_sections(content: str):
    """Yield (level, title, body) tuples, where body is text up to the
    next heading at the same or higher level (so a `## Foo` section
    includes all of its `### Bar` subsections in its body)."""
    matches = list(_HEADING_PATTERN.finditer(content))
    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = len(content)
        for j in range(i + 1, len(matches)):
            if len(matches[j].group(1)) <= level:
                end = matches[j].start()
                break
        body = content[start:end]
        yield level, title, body


def _find_section(content: str, title_substring: str) -> str:
    """Find a section by case-insensitive title substring; return its body or empty."""
    title_substring = title_substring.lower()
    for _, title, body in _split_into_sections(content):
        if title_substring in title.lower():
            return body
    return ""


def _find_subsections(parent_body: str):
    """Yield (title, body) for each ### subsection inside a parent."""
    matches = list(_HEADING_PATTERN.finditer(parent_body))
    for i, match in enumerate(matches):
        if len(match.group(1)) != 3:  # only ### depth
            continue
        title = match.group(2).strip()
        start = match.end()
        # Find next heading at same or higher level
        end = len(parent_body)
        for j in range(i + 1, len(matches)):
            if len(matches[j].group(1)) <= 3:
                end = matches[j].start()
                break
        yield title, parent_body[start:end]


# ----- Targeted extractors -----

_HEX_RE = re.compile(r"`?(#[0-9A-Fa-f]{6})`?")


def _extract_hex_codes(text: str) -> List[str]:
    """Find hex color codes in text. Dedupe preserving order."""
    seen = set()
    out: List[str] = []
    for match in _HEX_RE.finditer(text):
        h = match.group(1).upper()
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def _parse_palette_table(body: str) -> List[dict]:
    """Parse the palette table rows. Each row → {role, hex: [...], notes}."""
    rows: List[dict] = []
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "---" in line or line.strip().startswith("| Role"):
            continue
        parts = [c.strip() for c in line.split("|")[1:-1]]
        if len(parts) < 2:
            continue
        role = parts[0]
        hex_field = parts[1] if len(parts) > 1 else ""
        notes = parts[2] if len(parts) > 2 else ""
        hex_codes = _extract_hex_codes(hex_field)
        if not hex_codes:
            continue
        rows.append({
            "role": role,
            "hex": hex_codes,
            "notes": notes,
        })
    return rows


_KELVIN_RANGE_RE = re.compile(
    r"(\d{4})\s*[–\-—~]\s*(\d{4})\s*K",
    re.IGNORECASE,
)
_KELVIN_SINGLE_RE = re.compile(r"(\d{4})\s*K\b", re.IGNORECASE)


def _parse_kelvin_range(body: str) -> Tuple[int, int]:
    """Find the first Kelvin range in the lighting section, falling back
    to min/max of all detected Kelvin values."""
    range_match = _KELVIN_RANGE_RE.search(body)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))
    singles = [int(m.group(1)) for m in _KELVIN_SINGLE_RE.finditer(body)]
    plausible = [k for k in singles if 1500 <= k <= 7500]
    if plausible:
        return min(plausible), max(plausible)
    return (2700, 3000)  # safe residential default


def _parse_bullet_list(body: str) -> List[str]:
    """Pull bullet items from a markdown bulleted block. Strips inline citations."""
    items: List[str] = []
    for line in body.splitlines():
        line = line.strip()
        if not (line.startswith("- ") or line.startswith("* ")):
            continue
        text = line[2:].strip()
        # Strip parenthetical citations
        text = re.sub(r"\(per\s[^)]+\)", "", text).strip()
        # Strip trailing markdown emphasis markers
        text = text.rstrip(".")
        if text:
            items.append(text)
    return items


def _parse_reference_projects(body: str) -> List[dict]:
    """Parse the reference projects numbered/bulleted list."""
    projects: List[dict] = []
    pattern = re.compile(
        r"^\s*\d+\.\s+(.+)$|^\s*[-*]\s+(.+)$",
        re.MULTILINE,
    )
    for match in pattern.finditer(body):
        line = match.group(1) or match.group(2)
        if not line:
            continue
        # Try to split into "Designer/Firm, Project, Year — Publication"
        projects.append({"raw": line.strip()})
    return projects


# ----- Main parser -----


def parse_style_chapter(slug: str) -> StyleVocab:
    """Load `docs/handbook/styles/<slug>.md` and return a StyleVocab.

    Raises StyleVocabError if the chapter is missing or unparseable.
    """
    slug = slug.strip()
    if slug.startswith(_STYLE_PREFIX):
        slug = slug[len(_STYLE_PREFIX):]
    full_chapter = f"{_STYLE_PREFIX}{slug}"

    try:
        content = read_chapter(full_chapter)
    except HandbookError as e:
        raise StyleVocabError(
            f"style chapter '{slug}' not found. available: "
            f"{', '.join(available_styles())}"
        ) from e

    vocab = StyleVocab(slug=slug)

    # Anchor description
    anchor = _find_section(content, "anchor description")
    if anchor:
        # Take the first non-empty paragraph, stripping inline citations
        first_para = anchor.strip().split("\n\n", 1)[0]
        vocab.anchor_description = re.sub(
            r"\(per\s[^)]+\)", "", first_para,
        ).strip()

    # Palette
    palette_body = _find_section(content, "color palette")
    if palette_body:
        vocab.palette_60_30_10 = _parse_palette_table(palette_body)

    # Materials In / Out
    materials_body = _find_section(content, "material vocabulary")
    for sub_title, sub_body in _find_subsections(materials_body):
        items = _parse_bullet_list(sub_body)
        if "in" in sub_title.lower():
            vocab.materials_in = items
        elif "out" in sub_title.lower():
            vocab.materials_out = items

    # Kelvin range
    lighting_body = _find_section(content, "lighting profile")
    if lighting_body:
        vocab.kelvin_range = _parse_kelvin_range(lighting_body)

    # Prop vocabulary → keywords
    prop_body = _find_section(content, "prop vocabulary")
    if prop_body:
        vocab.prop_keywords = _parse_bullet_list(prop_body)

    # Fixture keywords (subset — derive from material vocabulary in + lighting)
    # We use a heuristic: anything in materials_in that mentions "lamp",
    # "pendant", "sconce", "fixture", "lantern" is a fixture keyword.
    fixture_terms = (
        "lamp", "pendant", "sconce", "fixture", "lantern", "chandelier",
        "downlight", "track", "spot",
    )
    for item in vocab.materials_in:
        lower = item.lower()
        if any(t in lower for t in fixture_terms):
            vocab.fixture_keywords.append(item)
    # Add any prop_keywords mentioning fixtures
    for item in vocab.prop_keywords:
        lower = item.lower()
        if any(t in lower for t in fixture_terms):
            vocab.fixture_keywords.append(item)

    # Reference projects
    ref_body = _find_section(content, "reference projects")
    if ref_body:
        vocab.reference_projects = _parse_reference_projects(ref_body)

    return vocab
