---
description: Render the current Atelier project's hero shot. Runs the 9-dimension quality audit first; refuses to render until 🔴 HARD gates pass. Surfaces every gate violation with a handbook citation. Output goes to renders/ with a snapshot recorded.
---

You are producing a rendered shot of the current Blender scene for an Atelier project.

## Required state

Blender connected; addon registered; an active camera in the scene.

## Process

1. **Identify render mode** from user phrasing:
   - "show me", "preview", "quick render" → **exploration** mode (low samples, only 🔴 HARD gates enforced)
   - "render", "hero shot", "make a final" → **hero** mode (high samples, all gates 🔴/🟡/🔵 enforced)
   - "施工图", "construction", "for the contractor" → **construction** mode (gate #9 texture packing upgraded to 🔴)
2. **Load the relevant handbook chapters** — `camera.md`, `render-output.md`, `lighting.md`.
3. **If no camera exists**, run `create_interior_camera_set` per the project type's recommended view set.
4. **Run `audit_interior_quality_native(mode=...)`**.
5. **If any 🔴 HARD finding fires**, surface to the user with the citation, suggest a one-call fix from `suggested_fix`. Do NOT auto-render with `force=True`. Wait for the user to acknowledge or override explicitly.
6. **Once gates pass** (or user explicitly overrode), call `render_image(...)` (or `render_view_set` for multi-view).
7. **For hero or construction renders**, also call `version_snapshot(project_root, label="<phase>-render-<timestamp>")` so the result is in the version log.
8. **Return the preview** to the user (`render_image(return_preview=True)`).

## Cite when gates fire

Every gate violation surfaced to the user must include the handbook chapter + section that defines the rule:

> "Render blocked by quality gate #2 (lighting layers). Scene has only 1 light source. Per lighting.md §1.2 (citing IES Lighting Handbook 10th ed., Indoor Lighting), interior renders require ambient + accent at minimum. Suggested fix: `setup_interior_lighting_plan(zones=['Living'], layers=['ambient','accent'])`. Want me to run that?"

If the user pushes back on the rule, point them to the cited source. They can override with `--force` + a reason; the override is logged to the audit report.
