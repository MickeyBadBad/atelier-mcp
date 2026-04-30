---
name: interior-style-locking
description: Use when the user wants to lock a style direction, generate moodboards, says "moodboard", "lock the style", "I want X feel", "show me ideas", "确定风格", or otherwise establishes the visual direction before 3D modeling.
---

# interior-style-locking

Run the moodboard / style-lock phase: generate 3-5 candidate directions aligned with the existing taste profile, present them, let the user select one, and write the locked palette + material vocabulary into the project's `taste-profile.json`.

## Required reading

Before generating images, call:

1. `read_design_handbook(query="<inferred style name from taste profile>")` — load the matching `styles/*.md` chapter.
2. `read_design_handbook(chapter="materials")` — color rules, palette construction.
3. `read_design_handbook(chapter="codes")` — for any commercial project, glance at constraints that limit material choices (fire rating, accessibility).

If the inferred style does not yet have a `styles/<name>.md` chapter (Slice 1 ships only a few example styles; the rest land in Slice 5), tell the user explicitly: "the handbook entry for this style isn't written yet, so I'll cite cross-style rules from materials.md and lighting.md, and we should treat the result as a draft until the style chapter lands."

## Process

1. Read the project's existing `taste-profile.json`. If missing, redirect the user to `interior-discovery-intake`.
2. Construct image-gen prompts using the style chapter's vocabulary (palette hex values, material list, lighting profile). **Quote the chapter directly** — do not paraphrase.
3. Use existing image-gen MCP tools (`generate_image_codex`, `generate_image_openai`, etc.) to produce 3-5 candidates per major direction.
4. Present candidates to the user; let them pick one or ask for more iterations.
5. On selection, write back into `taste-profile.json`:
   - `locked_style` — canonical name from the styles chapter
   - `locked_palette` — 60-30-10 hex values (per `materials.md`)
   - `locked_material_vocab` — in/out lists (from the style chapter)
   - `locked_anchor_images` — file paths to selected candidates
6. Snapshot project state (call `version_snapshot` when available in Slice 2; in Slice 1, copy the `.blend` + sidecar JSONs into `snapshots/2.5-moodboard-v<N>/` manually).

## Cite the handbook

Every claim about "Scandinavian uses light wood" must cite the style chapter, e.g. "(per styles/scandinavian.md, citing Norm Architects feature in Dezeen 2019)". Never speak generically about a style. If the handbook is silent, say so.
