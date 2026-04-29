---
name: interior-plain-language-edit
description: Use when the user issues a plain-language modification command on an existing 3D scene — verbs like "move", "swap", "change", "make warmer", "more X", "less X", "darker", "lighter", "remove that", "add a Y", "挪", "换", "暖一点", "冷一点", or any imperative referencing scene content.
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
| "move X to Y" / "挪到" | `get_object_info(name=X)` → compute new transform → existing transform/translate tool |
| "swap X for Y" / "换成" | `delete_objects(name=X)` + asset search/place |
| "make it warmer" / "更暖一点" | identify lights → reduce Kelvin per `lighting.md` range |
| "darker" / "lighter" | adjust `apply_material_color` brightness OR scene exposure |
| "more X" / "less X" (props) | `scatter_on_surface` + count delta per `styling.md` density rule |
| "remove that" | `delete_objects(name=last_referenced_object)` |
| "add a Y" | search asset providers in priority order: Sketchfab → PolyHaven → AmbientCG → AI generation. Use `asset_query_help` first if unsure how to query. |

## Loop classification

Per the spec § "Loop Architecture":

- **L1** (within Stage 5 render-tweak) — silent execute.
- **L2** (back to materials/lighting) — silent execute.
- **L3** (back to layout / Stage 3-4) — execute + auto-snapshot prior state + record version-log entry.
- **L4** (style change / back to Stage 2.5) — **STOP** and prompt user with 3-choice (branch / overwrite / cancel). Do not silently execute L4.

When unsure which level a request maps to, default to "ask first" — better to confirm than to silently destroy half a day's work.

## Quality gates

After every edit that affects rendered output, run `audit_interior_scene` (when extended in Slice 3). For Slice 1, this skill exists but most underlying audit functionality lands later — focus on intent parsing + tool routing being correct.

## Cite when explaining

If a user asks "why" you did something, cite the handbook chapter that drove the choice. Example:

> "I dropped the Kelvin from 4000K to 2700K because lighting.md §2 (citing GB 50034-2013 §5.1 Table) places residential evening lighting in the 2700-3000K band, and you said 'warmer'."
