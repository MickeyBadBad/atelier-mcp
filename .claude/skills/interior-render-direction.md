---
name: interior-render-direction
description: Use when the user wants to render — "render", "make a hero shot", "show me how it looks", "出图", "do a final render", "渲染", "看看效果", or after any major edit when the user asks to see results.
---

# interior-render-direction

Plan and execute renders. Decide camera framing, run the audit, fix gates, render, return previews.

## Required reading

1. `read_design_handbook(chapter="camera")` — focal length, eye height, composition.
2. `read_design_handbook(chapter="render-output")` — view transforms, exposure, sample counts.
3. `read_design_handbook(chapter="lighting")` — sanity-check before render.

## Render mode classification

Decide the mode from user phrasing and project phase, not from a literal flag:

- **Exploration render** (during Stage 3-4 iteration): exposure 0, samples 64 Cycles / 32 EEVEE Next, view transform AgX, 1080p. Audit only 🔴 gates.
- **Hero render** (Stage 5 final / Stage 6): bracket -1/0/+1, samples ≥ 512 Cycles / ≥ 128 EEVEE Next, view transform AgX, 4K. Audit ALL 🔴/🟡/🔵 gates.
- **Construction-grade** (Stage 6.5 deliverables): samples high, packed textures required (gate #9 upgraded to 🔴), audit STRICT.

## Process

1. **Identify render mode** from user phrasing.
2. **Load the handbook chapters** above.
3. **If no camera exists**, run `create_interior_camera_set` per the project type. Pick views per `render-output.md` and the relevant `space-types/<name>.md`.
4. **Run `audit_interior_scene`** in the appropriate strictness mode.
5. **If any 🔴 fires**: surface to user with citation, suggest a one-call fix. Do NOT auto-`force=True`. Wait for the user to acknowledge or override.
6. **Once gates pass**, call `render_view_set`.
7. **Return previews** via `render_image(return_preview=True)` when a single view is enough.
8. **Call `version_snapshot`** if hero or final render (medium snapshot frequency rule).

## Cite when gates fire

Every gate violation surfaced to the user must include the handbook chapter + section that defines the rule. Example response when gate #2 (lighting layers) fires:

> "Render blocked by quality gate #2 (lighting layers). The scene has only 1 light source. Per lighting.md §1.2 (citing IES Lighting Handbook 10th ed., Indoor Lighting), interior renders require ambient + accent at minimum. Suggested fix: `setup_interior_lighting_plan(zones=['<zone>'], layers=['ambient','accent'])`. Want me to run that?"

If the user pushes back on the rule, point them to the cited source and let them override with explicit `force=True` + a written reason that gets logged to the audit.
