---
description: Lock the style direction for an Atelier project. Generates moodboard candidates from the taste-profile, lets the user pick one, writes the locked palette + material vocabulary back into taste-profile.json, auto-snapshots before writing.
---

You are locking the style direction for an existing Atelier project.

## Required state

The project must have a `taste-profile.json` with a `recommended_style` field. If missing, redirect the user to `/atelier-start` first.

## Process

1. **Read the taste profile** — `read_taste_profile_tool(project_root=...)`.
2. **Confirm the style slug** with the user. Default = `recommended_style`. If the user wants a different style from the 19 available, accept the override.
3. **Load the style chapter** — `read_design_handbook(chapter=f"styles/{slug}")`. This grounds every claim about the style in the handbook citation.
4. **Generate moodboard prompts** — `generate_moodboard_candidates(project_root, style_slug, space_type, n=4)`. This returns N image-gen prompts citing the style's palette, materials, Kelvin range, and reference projects.
5. **Run the prompts through an image-gen tool** — pick the cheapest available: `generate_image_codex` (free with ChatGPT subscription) or `generate_image_openai` (paid). Save each candidate as `moodboards/<slug>/candidate_<n>.png`.
6. **Show the candidates to the user**, ask which one feels right. Allow them to ask for more iterations if none of the 4 land.
7. **Lock** — `lock_moodboard(project_root, style_slug, selected_image_paths=[...])`. This writes the four `locked_*` fields into `taste-profile.json` and auto-snapshots the project before writing.

## Cite the handbook

Every claim about the style ("Scandinavian uses light wood") must cite the styles chapter, e.g. "(per styles/scandinavian.md, citing Norm Architects feature in Dezeen 2019)". If the chapter is silent, say so — never invent style attributes.
