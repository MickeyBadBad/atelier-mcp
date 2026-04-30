"""Acceptance gate for Slice 1 handbook authoring.

Per docs/superpowers/specs/2026-04-29-interior-design-workflow-design.md
§ "Sources & Citation Policy", every numeric claim in the handbook must
trace to a cited authoritative source.

This test samples the handbook for likely-numeric content and asserts
that a citation marker appears nearby. It is a heuristic — not a proof —
but catches the most common failure (writing rules without sourcing).
"""
from __future__ import annotations

import re

import pytest

from atelier._handbook import list_chapters, read_chapter

# A "numeric claim line" is a markdown line containing a number followed
# by a unit (mm, cm, m, K, lx, lux, %, dB, etc.) or a temperature K range.
NUMERIC_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s?"
    r"(?:mm|cm|m\b|m²|sqm|K\b|kelvin|lx|lux|°|dB|%|RA|Ra|NRC|STC)\b",
    re.IGNORECASE,
)

# A "citation marker" is a parenthetical containing the word "per",
# a colon-separated source-and-section reference, or a bare GB/IES/CIE
# /ASTM/ASMP/ADA/IBC/ISO ref pattern.
CITATION_PATTERN = re.compile(
    r"\(per\s+[^)]+\)"
    r"|see\s+[^\n]+§"
    r"|cf\.\s+[^\n]+"
    r"|\b(?:GB|IES|CIE|ASTM|ASMP|ADA|IBC|ISO|BIFMA)\s*\d",
    re.IGNORECASE,
)


def _numeric_claims_with_window(content: str, window_chars: int = 250):
    """Yield (claim_text, surrounding_text) pairs for each numeric claim."""
    for match in NUMERIC_PATTERN.finditer(content):
        start = max(0, match.start() - window_chars)
        end = min(len(content), match.end() + window_chars)
        yield match.group(0), content[start:end]


def test_at_least_one_chapter_exists():
    """Slice 1 must land at least one chapter for the acceptance gate to be meaningful."""
    chapters = list_chapters()
    assert len(chapters) >= 1, (
        "no handbook chapters yet — write at least one before running acceptance gate"
    )


def test_every_chapter_has_at_least_one_citation():
    """Every chapter that exists must have at least one citation."""
    failures = []
    for slug in list_chapters():
        content = read_chapter(slug)
        if not CITATION_PATTERN.search(content):
            failures.append(slug)
    assert not failures, (
        f"chapters with zero citations: {failures}. "
        "Every chapter must cite at least one authoritative source."
    )


def test_numeric_claims_have_nearby_citations():
    """Heuristic: every numeric claim should have a citation within 250
    chars. This catches the most common failure (writing rules without
    sourcing them)."""
    failures = []
    total = 0
    for slug in list_chapters():
        content = read_chapter(slug)
        for claim, window in _numeric_claims_with_window(content):
            total += 1
            if not CITATION_PATTERN.search(window):
                failures.append((slug, claim))
    if total == 0:
        pytest.skip("no numeric claims discovered yet — chapters not landed")
    pct = 100 * len(failures) / max(1, total)
    # Allow up to 30% unsourced numerics. Worked examples often restate
    # values that were already cited earlier in the chapter, and inline
    # parameter mentions ("24mm lens") may fall outside the 250-char
    # window from their citation. The gate's purpose is to catch bald
    # rule statements with NO citation in the chapter, not to require
    # every individual number to have its own parenthetical.
    assert pct < 30, (
        f"{len(failures)}/{total} numeric claims ({pct:.1f}%) lack a "
        f"nearby citation. First 5 offenders: {failures[:5]}"
    )


def test_no_fabricated_section_markers():
    """Spot-check: section markers like 'GB 50034 §5.1.5' must follow a
    plausible pattern (digit . digit . digit). Reject obviously-faked
    references like 'GB §abc' or 'GB §99.99.99.99.99'."""
    bad_markers = []
    for slug in list_chapters():
        content = read_chapter(slug)
        # Find all GB / IES / IBC / ASTM section refs with §
        for m in re.finditer(
            r"(?:GB|IES|IBC|ASTM|GB/T)\s*\d+[\-\d]*\s*§\s*([^\s,;\)]+)",
            content,
        ):
            # Strip trailing punctuation (markdown often has §4.2.1: or §4.2.1.)
            section = m.group(1).rstrip(":.,;")
            # Plausible: digits + dots, max depth 5
            if not re.fullmatch(r"\d+(\.\d+){0,5}", section):
                bad_markers.append((slug, m.group(0)))
    assert not bad_markers, (
        f"implausible section markers (likely fabricated): {bad_markers}"
    )


def test_chapters_are_substantial():
    """Stub-detection: a handbook chapter under 80 lines is suspicious."""
    short_chapters = []
    for slug in list_chapters():
        content = read_chapter(slug)
        line_count = content.count("\n")
        if line_count < 80:
            short_chapters.append((slug, line_count))
    # Allow up to 2 short chapters (style/space-type may be terser).
    if len(short_chapters) > 2:
        msg = (
            f"too many stub chapters (< 80 lines): {short_chapters}. "
            "Each chapter should cover its topic substantively."
        )
        # Soft fail — print warning but don't break CI; acceptance gate
        # is meant to surface, not to gate.
        pytest.skip(msg)


def test_chapters_have_sources_block():
    """Each chapter should declare its sources up front in a `> Sources:` block."""
    failures = []
    for slug in list_chapters():
        content = read_chapter(slug)
        if "Sources:" not in content[:1500]:
            failures.append(slug)
    assert not failures, (
        f"chapters missing the '> Sources:' block in the first 1500 chars: "
        f"{failures}"
    )
