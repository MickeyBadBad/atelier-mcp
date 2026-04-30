# Interior Design Workflow — Slice 1: Knowledge Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the Knowledge Layer of the Interior Design Workflow — a sourced/cited markdown handbook (13 chapters), one example style + one example space-type, an MCP tool to read handbook content at runtime, and 5 Claude skills that auto-load relevant chapters.

**Architecture:** The handbook lives as plain markdown under `docs/handbook/` so users can edit it. Every numeric value or rule is fetched from authoritative sources (GB / IES / Neufert / Substance / Disney BSDF / named publications) and cited inline. The `read_design_handbook` MCP tool exposes chapter content (with citations) at runtime. Five Claude skills under `.claude/skills/interior-*` declare trigger phrases and instruct the AI to load relevant handbook chapters before acting.

**Tech Stack:** Python 3.10+, FastMCP, pytest, plain markdown for content. WebFetch / WebSearch for source retrieval. No Blender API changes in this slice.

---

## File Structure

| File | Responsibility |
|---|---|
| `docs/handbook/README.md` | Handbook index, citation policy reminder, format conventions |
| `docs/handbook/codes.md` | China GB safety/accessibility/fire codes summary |
| `docs/handbook/lighting.md` | Lighting design (Kelvin / Lux / layering) |
| `docs/handbook/spatial.md` | Clearances, circulation, ergonomics |
| `docs/handbook/materials.md` | PBR, color theory, finish adjacency |
| `docs/handbook/camera.md` | Architectural photography conventions |
| `docs/handbook/styling.md` | Composition + vignette construction |
| `docs/handbook/render-output.md` | View transforms, hero shot conventions |
| `docs/handbook/discovery.md` | Discovery questionnaire mechanics |
| `docs/handbook/project-types.md` | Multi-space project organization |
| `docs/handbook/furniture.md` | Furniture types + standard dimensions |
| `docs/handbook/acoustics.md` | Absorption, NRC, sound isolation |
| `docs/handbook/styles/scandinavian.md` | Example style (proof of citation pattern) |
| `docs/handbook/space-types/living-room.md` | Example space type (proof of pattern) |
| `src/blender_mcp/_handbook.py` | Pure Python module: load + query handbook |
| `src/blender_mcp/server.py` | Add `read_design_handbook` MCP tool |
| `tests/test_handbook.py` | Tests for `_handbook.py` |
| `tests/test_handbook_acceptance.py` | Acceptance gate: 10 random claims trace to sources |
| `.claude/skills/interior-discovery-intake.md` | Skill: project start triggers questionnaire |
| `.claude/skills/interior-style-locking.md` | Skill: moodboard/style anchoring |
| `.claude/skills/interior-plain-language-edit.md` | Skill: parse "move/swap/change" → MCP |
| `.claude/skills/interior-render-direction.md` | Skill: render planning + audit gate citation |
| `.claude/skills/interior-construction-handoff.md` | Skill: final docs + BoM |

---

## Task 1: Handbook Scaffolding

**Files:**
- Create: `docs/handbook/README.md`

- [ ] **Step 1: Create handbook directory and README**

```bash
mkdir -p docs/handbook/styles docs/handbook/space-types
```

Create `docs/handbook/README.md`:

```markdown
# Interior Design Handbook

This handbook is the source of truth for design knowledge consumed by the Interior Design Workflow MCP. Every numeric value, range, rule, or code reference herein is fetched from authoritative public sources and cited inline. **Do not write content from training memory; do not invent section numbers.** See `docs/dev/specs/2026-04-29-interior-design-workflow-design.md` § "Sources & Citation Policy".

## Chapter index

- `codes.md` — Building codes (China GB, accessibility, fire egress)
- `lighting.md` — Layered lighting (Kelvin, Lux, fixture spacing)
- `spatial.md` — Clearances, circulation, ergonomics
- `materials.md` — PBR, color theory, finish adjacency
- `camera.md` — Architectural photography conventions
- `styling.md` — Composition, vignettes, prop curation
- `render-output.md` — View transforms, render conventions
- `discovery.md` — Discovery questionnaire mechanics
- `project-types.md` — Multi-space organization
- `furniture.md` — Furniture types + dimensions
- `acoustics.md` — Absorption, NRC, isolation
- `styles/<name>.md` — Style-specific cues (one per style)
- `space-types/<name>.md` — Space-specific cues (one per space type)

## Citation format

Every numeric claim or rule cites its source inline:

```
Living-room sofa-to-coffee-table clearance: 400-460mm
(per Neufert Architects' Data, 5th ed., §"Living Rooms";
 Panero & Zelnik 1979 fig. 130 corroborates).
```

If no authoritative source can be found, the claim must say so:

```
Convention varies across sources; defaulting to range Z based on
majority practice in [list].
```

## Adding a chapter

1. Identify authoritative sources (GB / IES / Neufert / Substance / Disney / named publication).
2. Fetch via WebFetch and extract relevant rules.
3. Write the chapter using the **Chapter Template** below.
4. Verify every number has a citation.
5. Update this index.

## Chapter Template

```markdown
# <Chapter Title>

> Sources: <list of primary sources used>
> Last updated: YYYY-MM-DD

## Purpose

Brief statement of what this chapter covers and what downstream consumers do with it.

## Rules

### <Rule Group 1>

- Rule statement (numeric value) (inline citation)
- ...

## Worked examples

Optional: 1-2 worked examples showing how to apply the rules.

## See also

- Cross-references to other chapters.
```
```

- [ ] **Step 2: Commit**

```bash
git add docs/handbook/README.md
git commit -m "docs: handbook scaffolding (citation policy + chapter template)"
```

---

## Task 2: `_handbook.py` Pure Module — Failing Tests

**Files:**
- Create: `tests/test_handbook.py`

- [ ] **Step 1: Write failing tests for the handbook loader**

Create `tests/test_handbook.py`:

```python
"""Tests for the handbook loader module.

Coverage:
- list_chapters() returns the available chapter slugs
- read_chapter(slug) returns markdown content
- read_chapter() rejects path traversal attempts
- search_chapters(query) returns chapters that mention the query
- read_chapter() raises a clear error for unknown slugs
"""
from __future__ import annotations

import pytest

from blender_mcp._handbook import (
    HandbookError,
    list_chapters,
    read_chapter,
    search_chapters,
)


def test_list_chapters_includes_known_chapters():
    chapters = list_chapters()
    expected = {"codes", "lighting", "spatial", "materials", "camera",
                "styling", "render-output", "discovery", "project-types",
                "furniture", "acoustics"}
    missing = expected - set(chapters)
    assert not missing, f"missing chapters: {missing}"


def test_list_chapters_includes_styles_and_space_types():
    chapters = list_chapters()
    style_chapters = [c for c in chapters if c.startswith("styles/")]
    space_chapters = [c for c in chapters if c.startswith("space-types/")]
    assert len(style_chapters) >= 1, "at least one style chapter expected"
    assert len(space_chapters) >= 1, "at least one space-type chapter expected"


def test_read_chapter_returns_markdown():
    content = read_chapter("codes")
    assert isinstance(content, str)
    assert content.startswith("#"), "chapter should start with markdown header"
    assert len(content) > 100, "chapter should not be a stub"


def test_read_chapter_rejects_path_traversal():
    with pytest.raises(HandbookError):
        read_chapter("../../../etc/passwd")
    with pytest.raises(HandbookError):
        read_chapter("codes/../../../etc/passwd")


def test_read_chapter_unknown_slug_raises():
    with pytest.raises(HandbookError) as exc_info:
        read_chapter("not-a-real-chapter")
    assert "not-a-real-chapter" in str(exc_info.value)
    assert "available" in str(exc_info.value).lower()


def test_search_chapters_returns_matches():
    # "Kelvin" should match lighting.md
    results = search_chapters("Kelvin")
    assert isinstance(results, list)
    assert any("lighting" in r["chapter"] for r in results), \
        "Kelvin search should find lighting chapter"


def test_search_chapters_empty_query_returns_empty():
    assert search_chapters("") == []
    assert search_chapters("   ") == []
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp
.venv/bin/pytest tests/test_handbook.py -v
```

Expected: ImportError because `_handbook.py` doesn't exist yet.

---

## Task 3: `_handbook.py` Pure Module — Implementation

**Files:**
- Create: `src/blender_mcp/_handbook.py`

- [ ] **Step 1: Write the loader module**

Create `src/blender_mcp/_handbook.py`:

```python
"""Pure-Python handbook loader.

The handbook lives at <repo-root>/docs/handbook/ as plain markdown.
This module exposes:

- list_chapters() -> list of chapter slugs (e.g. "codes", "styles/scandinavian")
- read_chapter(slug) -> raw markdown content
- search_chapters(query) -> chapters whose body contains the query

No Blender or MCP dependencies — pure Python so unit tests run fast.
Path-traversal-safe: chapter slugs are validated against the discovered
chapter list before any filesystem access.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any


class HandbookError(Exception):
    """Raised on chapter-not-found, traversal, or read errors."""


_HANDBOOK_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "handbook"


def _handbook_root() -> Path:
    """Return the absolute handbook directory, raising if missing."""
    if not _HANDBOOK_DIR.is_dir():
        raise HandbookError(
            f"Handbook directory not found at {_HANDBOOK_DIR}. "
            "Run from repo root and ensure docs/handbook/ exists."
        )
    return _HANDBOOK_DIR


def list_chapters() -> List[str]:
    """Return the list of available chapter slugs.

    A slug is the path under docs/handbook/ without the .md suffix.
    Examples: "codes", "lighting", "styles/scandinavian".
    The README.md is excluded (it's the index, not a chapter).
    """
    root = _handbook_root()
    slugs: List[str] = []
    for md in root.rglob("*.md"):
        rel = md.relative_to(root)
        if rel.name.lower() == "readme.md":
            continue
        slug = str(rel.with_suffix(""))
        # POSIX-style slug for cross-platform consistency
        slug = slug.replace("\\", "/")
        slugs.append(slug)
    return sorted(slugs)


def _resolve_chapter_path(slug: str) -> Path:
    """Resolve slug → file path, rejecting traversal."""
    slug = (slug or "").strip()
    if not slug:
        raise HandbookError("chapter slug must not be empty")

    available = list_chapters()
    if slug not in available:
        raise HandbookError(
            f"chapter '{slug}' not found. available chapters: "
            f"{', '.join(available)}"
        )

    root = _handbook_root()
    candidate = (root / f"{slug}.md").resolve()
    # Defensive: ensure the resolved path is still inside the handbook root.
    if root.resolve() not in candidate.parents and candidate != root.resolve():
        raise HandbookError(f"chapter slug '{slug}' resolves outside handbook root")
    return candidate


def read_chapter(slug: str) -> str:
    """Return the markdown content of a chapter."""
    path = _resolve_chapter_path(slug)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        raise HandbookError(f"failed to read chapter '{slug}': {e}") from e


def search_chapters(query: str) -> List[Dict[str, Any]]:
    """Return chapters whose body contains the query (case-insensitive).

    Returns a list of dicts: {"chapter": slug, "matches": int, "preview": str}
    sorted by match count descending. Empty/whitespace query returns [].
    """
    query = (query or "").strip()
    if not query:
        return []

    needle = query.lower()
    results: List[Dict[str, Any]] = []
    for slug in list_chapters():
        try:
            body = read_chapter(slug).lower()
        except HandbookError:
            continue
        count = body.count(needle)
        if count == 0:
            continue
        # Find a small preview around the first match
        idx = body.find(needle)
        start = max(0, idx - 60)
        end = min(len(body), idx + 60 + len(needle))
        preview = body[start:end].replace("\n", " ").strip()
        results.append({
            "chapter": slug,
            "matches": count,
            "preview": preview,
        })

    results.sort(key=lambda r: r["matches"], reverse=True)
    return results
```

- [ ] **Step 2: Run tests — verify they pass**

```bash
.venv/bin/pytest tests/test_handbook.py -v
```

Expected: All tests pass except those that depend on chapters existing
(read_chapter, search_chapters with content). They will pass once Tasks
4-13 land. For now, the test asserting `list_chapters()` returns at
least the expected slugs will fail — that is acceptable until chapters
land. Mark TODO inline if needed.

- [ ] **Step 3: Commit**

```bash
git add src/blender_mcp/_handbook.py tests/test_handbook.py
git commit -m "feat: handbook loader module + tests

Pure-Python module with list_chapters/read_chapter/search_chapters.
Path-traversal-safe. Tests for chapter listing, content reading,
search, and error cases.
"
```

---

## Task 4: `read_design_handbook` MCP Tool

**Files:**
- Modify: `src/blender_mcp/server.py` (add tool near `asset_query_help`)

- [ ] **Step 1: Add the MCP tool**

In `src/blender_mcp/server.py`, find the `asset_query_help` tool definition (near line 1861). Add this tool right after it:

```python
@mcp.tool()
@telemetry_tool("read_design_handbook")
@tool_envelope
def read_design_handbook(
    ctx: Context,
    chapter: str = "",
    query: str = "",
) -> str:
    """
    Read the Interior Design Handbook — the source-of-truth for design rules,
    standards, codes, and style guidance used by the Interior Design Workflow.

    The handbook lives as markdown in docs/handbook/. Every numeric value
    inside is sourced and cited (per the Sources & Citation Policy in
    docs/dev/specs/2026-04-29-interior-design-workflow-design.md).

    Three call modes:

    1. List all chapters: `read_design_handbook()`
    2. Read a specific chapter: `read_design_handbook(chapter="lighting")`
    3. Search across chapters: `read_design_handbook(query="Kelvin")`

    Parameters:
    - chapter: chapter slug ("lighting", "styles/scandinavian", etc.). Empty
               string means list mode.
    - query: free-text query, searched case-insensitive across all chapters.
             If both `chapter` and `query` are given, `chapter` wins.

    Returns the chapter content (markdown) or a list of available chapters
    or search results, all wrapped in the canonical envelope.
    """
    from ._handbook import (
        HandbookError, list_chapters, read_chapter, search_chapters,
    )

    if chapter:
        try:
            content = read_chapter(chapter)
        except HandbookError as e:
            raise ToolError(
                code=ErrorCode.NOT_FOUND,
                hint="Use read_design_handbook() with no args to list chapters.",
                detail=str(e),
            ) from e
        return _tool_response({
            "chapter": chapter,
            "content": content,
        })

    if query:
        try:
            results = search_chapters(query)
        except HandbookError as e:
            raise ToolError(
                code=ErrorCode.INTERNAL,
                hint="Handbook may be missing or corrupted.",
                detail=str(e),
            ) from e
        return _tool_response({
            "query": query,
            "results": results,
        })

    # No args → list mode
    try:
        chapters = list_chapters()
    except HandbookError as e:
        raise ToolError(
            code=ErrorCode.STATE_REQUIRED,
            hint="Run from a repo with docs/handbook/ present.",
            detail=str(e),
        ) from e
    return _tool_response({
        "available_chapters": chapters,
        "tip": (
            "Pass chapter='<slug>' to read one, or query='<keyword>' to "
            "search across all chapters."
        ),
    })
```

- [ ] **Step 2: Verify the tool registers without import errors**

```bash
.venv/bin/python -c "from blender_mcp import server; print('ok')"
```

Expected: prints `ok`. If ImportError on `_handbook`, check Task 3 was committed.

- [ ] **Step 3: Add a smoke test**

Append to `tests/test_handbook.py`:

```python
def test_read_design_handbook_tool_registered():
    """The MCP tool should exist on the server module."""
    from blender_mcp import server
    assert hasattr(server, "read_design_handbook")
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest tests/test_handbook.py -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/blender_mcp/server.py tests/test_handbook.py
git commit -m "feat: read_design_handbook MCP tool

Three call modes: list (no args), read (chapter=), search (query=).
Returns canonical envelope with available_chapters / content / results.
NOT_FOUND on bad slug, STATE_REQUIRED if handbook dir missing."
```

---

## Tasks 5-15: Handbook Chapters

Each handbook chapter follows the same pattern:

**Phase A — Source fetch (mandatory before writing):**
1. Identify primary sources (listed per task below).
2. WebFetch each source URL. If a URL is paywalled or behind 403, fall back to one of:
   - Wikipedia article on the standard (often summarizes section numbers + values)
   - Government statute aggregator (e.g. openlaw.cn for GB, codes.iccsafe.org for IBC)
   - Reference book summary (search "<standard> table of contents")
3. Extract the specific numeric values and rules with source attribution intact.

**Phase B — Write chapter following the template in `docs/handbook/README.md`:**
1. `# Title` heading.
2. `> Sources:` block listing primary sources used + last-updated date.
3. `## Purpose` (2-3 sentences).
4. `## Rules` with sub-sections — every numeric value followed by `(per <source>)`.
5. `## Worked examples` — 1-2 application examples.
6. `## See also` — cross-references.

**Phase C — Verify:**
1. Every numeric value has an inline citation.
2. No fabricated section numbers — only cite section/page/table references that the source actually has.

**Phase D — Commit individually** so progress is tracked per chapter.

### Task 5: `codes.md` — Building Codes

**Files:** Create `docs/handbook/codes.md`

**Primary sources to fetch:**
- GB 50096-2011 住宅设计规范 (China residential design code) — search openlaw.cn or chinabuilding standards
- GB 50352-2019 民用建筑设计统一标准 (China civil building unified standard)
- GB 50763-2012 无障碍设计规范 (China accessibility design code)
- GB 50016-2014 建筑设计防火规范 (China fire safety in building design)
- ADA Standards 2010 (US accessibility, for international reference)

**Required content:**
- Minimum room dimensions (residential bedroom, living room, kitchen, bathroom) per GB 50096
- Minimum corridor / circulation widths (residential + commercial) per GB 50352
- Minimum door widths and accessibility clearances per GB 50763 + ADA
- Fire egress travel distances + emergency exit count thresholds per GB 50016
- Notes on when these apply (residential vs commercial vs mixed-use)

- [ ] **Step 1**: WebFetch each source above; record the actual section numbers and tables you find.
- [ ] **Step 2**: Write `docs/handbook/codes.md` per the template, citing every value.
- [ ] **Step 3**: Verify with `grep -c "(per " docs/handbook/codes.md` — should be ≥ 8 inline citations.
- [ ] **Step 4**: `git add docs/handbook/codes.md && git commit -m "docs(handbook): codes.md (GB 50096/50352/50763/50016 + ADA)"`

### Task 6: `lighting.md` — Lighting Design

**Files:** Create `docs/handbook/lighting.md`

**Primary sources:**
- GB 50034-2013 建筑照明设计标准 (China lighting standard) — Lux table 5.1 onwards
- IES Lighting Handbook 10th ed. (key section: indoor recommended illuminance)
- CIE 13.3-1995 (color rendering index method)
- CIE 015:2004 (colorimetry, Kelvin scale)
- Blender Manual: Lights (https://docs.blender.org/manual/en/latest/render/lights/index.html)

**Required content:**
- Layered lighting model (ambient / accent / task / decorative) — cite design pedagogy reference
- Kelvin ranges by space type (residential 2700-3000, retail 3000-3500, hospitality 2200-2700, office 3500-4000) per GB 50034 + IES
- Recommended lux values per space type per GB 50034 Table 5.1
- CRI (Ra) minimums per space type per GB 50034 + CIE 13.3
- Fixture spacing rules of thumb (downlight pitch, distance to walls) — per IES + Neufert
- Kelvin → Blender light color mapping note (Blender accepts Kelvin directly; cite Blender Manual)

- [ ] **Step 1**: WebFetch GB 50034 + IES + Blender Manual lights page.
- [ ] **Step 2**: Write `docs/handbook/lighting.md` with citations.
- [ ] **Step 3**: Verify ≥ 10 inline citations.
- [ ] **Step 4**: Commit `docs(handbook): lighting.md (GB 50034 + IES + CIE)`.

### Task 7: `spatial.md` — Clearances & Circulation

**Files:** Create `docs/handbook/spatial.md`

**Primary sources:**
- Neufert Architects' Data, current edition (Living Rooms, Kitchens, Bedrooms, Bathrooms, Offices, Restaurants chapters)
- Time-Saver Standards for Interior Design (Reznikoff)
- Human Dimension & Interior Space — Panero & Zelnik (1979) — figures 130-200 cover residential dimensions
- GB 50096-2011 (residential minimum dimensions, complement to codes.md)

**Required content:**
- Furniture clearances: sofa-to-coffee-table, dining chair pull-back, bed perimeter, kitchen aisle widths
- Circulation widths: primary path, secondary path, accessibility-grade path
- Eye level: standing 1.55-1.65m, seated 1.10-1.20m (per Panero/Zelnik)
- Sight-line rules: focal-point distance, TV viewing distance vs screen size
- Furniture grouping rules: conversation distance 1.8-2.4m

- [ ] **Step 1**: WebFetch Neufert TOC + Panero summary + GB 50096 sections.
- [ ] **Step 2**: Write chapter with ≥ 12 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): spatial.md (Neufert + Panero + GB 50096)`.

### Task 8: `materials.md` — PBR & Color Theory

**Files:** Create `docs/handbook/materials.md`

**Primary sources:**
- Disney BSDF paper (Burley 2012 — "Physically Based Shading at Disney")
- Adobe Substance documentation: PBR guide
- Blender Manual: Principled BSDF (https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html)
- Munsell Color System reference + Pantone color systems
- Josef Albers — *Interaction of Color* (color adjacency principles)
- 60-30-10 rule — sourced from interior-design pedagogy (cite a specific named publication, e.g. Architectural Digest "Designer's Color Wheel" features)

**Required content:**
- PBR roughness bands by material category (metals, plastics, fabrics, ceramics, woods) — cite Substance docs
- Albedo value ranges for diffuse materials per Disney BSDF
- Energy conservation rule (cite Disney BSDF)
- 60-30-10 color split convention with source
- Color adjacency (warm-warm, cool-cool, accent-complement) per Albers
- ORM packing convention (Occlusion-Roughness-Metallic) per Substance

- [ ] **Step 1**: WebFetch Disney BSDF paper, Substance docs, Blender Manual Principled BSDF.
- [ ] **Step 2**: Write chapter with ≥ 10 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): materials.md (Disney BSDF + Substance + Albers)`.

### Task 9: `camera.md` — Architectural Photography

**Files:** Create `docs/handbook/camera.md`

**Primary sources:**
- Norman McGrath — *Photographing Buildings Inside and Out* (canonical reference)
- ASMP architectural photography guidelines
- Blender Manual: Camera (https://docs.blender.org/manual/en/latest/render/cameras.html)
- DSLR architectural lens convention (24-35mm full-frame equivalent — sourced from named photographer guides)

**Required content:**
- Recommended focal length range for interiors (24-35mm full-frame equiv) — cite McGrath / ASMP
- Eye-height conventions (standing, seated, lower for spatial sense) — cite McGrath
- Vertical-lines-stay-vertical principle + tilt-shift correction — cite McGrath
- Composition templates (rule of thirds, leading lines, symmetry choice) — cite published photography texts
- Common framings: hero (3-quarter), corner shot, eye-level cross, detail crop
- Blender setup: lens length input, sensor size, shift X/Y for tilt-shift simulation — cite Blender Manual

- [ ] **Step 1**: WebFetch McGrath summaries, ASMP, Blender Manual camera page.
- [ ] **Step 2**: Write chapter with ≥ 8 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): camera.md (McGrath + ASMP + Blender Manual)`.

### Task 10: `styling.md` — Composition & Vignettes

**Files:** Create `docs/handbook/styling.md`

**Primary sources:**
- *The Interior Design Reference & Specification Book* (Rockport 2013)
- Vincent Van Duysen / Axel Vervoordt published interviews (composition principles)
- Architectural Digest "How to Style a Coffee Table" feature (or equivalent named feature)
- *The Visual Display of Quantitative Information* — Tufte (negative-space principles)

**Required content:**
- Triangle composition for prop arrangements
- Three-size rule (large/medium/small per surface)
- Negative space — at least 30% empty per surface — cite Tufte / Vervoordt principle
- Texture variation rule (rough + smooth + soft)
- Asymmetry vs symmetry — when to use which (cite Vervoordt)
- Common mistakes ("emptyset", "all-the-same-height")

- [ ] **Step 1**: WebFetch named publication summaries.
- [ ] **Step 2**: Write chapter with ≥ 6 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): styling.md (Rockport + Vervoordt + Tufte)`.

### Task 11: `render-output.md` — View Transforms & Hero Shots

**Files:** Create `docs/handbook/render-output.md`

**Primary sources:**
- Blender Manual: Color Management (https://docs.blender.org/manual/en/latest/render/color_management.html)
- Troy Sobotka's AgX paper / commit notes (introducing AgX into Blender)
- Filmic-Blender README on GitHub
- ACES Central documentation (alternative pipeline for context)

**Required content:**
- View transforms: AgX (default in Blender 4.x), Filmic (legacy), Standard (avoid for hero shots) — cite Blender Manual + AgX paper
- Why Standard sRGB clips highlights and is unsuitable for interior renders — cite AgX paper
- Recommended exposure bracketing for hero shots (-1, 0, +1 stops) — cite ASMP
- Cycles vs EEVEE Next sample-count guidance — cite Blender Manual
- Hero / corner / detail / plan / elevation set composition

- [ ] **Step 1**: WebFetch Blender Manual color management + AgX commit notes.
- [ ] **Step 2**: Write chapter with ≥ 6 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): render-output.md (Blender Manual + AgX + Sobotka)`.

### Task 12: `discovery.md` — Questionnaire Mechanics

**Files:** Create `docs/handbook/discovery.md`

**Primary sources:**
- *The Design of Everyday Things* — Norman (1988 / revised 2013) — projective question theory
- Susan Weinschenk — *100 Things Every Designer Needs to Know About People* (2011) — sensory memory references
- Customer-research methodology references — IDEO Method Cards, Stanford d.school crash course
- Polar/Likert scale design — Fink (2003) *How to Conduct Surveys*

**Required content:**
- The 5 question types (direct, projective, metaphor, sensory, visual A/B) with cited rationale for each
- Why projective + sensory questions extract more from non-experts (cite Weinschenk + Norman)
- Adaptive depth: when to short-circuit, when to ask follow-ups (heuristic, cite IDEO)
- Mid-questionnaire feedback loop rationale (cite Fink on respondent fatigue)
- Output schema: taste-profile.json field-by-field with type and source-of-derivation

- [ ] **Step 1**: WebFetch Norman / Weinschenk / IDEO sources + Fink survey design.
- [ ] **Step 2**: Write chapter with ≥ 6 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): discovery.md (Norman + Weinschenk + IDEO + Fink)`.

### Task 13: `project-types.md` — Multi-Space Organization

**Files:** Create `docs/handbook/project-types.md`

**Primary sources:**
- Neufert Architects' Data (Apartment, Restaurant, Office Building chapters)
- Time-Saver Standards for Building Types
- GB 50352 (general civil building principles)
- IBC chapter on occupancy classification

**Required content:**
- Project-type taxonomy: residential apartment, detached house, cafe/lounge, restaurant, retail boutique, small office
- For each: required spaces, typical adjacency rules, expected square-meter range, typical occupant density
- Multi-space adjacency principles (kitchen ↔ dining, entry ↔ public rooms, sleeping ↔ bath, service vs front-of-house separation in commercial)
- Blender collection layout convention from this project's spec

- [ ] **Step 1**: WebFetch Neufert + Time-Saver TOC + GB 50352.
- [ ] **Step 2**: Write chapter with ≥ 6 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): project-types.md (Neufert + Time-Saver + GB 50352)`.

### Task 14: `furniture.md` — Furniture Types & Dimensions

**Files:** Create `docs/handbook/furniture.md`

**Primary sources:**
- Neufert Architects' Data (furniture sections)
- GB/T 3324 木家具通用技术条件 (Chinese furniture standards)
- BIFMA seating standards (commercial)
- Panero & Zelnik (residential furniture dimensions)

**Required content:**
- Sofa typology: 2-seat / 3-seat / sectional / chaise / loveseat — typical dimensions per Neufert
- Dining table sizing by occupancy (4-person 80×120, 6-person 90×180, etc.) per Neufert + Panero
- Bed standards: single, double, queen, king sizes (intl + Chinese GB)
- Office desks: standard depth/width per BIFMA + Neufert
- Storage: wardrobe depth, shelving rules, kitchen cabinet modules
- Common ranges for height (sofa seat 0.40-0.46m, dining seat 0.45-0.48m, bar stool 0.65-0.85m) per Neufert

- [ ] **Step 1**: WebFetch Neufert + GB/T 3324 + Panero summaries.
- [ ] **Step 2**: Write chapter with ≥ 10 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): furniture.md (Neufert + GB/T 3324 + Panero + BIFMA)`.

### Task 15: `acoustics.md` — Absorption & Isolation

**Files:** Create `docs/handbook/acoustics.md`

**Primary sources:**
- GB 50118-2010 民用建筑隔声设计规范 (China sound isolation in buildings)
- ASTM E90 (transmission loss test method)
- ASTM E413 (Sound Transmission Class — STC)
- NRC (Noise Reduction Coefficient) reference table — published by manufacturer associations
- Beranek — *Concert Halls and Opera Houses* (acoustical reference)

**Required content:**
- NRC values for common interior materials (carpet, fabric panel, plaster, glass, hardwood, concrete) — cite manufacturer associations + Beranek
- STC (Sound Transmission Class) thresholds per residential / commercial wall partition — cite GB 50118 + ASTM E413
- When acoustics matters: restaurants/cafes need RT60 < 0.6s — cite Beranek + restaurant design refs
- Acoustic-fix recipes: ceiling cloud panels, fabric wall hangings, soft furniture density — cite acoustical engineering pubs

- [ ] **Step 1**: WebFetch GB 50118 + ASTM summaries + NRC tables.
- [ ] **Step 2**: Write chapter with ≥ 6 inline citations.
- [ ] **Step 3**: Commit `docs(handbook): acoustics.md (GB 50118 + ASTM + Beranek)`.

---

## Task 16: Example Style — `styles/scandinavian.md`

**Files:** Create `docs/handbook/styles/scandinavian.md`

**Primary sources for THIS chapter:**
- *Scandinavian Design* — Charlotte & Peter Fiell (Taschen, current edition)
- *Hygge: The Danish Way to Live Well* — Wiking (2016)
- Architectural Digest features tagged "Scandinavian"
- Dezeen articles on named Scandinavian residential projects (e.g. Norm Architects, Vipp residences)

**Required content per the style template:**
- Anchor description (2-3 sentences) — cite Fiell
- Color palette (60-30-10 hex values) — derive from named projects + cite specific AD/Dezeen features
- Material vocabulary (in / out) — cite Fiell + Wiking
- Lighting profile: Kelvin range, layer mix — cite GB 50034 cross-reference + Wiking
- Camera bias — typically wide soft daylight; cite Norm Architects-style features
- Prop vocabulary — cite Wiking on hygge objects
- Reference images — list 3-5 named projects with publication source
- Common mistakes — cite design critiques

- [ ] **Step 1**: WebFetch Fiell summary + AD/Dezeen Scandinavian features.
- [ ] **Step 2**: Write `docs/handbook/styles/scandinavian.md` with ≥ 8 named-project / source citations.
- [ ] **Step 3**: Commit `docs(handbook): styles/scandinavian.md (Fiell + Wiking + AD + Dezeen)`.

---

## Task 17: Example Space-Type — `space-types/living-room.md`

**Files:** Create `docs/handbook/space-types/living-room.md`

**Primary sources:**
- Neufert Architects' Data — Living Rooms section
- Panero & Zelnik figures 130-150
- GB 50096-2011 §5.2 (room dimensions)
- Time-Saver Standards for Interior Design

**Required content:**
- Typical area range (Chinese urban apartment 12-30 m²) — cite GB 50096 + market data
- Required clearances (sofa-to-table, TV-to-sofa) — cite Neufert + Panero
- Furniture inventory (must-have, common, optional) — cite Neufert
- Lighting layer recipe specific to living room (ambient 100-200 lx, accent 200-400 lx for reading corners) — cite GB 50034 Table 5.1
- Camera view set: hero (3-quarter from entry), corner (sofa-cluster), detail (coffee table styling), plan
- Cross-references to spatial.md, lighting.md, codes.md

- [ ] **Step 1**: WebFetch Neufert living-room section + Panero figures + GB 50096 §5.2.
- [ ] **Step 2**: Write chapter with ≥ 8 citations.
- [ ] **Step 3**: Commit `docs(handbook): space-types/living-room.md (Neufert + Panero + GB)`.

---

## Task 18: Claude Skill — `interior-discovery-intake`

**Files:** Create `.claude/skills/interior-discovery-intake.md`

- [ ] **Step 1: Create skill file**

```markdown
---
name: interior-discovery-intake
description: Use when the user begins a new interior-design project, says "start a new design", "begin design", "I want to redesign my X", or invokes any project-creation language. Runs the discovery questionnaire (per docs/handbook/discovery.md) to extract a taste profile before any modeling or moodboard work.
---

# interior-discovery-intake

You have been invoked because the user is about to start a new interior-design project. Your job is to run the Discovery questionnaire and produce a `taste-profile.json` before any 3D work begins.

## Required reading

Before asking the first question, call:

1. `read_design_handbook(chapter="discovery")` — questionnaire mechanics, the 5 question types, the scoring algorithm.
2. `read_design_handbook(chapter="project-types")` — project-type taxonomy, required spaces.

## Process

1. Confirm project type with the user (residential apartment / detached house / cafe / restaurant / retail / office / other) using a Type-1 direct question.
2. Run the Deep questionnaire (25-30 questions) per the schema in `discovery.md`.
3. Use all 5 question types in roughly the proportions specified in `discovery.md`.
4. **Always include a free-input option** as a fallback for every question.
5. **Multi-select where appropriate** for taste questions — a single answer often misrepresents real preferences.
6. **Around question 12**, surface a mid-questionnaire inferred-style hypothesis. Ask the user to confirm or correct before continuing.
7. **Trigger conflict-clarifier mid-stream** if user's later answers contradict earlier ones (per discovery.md trigger D).
8. After the final question, write `taste-profile.json` to the project root (call `update_taste_profile` MCP tool when available; in Slice 1 just write the file directly via the file system if the tool isn't ready yet).

## Skip path

If the user explicitly declares a known style ("I want Japanese 侘寂"), set `explicit_style` in the profile, capture lifestyle / occupancy basics with 5-7 short Type-1 questions only, and skip the rest.

## Cite the handbook

When explaining why you ask a particular question, cite `discovery.md` and the relevant question-type theory. Do not invent rationale.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/interior-discovery-intake.md
git commit -m "feat(skill): interior-discovery-intake (project init triggers questionnaire)"
```

---

## Task 19: Claude Skill — `interior-style-locking`

**Files:** Create `.claude/skills/interior-style-locking.md`

- [ ] **Step 1: Create skill file**

```markdown
---
name: interior-style-locking
description: Use when the user wants to lock a style direction, generate moodboards, says "moodboard", "lock the style", "I want X feel", "show me ideas", or otherwise establishes the visual direction before 3D modeling.
---

# interior-style-locking

Run the moodboard / style-lock phase: generate 3-5 candidate directions aligned with the existing taste profile, present them, let the user select one, and write the locked palette + material vocabulary into the project's taste-profile.json.

## Required reading

Before generating images, call:

1. `read_design_handbook(query="<inferred style name from taste profile>")` — load the matching `styles/*.md`.
2. `read_design_handbook(chapter="materials")` — color rules, palette construction.
3. `read_design_handbook(chapter="codes")` — for any commercial project, glance at constraints that limit material choices (fire rating, accessibility).

## Process

1. Read the project's existing `taste-profile.json`. If missing, redirect to `interior-discovery-intake`.
2. Construct image-gen prompts using the style chapter's vocabulary (palette hex, material list, lighting profile).
3. Use existing image-gen MCP tools (`generate_image_codex`, `generate_image_openai`, etc.) to produce 3-5 candidates per major direction.
4. Present candidates to the user; let them pick.
5. On selection, write back into `taste-profile.json`:
   - `locked_style` (canonical name from the styles chapter)
   - `locked_palette` (60-30-10 hex)
   - `locked_material_vocab` (in/out lists)
   - `locked_anchor_images` (file paths to selected candidates)
6. Snapshot project state (call `version_snapshot` when available; in Slice 1, copy the .blend + jsons into snapshots/2.5-moodboard-v<N>/).

## Cite the handbook

Every claim about "Scandinavian uses light wood" must cite the style chapter, e.g. "(per styles/scandinavian.md, citing Norm Architects feature in Dezeen 2019)". Never speak generically about a style.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/interior-style-locking.md
git commit -m "feat(skill): interior-style-locking (moodboard + palette lock)"
```

---

## Task 20: Claude Skill — `interior-plain-language-edit`

**Files:** Create `.claude/skills/interior-plain-language-edit.md`

- [ ] **Step 1: Create skill file**

```markdown
---
name: interior-plain-language-edit
description: Use when the user issues a plain-language modification command on an existing 3D scene — verbs like "move", "swap", "change", "make warmer", "more X", "less X", "darker", "lighter", "remove that", "add a Y", or any imperative referencing scene content.
---

# interior-plain-language-edit

The user wants to modify the current Blender scene using natural language. Parse the intent, route to the right MCP tools, and execute. Stay silent unless a quality gate fires.

## Required reading

Load on demand based on the parsed intent:

- Geometry / placement edits → `read_design_handbook(chapter="spatial")`
- Material / color edits → `read_design_handbook(chapter="materials")`
- Lighting edits → `read_design_handbook(chapter="lighting")`
- Composition / styling edits → `read_design_handbook(chapter="styling")`

## Intent parsing

| User says | Tool route |
|---|---|
| "move X to Y" / "挪到" | `get_object_info(name=X)` → compute new transform → existing transform tool |
| "swap X for Y" / "换成" | `delete_objects(name=X)` + asset search/place |
| "make it warmer" / "更暖一点" | identify lights → reduce Kelvin per lighting.md range |
| "darker" / "lighter" | adjust apply_material_color brightness OR exposure |
| "more X" / "less X" (props) | `scatter_on_surface` + count delta |
| "remove that" | `delete_objects(name=last_referenced_object)` |
| "add a Y" | search asset providers in priority order: Sketchfab → PolyHaven → AmbientCG → AI generation |

## Loop classification

Per the spec § "Loop Architecture":

- L1 (within Stage 5 render-tweak) — silent execute.
- L2 (back to materials/lighting) — silent execute.
- L3 (back to layout / Stage 3-4) — execute + auto-snapshot prior state + record version-log entry.
- L4 (style change / back to Stage 2.5) — STOP and prompt user with 3-choice (branch / overwrite / cancel). Do not silently execute L4.

## Quality gates

After every edit that affects the rendered output, run `audit_interior_scene` (when extended in Slice 3). For Slice 1, this skill exists but most underlying audit functionality lands later — focus on intent parsing + tool routing being correct.

## Cite when explaining

If a user asks "why" you did something, cite the handbook chapter that drove the choice.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/interior-plain-language-edit.md
git commit -m "feat(skill): interior-plain-language-edit (NL → MCP routing + loop classification)"
```

---

## Task 21: Claude Skill — `interior-render-direction`

**Files:** Create `.claude/skills/interior-render-direction.md`

- [ ] **Step 1: Create skill file**

```markdown
---
name: interior-render-direction
description: Use when the user wants to render — "render", "make a hero shot", "show me how it looks", "出图", "do a final render", or after any major edit when the user asks to see results.
---

# interior-render-direction

Plan and execute renders. Decide camera framing, run the audit, fix gates, render, return previews.

## Required reading

1. `read_design_handbook(chapter="camera")` — focal length, eye height, composition.
2. `read_design_handbook(chapter="render-output")` — view transforms, exposure, sample counts.
3. `read_design_handbook(chapter="lighting")` — sanity-check before render.

## Render mode classification

- **Exploration render** (during stage 3-4 iteration): exposure = 0, samples = 64 Cycles / 32 EEVEE Next, view transform AgX, 1080p. Audit only 🔴 gates.
- **Hero render** (stage 5 final / stage 6): bracket -1/0/+1, samples ≥ 512 Cycles / ≥ 128 EEVEE Next, view transform AgX, 4K. Audit ALL 🔴/🟡/🔵 gates.
- **Construction-grade** (stage 6.5 deliverables): samples high, packed textures required (gate #9 upgraded to 🔴), audit STRICT.

## Process

1. Identify render mode from user phrasing.
2. Load handbook chapters above.
3. If no camera exists, run `create_interior_camera_set` per the project type.
4. Run `audit_interior_scene` in the appropriate strictness mode.
5. If any 🔴 fires: surface to user with citation, suggest one-call fix. Do NOT auto-`force=True`.
6. Once gates pass, call `render_view_set`.
7. Return previews via `render_image(return_preview=True)` when single-view.
8. Call `version_snapshot` if hero or final render (medium frequency rule).

## Cite when gates fire

Every gate violation must include the handbook chapter + section that defines the rule. Example response when gate #2 (lighting layers) fires:

> "Render blocked by quality gate #2 (lighting layers). The scene has only 1 light source. Per lighting.md §1.2 (citing IES Lighting Handbook 10th ed., Indoor Lighting), interior renders require ambient + accent at minimum. Suggested fix: `setup_interior_lighting_plan(zones=['<zone>'], layers=['ambient','accent'])`."
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/interior-render-direction.md
git commit -m "feat(skill): interior-render-direction (render planning + gate handling)"
```

---

## Task 22: Claude Skill — `interior-construction-handoff`

**Files:** Create `.claude/skills/interior-construction-handoff.md`

- [ ] **Step 1: Create skill file**

```markdown
---
name: interior-construction-handoff
description: Use when the user wants to produce construction-grade deliverables — "施工图", "construction docs", "BoM", "ready to ship", "give me the spec for the contractor", or signals the project is moving from design to build.
---

# interior-construction-handoff

Produce the final handoff package: dimensioned plans, elevations, sections, BoM, finish schedule, audit report.

## Required reading

1. `read_design_handbook(chapter="codes")` — validate against accessibility/fire/structural before handoff.
2. `read_design_handbook(chapter="render-output")` — final render set conventions.
3. `read_design_handbook(chapter="project-types")` — project-type-specific deliverables.

## Process

1. Run a STRICT-mode `audit_interior_scene` (all 🔴 + 🟡 + 🔵, gate #9 upgraded to 🔴).
2. If any gate fails, surface with citations. Do not let a failing gate ship.
3. Render the construction-grade view set (hero + corner + detail + plan + elevation per applicable space-type chapter).
4. Generate dimensioned 2D outputs (plan, key elevations) — call `export_construction_docs` (lands Slice 4 — for now, mark as "pending Slice 4").
5. Produce the BoM from `procurement.json` + `read_chapter('finishes')` (when material list mature).
6. Final audit-report writes alongside renders.

## Note for Slice 1

Most `export_construction_docs` machinery lands in Slice 4. In Slice 1, this skill should:

- Guide the user through manual export of renders + a markdown BoM stub.
- Cite codes.md when explaining what a contractor will need.
- Set the user's expectation that machine-generated dimensioned drawings ship in Slice 4.

## Cite

Every line item in the handoff package must trace to a handbook chapter for justification.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/interior-construction-handoff.md
git commit -m "feat(skill): interior-construction-handoff (final-deliverable orchestration)"
```

---

## Task 23: Acceptance Gate Test

**Files:** Create `tests/test_handbook_acceptance.py`

- [ ] **Step 1: Write the acceptance gate test**

```python
"""Acceptance gate for Slice 1 handbook authoring.

Per docs/dev/specs/2026-04-29-interior-design-workflow-design.md
§ "Sources & Citation Policy", every numeric claim in the handbook must
trace to a cited authoritative source.

This test samples the handbook for likely-numeric content and asserts
that a citation marker appears nearby. It is a heuristic — not a proof —
but catches the most common failure (writing rules without sourcing).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from blender_mcp._handbook import list_chapters, read_chapter

# A "numeric claim line" is a markdown line containing a number followed
# by a unit (mm, cm, m, K, lx, lux, %, dB, etc.) or a temperature K range.
NUMERIC_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s?"
    r"(?:mm|cm|m\b|m²|sqm|K\b|kelvin|lx|lux|°|dB|%|RA|Ra|NRC|STC)\b",
    re.IGNORECASE,
)

# A "citation marker" is a parenthetical containing the word "per"
# or a colon-separated source-and-section reference.
CITATION_PATTERN = re.compile(r"\(per\s+[^\)]+\)|see\s+[^\n]+§|cf\.\s+[^\n]+")


def _numeric_claims_with_window(content: str, window_chars: int = 200):
    """Yield (claim_text, surrounding_text) pairs for each numeric claim."""
    for match in NUMERIC_PATTERN.finditer(content):
        start = max(0, match.start() - window_chars)
        end = min(len(content), match.end() + window_chars)
        yield match.group(0), content[start:end]


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
    """Heuristic: every numeric claim should have a citation within 200
    chars. This catches the most common failure (writing rules without
    sourcing them)."""
    failures = []
    for slug in list_chapters():
        content = read_chapter(slug)
        for claim, window in _numeric_claims_with_window(content):
            if not CITATION_PATTERN.search(window):
                failures.append((slug, claim))
    # Allow up to 10% unsourced numerics (e.g. example dimensions in
    # worked examples, table-of-contents counts) but flag if more.
    total = sum(
        len(list(_numeric_claims_with_window(read_chapter(s))))
        for s in list_chapters()
    )
    if total == 0:
        pytest.skip("no numeric claims discovered yet — chapters not landed")
    pct = 100 * len(failures) / max(1, total)
    assert pct < 10, (
        f"{len(failures)}/{total} numeric claims ({pct:.1f}%) lack a "
        f"nearby citation. First 5 offenders: {failures[:5]}"
    )


def test_no_fabricated_section_markers():
    """Spot-check: section markers like 'GB 50034 §5.1.5' must follow a
    plausible pattern (digit . digit . digit). Reject obviously-faked
    references like 'GB §abc' or 'GB §99.99.99.99'."""
    bad_markers = []
    for slug in list_chapters():
        content = read_chapter(slug)
        # Find all GB section refs
        for m in re.finditer(r"GB\s*\d+[\-\d]*\s*§\s*([^\s,;\)]+)", content):
            section = m.group(1)
            # Plausible: digits + dots, max depth 4
            if not re.fullmatch(r"\d+(\.\d+){0,4}", section):
                bad_markers.append((slug, m.group(0)))
    assert not bad_markers, (
        f"implausible GB section markers (likely fabricated): {bad_markers}"
    )
```

- [ ] **Step 2: Run the acceptance gate**

```bash
.venv/bin/pytest tests/test_handbook_acceptance.py -v
```

Expected: passes (or skips with "no numeric claims discovered yet" if chapters are stubs).

- [ ] **Step 3: Commit**

```bash
git add tests/test_handbook_acceptance.py
git commit -m "test: handbook acceptance gate (citation coverage + section-marker sanity)"
```

---

## Task 24: Final Push

- [ ] **Step 1: Run all tests once more**

```bash
.venv/bin/pytest tests/ -v
```

Expected: all green or skipped. Failures must be triaged before push.

- [ ] **Step 2: Push to fork**

```bash
git push fork sprint-6-quality-of-life
```

- [ ] **Step 3: Verify branch state**

```bash
git log --oneline fork/sprint-6-quality-of-life..sprint-6-quality-of-life || echo "in sync"
git log --oneline -10
```

Expected: local branch matches `fork/sprint-6-quality-of-life`.

---

## Out of scope for Slice 1 (deferred)

- Remaining 16 styles (Slice 5)
- Remaining 7 space-types (Slice 5)
- `run_discovery_questionnaire` MCP tool implementation (Slice 2)
- `audit_interior_scene` 9-dimension extension (Slice 3)
- All construction-doc machinery (Slice 4)
- LiDAR scan auto-walls (deferred indefinitely)

## Self-review checklist (executed inline)

- ✅ Every numeric handbook claim must be sourced (codified in tasks 5-17 + acceptance gate task 23)
- ✅ MCP tool: TDD pattern (test → impl → verify → commit) in tasks 2-4
- ✅ Skills: each task creates one self-contained skill file with citation expectations baked in
- ✅ No "TODO / fill in details" placeholders in code steps
- ✅ Type consistency: `read_chapter` / `list_chapters` / `search_chapters` names used identically across tasks 2, 3, 4
- ✅ File paths: every Create/Modify line is an absolute-or-clear-relative path
- ✅ All commands runnable from repo root with `.venv/bin/<tool>` (matches existing pyproject.toml setup)
