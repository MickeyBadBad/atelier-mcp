---
name: interior-discovery-intake
description: Use when the user begins a new interior-design project, says "start a new design", "begin design", "I want to redesign my X", "新项目", "我想装修我的", or invokes any project-creation language. Runs the discovery questionnaire (per docs/handbook/discovery.md) to extract a taste profile before any modeling or moodboard work.
---

# interior-discovery-intake

You have been invoked because the user is about to start a new interior-design project. Your job is to run the Discovery questionnaire and produce a `taste-profile.json` before any 3D work begins.

## Required reading

Before asking the first question, call:

1. `read_design_handbook(chapter="discovery")` — questionnaire mechanics, the 5 question types, the scoring algorithm.
2. `read_design_handbook(chapter="project-types")` — project-type taxonomy, required spaces.

If either chapter cannot be loaded, surface the error to the user and stop. Do not invent questionnaire content from training memory — the handbook is the source of truth.

## Process

1. **Confirm project type** with the user (residential apartment / detached house / cafe-lounge / restaurant / retail / office / other) using a Type-1 direct question.
2. Run the **Deep questionnaire** (25-30 questions) per the schema in `discovery.md`.
3. Use **all 5 question types** in roughly the proportions specified in `discovery.md`.
4. **Always include a free-input option** as a fallback for every question — taste questions get a "或者：自己描述" choice.
5. **Multi-select where appropriate** for taste questions — a single answer often misrepresents real preferences.
6. **Around question 12**, surface a mid-questionnaire inferred-style hypothesis. Ask the user to confirm or correct before continuing.
7. **Trigger conflict-clarifier mid-stream** if user's later answers contradict earlier ones (per `discovery.md` trigger D).
8. After the final question, write `taste-profile.json` to the project root. (When the `update_taste_profile` MCP tool ships in Slice 2, call it; in Slice 1 just write the file directly.)

## Skip path

If the user explicitly declares a known style ("I want Japanese 侘寂"), set `explicit_style` in the profile, capture lifestyle / occupancy basics with 5-7 short Type-1 questions only, and skip the rest. Per `discovery.md` trigger B (skippable).

## Cite the handbook

When explaining why you ask a particular question, cite `discovery.md` and the relevant question-type theory. For example:

> "I'm asking how you want to FEEL when you enter (not what style you like) because projective questions extract latent preferences from non-experts more reliably than direct style questions — see discovery.md citing Norman 2013 *The Design of Everyday Things*."

Do not invent rationale. If the handbook doesn't cover a specific question's rationale, default to the type-level rationale (e.g. "type-2 projective question, see discovery.md §Type-2").
