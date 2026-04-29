# Slice 6 — Moodboard, Style-Aware Furniture, and Live SKU Fetch

> **For agentic workers:** Use superpowers:executing-plans. Steps use `- [ ]`.

**Goal:** Close the gap between "Discovery + Style Locked" and "3D scene populated" by adding the moodboard candidates / lock cycle, style-aware furniture placement, and live SKU fetching via claude-in-chrome.

**Architecture:** All four new features are wrappers around existing primitives. `generate_moodboard_candidates` calls existing image-gen tools (`generate_image_codex` / `generate_image_openai`) with handbook-derived prompts. `lock_moodboard` writes structured fields back into `taste-profile.json`. `place_furniture_from_style` chains existing `search_sketchfab_models` → `download_sketchfab_model` → `place_on_ground` using style-vocab from the matching `styles/<name>.md` chapter. `extract_sku_from_url` uses claude-in-chrome MCP (when available) to fetch a product page → existing `extract_sku_metadata` to parse.

**Tech Stack:** Python stdlib + Pillow (already installed). No Blender addon changes.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/blender_mcp/_moodboard.py` | Moodboard prompt builder + candidate generation orchestrator |
| `src/blender_mcp/_style_vocab.py` | Parse style-chapter front-matter into structured vocab (palette / materials / fixtures) |
| `src/blender_mcp/server.py` | 4 new MCP tools |
| `tests/test_moodboard.py` | Tests for prompt builder + lock |
| `tests/test_style_vocab.py` | Tests for style-vocab parser |

---

## Task 1: `_style_vocab.py` — Style Chapter Parser

**Files:**
- Create: `src/blender_mcp/_style_vocab.py`
- Test: `tests/test_style_vocab.py`

The style chapters under `docs/handbook/styles/<slug>.md` follow a known structure (palette table, material vocab in/out, lighting profile, prop vocab). This module parses the markdown into a structured object so MCP tools can consume vocab without re-parsing each call.

```python
@dataclass
class StyleVocab:
    slug: str
    anchor_description: str
    palette_60_30_10: list[dict]  # [{role, hex, source_project}]
    materials_in: list[str]
    materials_out: list[str]
    kelvin_range: tuple[int, int]   # parsed from "2700-3000K" patterns
    fixture_keywords: list[str]      # for Sketchfab search
    prop_keywords: list[str]
    reference_projects: list[dict]   # [{designer, project, location, year, publication}]
```

**Tasks:**

- [ ] **Step 1: Write failing tests for `parse_style_chapter`**

```python
def test_parse_scandinavian_extracts_kelvin_range():
    vocab = parse_style_chapter("scandinavian")
    assert 2700 <= vocab.kelvin_range[0] <= 3000

def test_parse_speakeasy_has_warm_palette():
    vocab = parse_style_chapter("speakeasy")
    # All dominant hex values should be warm-leaning (R+G > 1.5*B avg)
    assert any(_is_warm(p["hex"]) for p in vocab.palette_60_30_10)

def test_parse_unknown_style_raises():
    with pytest.raises(StyleVocabError):
        parse_style_chapter("not-a-style")

def test_parse_extracts_materials_in_and_out():
    vocab = parse_style_chapter("japanese-wabi-sabi")
    assert any("wood" in m.lower() or "sumi" in m.lower() for m in vocab.materials_in)
    assert vocab.materials_out  # non-empty
```

- [ ] **Step 2: Implement `parse_style_chapter`** — read the markdown via `_handbook.read_chapter("styles/<slug>")`, then regex/section-walk to extract palette table rows, lists under "### In" / "### Out", Kelvin numbers from "## Lighting profile", reference-project list.

- [ ] **Step 3: Run tests + commit**

## Task 2: `_moodboard.py` — Prompt builder + candidate orchestrator

Generate 3-5 moodboard candidate prompts from a taste profile + style vocab, calling existing image-gen MCP tools.

Function signature:

```python
def build_moodboard_prompts(
    taste_profile: dict,
    style_vocab: StyleVocab,
    n: int = 4,
    space_type: str = "living_room",
) -> list[str]:
    """Each prompt is photorealistic, cites palette hex + material vocab + Kelvin."""
```

Output prompts look like:

```
Photorealistic interior render of a residential living room in
Scandinavian style. Walls in chalky off-white plaster (#EFEAE3),
floor in pale natural oak. One charcoal linen sectional sofa, one
rattan armchair, books and a ceramic vase on a low walnut coffee
table. Lighting: 2800K diffuse warm light from a paper-pendant
lamp (Norm Architects-style). Camera at 24mm focal length, eye-
level (1.5m), 3-quarter framing from the entry. Negative space
30%+. Shot in AgX color management. Architectural photography
style.
```

Tests:
- [ ] `build_moodboard_prompts` returns exactly N prompts
- [ ] Each prompt contains hex values from style palette
- [ ] Each prompt references the space-type
- [ ] Each prompt includes lighting Kelvin within style range

## Task 3: 4 new MCP Tools

```python
@mcp.tool()
@tool_envelope
def generate_moodboard_candidates(
    ctx: Context,
    project_root: str,
    style_slug: str,
    space_type: str = "living_room",
    n: int = 4,
    backend: str = "codex",  # or "openai"
) -> str:
    """
    Generate N moodboard candidate images for a style + space pairing,
    using the project's taste profile.

    Saves images to <project_root>/moodboards/<style_slug>/<n>_<timestamp>.png
    Returns the list of generated paths.
    """
    # 1. Read taste-profile, parse style chapter
    # 2. Build N prompts via _moodboard.build_moodboard_prompts
    # 3. Loop over prompts → call generate_image_codex or _openai
    # 4. Return paths
```

```python
@mcp.tool()
@tool_envelope
def lock_moodboard(
    ctx: Context,
    project_root: str,
    style_slug: str,
    selected_image_paths: list[str],
    palette_override: dict = None,
) -> str:
    """
    Lock the chosen moodboard direction. Writes to taste-profile.json:
    - locked_style: style_slug
    - locked_palette: from style chapter or palette_override
    - locked_material_vocab: in/out lists from style chapter
    - locked_anchor_images: selected_image_paths

    Auto-snapshots the project state before writing.
    """
```

```python
@mcp.tool()
@tool_envelope
def place_furniture_from_style(
    ctx: Context,
    style_slug: str,
    furniture_category: str,
    target_zone_object: str,
    density: float = 0.5,
) -> str:
    """
    Search Sketchfab using style-vocab keywords for the requested furniture
    category, download the top result, place it grounded inside the target
    zone bounding box. Density 0.0-1.0 controls cluster fill.

    Returns: {placed_object: name, sku_metadata: dict}.
    """
    # 1. Load style vocab via _style_vocab.parse_style_chapter
    # 2. Compose Sketchfab query: f"{furniture_category} {style_vocab.fixture_keywords}"
    # 3. search_sketchfab_models → pick top result
    # 4. download_sketchfab_model
    # 5. place_on_ground with target zone bbox
    # 6. Return name + sku metadata
```

```python
@mcp.tool()
@tool_envelope
def extract_sku_from_url(
    ctx: Context,
    url: str,
    page_html: str = "",
    category_hint: str = "other",
) -> str:
    """
    Live SKU metadata extraction. If page_html is empty, instructs the
    AI to use claude-in-chrome MCP to fetch the page, then call this
    tool again with page_html populated.

    When page_html is given, delegates to extract_sku_metadata.
    Returns a draft procurement record ready for record_sku_purchase.
    """
    if not page_html.strip():
        return _tool_response({
            "needs_fetch": True,
            "instruction": (
                "Use claude-in-chrome MCP to fetch the page content, "
                "then call extract_sku_from_url(url, page_html=...) "
                "with the rendered HTML or text."
            ),
            "url": url,
        })
    from ._sku_parse import parse_sku_metadata
    draft = parse_sku_metadata(url, page_html, category_hint)
    return _tool_response({"draft": draft})
```

## Task 4: Tests + commit + push

- [ ] `tests/test_moodboard_mcp.py` — smoke tests verifying all 4 new tools register and accept the documented args
- [ ] Full suite: `pytest tests/ -v` — expect 205 → ~225 passing
- [ ] Commit `feat: Slice 6 — moodboard + style-aware furniture + live SKU fetch`
- [ ] Push to `develop`

## Out of scope for this slice

- Construction-doc PDF generation → Slice 7
- Native addon socket commands → Slice 8
- LiDAR auto-walls → still indefinitely deferred

## Acceptance

After Slice 6 the AI can take a discovery-completed project from "I have a taste profile" to "I have a Blender scene with style-correct furniture and an SKU-tracked moodboard" via 4 tool calls.
