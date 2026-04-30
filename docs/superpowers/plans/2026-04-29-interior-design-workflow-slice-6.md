# Slice 6 — Asset Integration & Moodboard Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans. Steps use `- [ ]`.

**Goal:** Wire the AI's intent ("I want a Scandinavian living room") all the way to actual 3D content — moodboard candidate generation, SKU URL fetching via claude-in-chrome, style-aware Sketchfab furniture placement, and `import_lidar_scan` for iPhone scans.

**Architecture:** Three new pure-Python modules (moodboard, lidar, fetcher) plus four new MCP tools wired to existing fork tools (`generate_image_codex`, `search_sketchfab_models`, `place_on_ground`, `apply_archviz_material`). The claude-in-chrome integration is delegated — this slice just defines the *intent contract* (what URL to fetch, what to do with the returned page content).

**Tech Stack:** Python stdlib only. Reuses existing `_handbook.py` (style chapter loader), `_procurement.py` (record_purchase), `_project.py` (taste-profile read/write), `_sku_parse.py` (extract_sku_metadata).

---

## File Structure

| File | Responsibility |
|---|---|
| `src/blender_mcp/_moodboard.py` | Build image-gen prompts from taste-profile + style chapter; lock moodboard fields back into taste-profile.json |
| `src/blender_mcp/_lidar.py` | Validate LiDAR FBX/GLB import paths, normalize scale + units, return import metadata |
| `src/blender_mcp/_fetch_intent.py` | Build the "fetch this URL" intent envelope for claude-in-chrome callers |
| `src/blender_mcp/server.py` | Add 4 MCP tools |
| `tests/test_moodboard.py` | Tests for prompt builder + lock writer |
| `tests/test_lidar.py` | Tests for FBX/GLB validation + scale heuristics |
| `tests/test_fetch_intent.py` | Tests for URL → fetch-intent envelope |

---

## Task 1: `_moodboard.py` Module

Functions:
- `build_image_prompts(taste_profile, style_chapter_md, n_candidates=4) -> list[str]` — extracts palette hex + material vocab + lighting profile from the style chapter and assembles `n` distinct image-gen prompts (varying camera angle, time of day, mood) for each candidate.
- `lock_moodboard(project_root, locked_style, anchor_images, palette) -> taste_profile` — writes the four `locked_*` fields into `taste-profile.json`. Returns the updated profile.
- `validate_anchor_images(paths) -> list[Path]` — at least 1, at most 5 paths; each must exist; each must be PNG/JPG/WebP.

Tests cover: prompt diversity (no two prompts identical), prompt cites the style chapter (per the citation policy), lock writes all 4 fields, invalid anchor paths rejected.

## Task 2: `generate_moodboard_candidates` MCP Tool

Inputs:
- `project_root: str`
- `n: int = 4`
- `style_hint: str = ""` — optional override; default reads `recommended_style` from taste-profile

Behavior:
1. Read `taste-profile.json` → `recommended_style`.
2. Call `read_design_handbook(chapter=f"styles/{style_hint or recommended_style}")` → markdown.
3. Call `build_image_prompts(profile, style_md, n)` → list of prompts.
4. **Returns the list of prompts** — does NOT call image-gen itself. The AI client picks an image-gen tool (`generate_image_codex`, `generate_image_openai`, `generate_3d_smart`) and runs the prompts itself.

This split keeps the moodboard module independent of any specific image-gen provider.

## Task 3: `lock_moodboard` MCP Tool

Inputs:
- `project_root: str`
- `locked_style: str` — canonical name (e.g. `scandinavian`)
- `anchor_images: list[str]` — file paths to the 1-3 selected candidates
- `palette: dict` — `{"60": "#hex", "30": "#hex", "10": "#hex"}` from the style chapter

Behavior: validates inputs, writes back into taste-profile.json, calls `version_snapshot(label="2.5-moodboard-locked")`.

## Task 4: `place_furniture_from_style` MCP Tool

Inputs:
- `zone: str` — Blender collection name to place into (e.g. `03_ZONES/Living`)
- `style: str` — canonical style name (looked up in handbook)
- `density: str = "medium"` — `low | medium | high`
- `category_filter: list[str] = []` — restrict to e.g. `["sofa", "chair"]`

Behavior:
1. Load `styles/<style>.md` via handbook.
2. Extract the prop vocabulary (sofa types, lamp types, etc.) from the chapter.
3. For each prop type, call existing `search_sketchfab_models(query=...)` with the style chapter's vocabulary.
4. Score results by name relevance + license; pick top-1 per category.
5. Call existing `download_sketchfab_model` + `place_on_ground` + (optionally) `apply_archviz_material`.
6. Tag each placed object with the style name + `source_chapter` custom property.
7. Returns `{placed: [{category, name, sketchfab_uid, position}], skipped: [{category, reason}]}`.

This is the "AI-as-designer" payoff — one tool, one style, the room gets furnished.

## Task 5: `import_lidar_scan` MCP Tool

Inputs:
- `filepath: str` — absolute path to FBX, GLB, or PLY
- `target_collection: str = "00_REFERENCES"`
- `assume_meters: bool = True` — most iPhone scans are in meters; if False, the tool checks scale

Behavior:
1. Validate file exists and is a known format.
2. Call existing addon import path (FBX import for .fbx, GLTF import for .glb).
3. Compute world bbox; warn if scale < 0.5 m or > 50 m (likely wrong unit).
4. Move the imported empty into the target collection.
5. Lock the empty's transform so subsequent `apply_finish` calls don't accidentally rescale.
6. Returns `{root_object, world_bbox, dim_meters}`.

## Task 6: `extract_sku_from_url` MCP Tool (claude-in-chrome contract)

Inputs:
- `url: str`
- `category_hint: str = "other"`

Behavior: returns a *fetch intent* envelope, NOT the parsed metadata. The intent tells the AI client which claude-in-chrome calls to make:

```json
{
  "ok": true,
  "data": {
    "intent": "fetch_and_parse_sku",
    "url": "<url>",
    "category_hint": "<hint>",
    "vendor_hint": "1688",  // detected from URL
    "next_steps": [
      "1. Navigate to <url> via claude-in-chrome (mcp__claude-in-chrome__navigate or browser_navigate)",
      "2. Wait for page load (browser_wait_for or 3s pause)",
      "3. Capture page text via mcp__claude-in-chrome__get_page_text or browser_snapshot",
      "4. Pass URL + page content back to extract_sku_metadata"
    ]
  }
}
```

The actual fetch/scrape happens on the AI side; this tool just hands the AI a recipe. Pure Python, testable.

## Task 7: Integration Tests

A new `tests/test_slice6_integration.py`:
- end-to-end: build_image_prompts → lock_moodboard → version_snapshot exists
- import_lidar_scan path validation against fixture FBX/GLB stubs
- place_furniture_from_style returns expected stub envelope when Blender unavailable

---

## Out of scope for Slice 6

- Real Blender addon execution (place_furniture_from_style returns a *plan*; addon execution lands in Slice 7)
- PDF plan import (Slice 7)
- Style transfer between projects
