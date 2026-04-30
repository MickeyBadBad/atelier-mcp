# Slice 7 — Construction Document Generation (PDF Plans + Elevations)

> **For agentic workers:** Use superpowers:executing-plans. Heavier than Slices 2-6 because it needs Blender-side bpy work + a PDF library. Estimated 2-4 hours.

**Goal:** Generate a contractor-ready construction document set: dimensioned plan, dimensioned elevation per major wall, finish schedule, BoM, and a single combined PDF. This is the deliverable that goes from "renders look pretty" to "施工队 can build it".

**Architecture:** Two layers. Pure-Python `_construction_docs.py` orchestrates the pipeline (calls into Blender for orthographic renders, runs PDF assembly). Blender-side: a new addon command `render_orthographic_view` that renders top-down or straight-on with explicit ortho-scale + dimension annotations. PDF assembly uses `reportlab` (pure Python, well-known, ships in PyPI).

**Tech Stack:** Python 3.10+, reportlab (new dep), existing render_view_set / quick_export MCP tools, addon socket protocol.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/blender_mcp/_construction_docs.py` | Orchestrate plan/elevation rendering, PDF assembly |
| `addon.py` | New socket commands: `render_orthographic_view`, `compute_room_extents` |
| `src/blender_mcp/server.py` | 1 new MCP tool: `export_construction_docs` |
| `tests/test_construction_docs.py` | Pure-Python tests (PDF assembly + dimension math, no bpy) |
| `pyproject.toml` | Add `reportlab` to deps |

---

## Task 1: PDF Assembly (Pure Python, no Blender)

`_construction_docs.py` exports a `build_construction_pdf(project_root, output_path) -> dict` that:

1. Reads `<project>/exports/renders/plan.png`, `elevation_<wall>.png` (already rendered by upstream task)
2. Reads `taste-profile.json`, `procurement.json`
3. Calls `_bom.render_bom_markdown` → embeds in PDF
4. Builds a multi-page PDF using reportlab:
   - Cover page (project name, palette swatches, key dimensions summary)
   - Plan page (dimensioned plan + scale bar + north arrow)
   - One elevation page per major wall
   - Finish schedule table (object → material → SKU)
   - BoM table
   - Audit report appendix
5. Returns `{pdf_path, page_count, summary}`

Tests cover dimension-string formatting, scale-bar geometry, page count vs input image count.

## Task 2: Blender-Side `render_orthographic_view` Command

`addon.py` adds a socket command (matches the existing pattern for `set_camera_view` etc.):

```python
def render_orthographic_view(self, params):
    """
    Render a true orthographic top-down (plan) or front (elevation) view
    of the requested zone or whole scene.

    Params:
        view: "plan" | "elevation_north" | "elevation_south" | "elevation_east" | "elevation_west"
        zone: optional Blender collection name (defaults to whole scene)
        output_path: absolute PNG path
        ortho_scale: float (auto-computed from zone bbox if absent)
        annotate_dimensions: bool (uses Blender's grease-pencil overlay)

    Returns: {output_path, ortho_scale_used, bbox_world}
    """
```

Implementation steps:

- Compute zone bbox (existing `_world_bbox` helper or new `compute_room_extents`)
- Create temp orthographic camera positioned to capture bbox
- Use Standard view transform (one of the only legitimate uses — see `render-output.md`)
- Set Blender world to white, disable HDRI for plan/elevation clarity
- Render
- If `annotate_dimensions=True`, post-process: overlay grease pencil dimension lines via bpy

## Task 3: `export_construction_docs` MCP Tool

Wraps everything:

```python
@mcp.tool()
@tool_envelope
def export_construction_docs(
    ctx: Context,
    project_root: str,
    include_walls: list[str] = None,  # default: north/south/east/west
    output_filename: str = "construction-docs.pdf",
) -> str:
    """
    Generate the full construction document set as a single PDF.

    Pipeline:
    1. For each wall in include_walls + plan: call render_orthographic_view
    2. Build BoM via existing generate_bom
    3. Build finish schedule from current scene materials
    4. Run audit_interior_quality in 'construction' strictness mode
    5. Assemble all into PDF via _construction_docs.build_construction_pdf
    6. Return PDF path + summary
    """
```

## Task 4: PDF Plan Reference (Slice 6 deferred from Slice 1)

Adds PDF→image conversion for `import_plan_reference` so users can pass an architect's PDF directly. Uses pdf2image (poppler-backed) — **optional dep**; if poppler not installed, return BAD_INPUT with install hint.

## Task 5: Tests + commit + push

- Pure-Python tests for PDF assembly (without bpy)
- Manual verification: a sample project + simple test scene → run `export_construction_docs` → open PDF, confirm pages render correctly
- Commit `feat: Slice 7 — construction docs (PDF plans + elevations + BoM)`

## Acceptance

After Slice 7, an AI can take a project that's passed audit_interior_quality(strictness='construction') and emit a single PDF that includes dimensioned plan, elevations for the four walls, finish schedule, BoM, and the audit report. The contractor can read this PDF and build the space.

## Out of scope (deferred again)

- Sectional cuts (drawing a cut plane through the scene) — Slice 8 maybe
- Mechanical/electrical drawings (HVAC, lighting circuits) — much later
- LEED/BREEAM compliance docs — out of scope entirely
