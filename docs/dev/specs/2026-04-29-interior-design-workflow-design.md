# Interior Design Workflow Design

> Supersedes the generic-MCP scope of `2026-04-29-interior-design-mcp-design.md`. The generic MCP tool layer described there is preserved; this document adds the **Handbook · Skills · Quality Gates · Discovery · Workflow Orchestration** layers that turn the tools into an end-to-end designer-AI workflow.

## Purpose

Build an end-to-end interior design workflow where a non-designer user collaborates with an AI that carries professional design knowledge. The user supplies rough direction and "like / dislike" feedback in plain language; the AI plays the role of a real interior designer — running discovery, locking style, modeling space, lighting, materials, rendering, iterating, and producing construction handoff documents.

## User Profile (Hard Assumption)

Every user of this project is assumed to have **zero formal interior-design knowledge or talent**. The user can:

- Express rough direction ("I want my cafe to feel cozy")
- Recognize "I like this / I don't like this" when shown options
- Describe specific edits in plain language ("move that sofa to the window", "make it warmer")

The user cannot:

- Pick the right Kelvin temperature
- Choose between "Scandinavian" and "Japanese" without help
- Compose a vignette
- Read a section drawing
- Specify PBR roughness values

**Implication**: The design knowledge must live inside the system (handbook + skills + quality gates), not in the user's head. The system must be opinionated by default — it makes good design decisions on the user's behalf and only asks the user when human taste is required.

## Non-Goals

- Not a tool for trained interior designers (they want manual control over every parameter — out of scope)
- Not a one-click generator that hides design decisions from the user (they should still see and approve direction)
- Not a CAD/BIM replacement (we don't generate construction drawings to permit-grade precision)
- Not a vendor for any specific style — the handbook covers a curated set; users can extend
- Not a multi-tenant platform — single-user local toolchain

## Sources & Citation Policy (HARD RULE)

The user has zero design background and is fully delegating design judgment to the AI. If the AI invents rules or numbers, the user has no way to detect bad output. Therefore:

**Every numeric value, range, rule, code reference, or design heuristic in this project must be fetched from an authoritative public source and cited inline.** The implementation must NOT generate handbook content from model training memory.

### Authoritative source list (priority order)

| Domain | Primary sources |
|---|---|
| Chinese building codes | GB 50096-2011 住宅设计规范 · GB 50352-2019 民用建筑设计统一标准 · GB 50034-2013 建筑照明设计标准 · GB 50763-2012 无障碍设计规范 · GB 50016-2014 建筑设计防火规范 |
| International codes | IBC (International Building Code) · ADA Standards · ASHRAE 55 (thermal comfort) |
| Spatial / furniture standards | Neufert Architects' Data (current edition) · Time-Saver Standards for Interior Design · Human Dimension & Interior Space (Panero & Zelnik) |
| Lighting | IES Lighting Handbook (current edition) · CIE 13.3 (color rendering) · GB 50034-2013 |
| Materials / PBR | Disney BSDF paper · Adobe Substance documentation · Blender Manual (current version) · NCS / Pantone color references |
| Camera / architectural photography | ASMP guidelines · Norman McGrath "Photographing Buildings Inside and Out" |
| Acoustics | ASTM E90/E413 · NRC ratings · GB 50118-2010 民用建筑隔声设计规范 |
| Style references | Architectural Digest · Dezeen · Wallpaper* · Architectural Record · AD China · 安邸 · 室内设计师 — for STYLE references, cite the publication or specific named project, not "common knowledge" |

### Citation format

Inline citations in handbook chapters:

```markdown
Living-room sofa-to-coffee-table clearance: 400-460mm
(per Neufert Architects' Data, 5th ed., §"Living Rooms"; corroborated by
Panero & Zelnik 1979 fig. 130).
```

```markdown
Restaurant ambient illuminance: 75 lux average maintained
(per GB 50034-2013 §5.1.5 Table 5.1.5; IES Lighting Handbook 10th ed.
§29 corroborates 50-100 lx for fine dining).
```

### Implementation rules for Slice 1 (handbook authoring)

- Each chapter authoring task MUST start with `WebFetch` / `WebSearch` calls to retrieve the actual standard text or current published guidance. **Do NOT write a chapter from memory and then "look up sources later".**
- Every numeric range, classification, or rule statement in a chapter MUST have an inline citation pointing to a specific section, page, table, or figure of an identifiable source.
- If no authoritative source can be found for a claim the AI wants to make, the chapter MUST state that explicitly ("conventions vary across sources X and Y; defaulting to range Z based on majority practice") rather than presenting a fabricated number.
- Section numbers in standards (GB §, IES §, etc.) MUST be verified against the actual standard before citing. **No fabricated section numbers.**
- For style chapters: cite real named projects or named publications. "Japanese 侘寂 typically uses X" without citation is forbidden; "侘寂 spaces in [Naoto Fukasawa's house, AD Japan 2018] use X" is required.
- The `read_design_handbook` MCP tool returns chapter content **including the citations**, so quality gates and AI explanations always carry source attribution downstream.

### Quality gate citation requirement

Every quality-gate threshold (Section "Quality Gates — 9 Dimensions" below) must reference its source. The defaults shown in this document are placeholders pending citation; the implementation plan will replace each with the cited authoritative value.

## System Architecture

Five layers, top-down:

```
┌────────────────────────────────────────────────────────────┐
│ 👤 USER                                                     │
│    Rough direction · like/dislike · plain-language edits    │
├────────────────────────────────────────────────────────────┤
│ 🤖 AI AGENT (γ checkpoint-hybrid mode)                      │
│    Free conversation · silent phase tracking · auto snap   │
├──────────────────────┬────────────────┬────────────────────┤
│ 📖 HANDBOOK          │ 🧠 SKILLS      │ 🔧 MCP TOOLS        │
│ docs/handbook/       │ .claude/skills/│ blender-mcp +       │
│ 13 markdown chapters │ 5 trigger-     │ ~25 design tools    │
│ source of truth      │ based skills   │                     │
├──────────────────────┴────────────────┴────────────────────┤
│ 🛡️ QUALITY GATES (9 dim) │ 📐 PROJECT STATE                 │
│ refuse / warn / inform   │ .blend + taste-profile + log    │
├────────────────────────────────────────────────────────────┤
│ ⏩ WORKFLOW · 11 phases · 4 loop levels · F version log     │
└────────────────────────────────────────────────────────────┘
```

### Layer responsibilities

- **Handbook** — markdown source of truth for all design knowledge. Edited by humans. Versioned in git.
- **Claude Skills** — auto-loaded by trigger phrases. Each skill points to the handbook chapters it needs and instructs the AI on how to apply them.
- **MCP Tools** — the AI's hands. Includes the existing blender-mcp fork (~100 low-level tools) plus ~25 new design-specific tools.
- **Quality Gates** — block / warn / inform on 9 dimensions before render or export. Cite handbook chapters when triggering.
- **Project State** — a single `.blend` file per project (multi-collection for multi-space) plus sidecar JSON files (taste-profile, version-log) and a `snapshots/` directory.

## Workflow — 11 Phases

```
0. Discovery (questionnaire) → taste-profile.json
1. Survey / Plan import       → calibrated reference plane
2. Direction + AI image gen   → 3-5 candidate moodboards
2.5 Moodboard lock            → final 3 anchor images + palette
3. Floor plan in Blender      → measured walls, openings, rooms
4. 3D Scene                   → blockout + furniture placement
4.5 Material / SKU selection  → PBR finishes + procurement list
4.6 Lighting design           → layered fixtures, Kelvin/Lux
5. Render & iterate (主战场)   → tweaks via plain-language
6. Final render set           → hero shots, plan, elevation, detail
6.5 Construction docs         → dimensioned drawings + BoM + schedule
```

Phases are advisory boundaries, not gates. The AI tracks the current phase silently for snapshot frequency and quality-gate strictness, but the user is never blocked from skipping ahead or asking cross-phase edits.

## Loop Architecture

Four levels by cost. Each level has a different default behavior in γ mode:

| Level | Trigger | Default action | Cost |
|---|---|---|---|
| **L1** Tweak | within Stage 5: render-modify-render | silent execute | minutes |
| **L2** Material/light swap | back to 4.5 / 4.6 | silent execute | half hour |
| **L3** Layout change | back to 3 / 4 | execute + auto-snapshot prior state | hours |
| **L4** Style redo | back to 2.5 | **prompt user**: branch / overwrite / cancel | a day+ |

Versions branched at L4 are saved to `snapshots/` with a label (e.g. `moodboard-v2-japanese-pivot`). The version log records every L3+ transition with a one-line "why".

## Interaction Model — γ Checkpoint Hybrid

Default behavior:

- AI converses freely; no explicit phase prompts
- Plain-language edits route directly to MCP tools
- Snapshot frequency: **medium** — at phase completion + when user says "looks good"
- L1/L2 loops are silent; L3 records a log entry; L4 surfaces a 3-choice prompt (branch / overwrite / cancel)

Snapshot contents per checkpoint:

- `.blend` file copy
- taste-profile.json
- version-log.json (with current entry)
- a thumbnail render if available

## Handbook

Location: `docs/handbook/`

13 chapters:

| # | Chapter | Content |
|---|---|---|
| 1 | `discovery.md` | 5-type question bank + scoring algorithm + taste-profile schema |
| 2 | `spatial.md` | Clearances, circulation widths, furniture spacing, eye level, sight lines |
| 3 | `materials.md` | 60-30-10 color rule, PBR best practices, material adjacency, color theory basics |
| 4 | `lighting.md` | Layered lighting, Kelvin by space type, Lux targets, fixture spacing |
| 5 | `camera.md` | Architectural lens (24-35mm), eye height, vertical correction, composition templates |
| 6 | `styling.md` | Vignette construction, prop triangles, scale variation, negative space, prop density |
| 7 | `furniture.md` | Furniture typology (sofa types, dining table sizing, bed standards) + when-to-use |
| 8 | `acoustics.md` | Absorption coefficients, fabric placement, key surfaces (mostly commercial) |
| 9 | `render-output.md` | View set per project type, exposure bracketing, AgX/Filmic, post-processing |
| 10 | `codes.md` | China GB-T summaries, accessibility, fire egress (commercial) |
| 11 | `project-types.md` | Multi-space organization rules per project type |
| 12 | `styles/*.md` | One file per style (v1: 18 files) |
| 13 | `space-types/*.md` | One file per space type (v1: 8 files) |

### v1 Style Library (18)

**Residential (10)**: 现代简约 · 北欧 · 日式侘寂 · 新中式 · 法式奶油 · 极简 Muji · 美式经典 · 地中海 · 轻奢 Quiet-Luxury · 北欧中古 Mid-century

**Commercial (8)**: Speakeasy/酒吧 · 工业 Loft · 网红咖啡 · 日式茶咖 · 国风茶馆 · Boutique 零售 · 现代中餐 · 联合办公

Each `styles/<name>.md` includes:

- **Anchor description** — 2-3 sentences capturing the feeling
- **Color palette** — 60-30-10 hex values
- **Material vocabulary** — which materials are in / out
- **Lighting profile** — Kelvin range + layer mix
- **Camera bias** — preferred lens / framing
- **Prop vocabulary** — what to include / avoid
- **Reference images** — 3-5 anchor images (links or local thumbs)
- **Common mistakes** — what makes the style fall apart

### v1 Space-Type Library (8)

客厅 · 卧室 · 厨房+餐厅 · 卫浴 · 咖啡馆/lounge · 零售小店 · 餐厅 · 小型办公

Each `space-types/<name>.md` includes:

- Typical dimensions / area ranges
- Required clearances and circulation
- Furniture inventory (must-have, common, optional)
- Lighting layer recipe specific to the space
- Camera view set recommendations
- Cross-references to applicable codes

## Claude Skills (5)

Each skill is a markdown file in `.claude/skills/` with frontmatter (name, description, trigger phrases) and a body that points to handbook chapters + provides AI instructions.

| Skill | Trigger | Loads handbook | Calls MCP |
|---|---|---|---|
| `interior-discovery-intake` | "start a new project", "begin design", project init | discovery.md, project-types.md | run_discovery_questionnaire, create_interior_project |
| `interior-style-locking` | "moodboard", "lock the style", "I want X feel" | styles/*, materials.md, codes.md | generate images, search references, write taste-profile |
| `interior-plain-language-edit` | edit verbs in user message ("move", "change", "make it warmer", "swap") | spatial.md, materials.md, lighting.md, styling.md | object_info, transform, apply_finish, lighting tweaks |
| `interior-render-direction` | "render", "make a hero shot", "show me the result" | camera.md, render-output.md, lighting.md | camera_set, audit, render_view_set, version_snapshot |
| `interior-construction-handoff` | "施工图", "construction docs", "BoM", "ready to ship" | spatial.md, codes.md, render-output.md | export_construction, finish_schedule, audit |

Each skill explicitly instructs the AI to **cite the handbook chapter** when explaining decisions or quality-gate violations to the user, e.g. "I'm switching the lighting to 2400K because lighting.md §2 specifies speakeasy spaces should be 2200-2700K."

## MCP Tools (~25 new + ~100 existing fork tools)

New tools group by phase:

**Phase 0 (Discovery)**
- `run_discovery_questionnaire(space_type, depth, free_input_allowed)` → returns first batch of questions
- `submit_questionnaire_answers(session_id, answers)` → returns next batch or final taste-profile
- `read_taste_profile(project)` → current taste profile
- `update_taste_profile(project, override)` → manual override

**Phase 1-3 (Survey, Plan, Floor)**
- `create_interior_project(name, project_type, root_dir)` (extends existing)
- `import_plan_reference` (existing, from generic spec)
- `calibrate_plan_reference` (existing)
- `create_floorplan_linework` (existing)
- `extrude_floorplan_shell` (existing)
- `create_interior_zones` (existing) — extended to multi-space
- `import_lidar_scan(filepath)` — handles iPhone LiDAR FBX/GLB

**Phase 2-2.5 (Direction, Moodboard)**
- `generate_moodboard_candidates(taste_profile, n)` → calls existing image-gen tools with style-loaded prompts
- `lock_moodboard(project, anchor_image_paths, palette)` → writes taste-profile.json final fields

**Phase 4-4.6 (Scene, Materials, Lighting)**
- `apply_finish` (existing) — extended to read style files
- `setup_interior_lighting_plan` (existing) — extended to read style + space-type
- `place_furniture_from_style(zone, style, density)` → searches Sketchfab by style vocabulary, places + grounds
- `record_sku_purchase(item, url, price, vendor)` → appends to procurement.json
- `extract_sku_from_url(url)` → uses claude-in-chrome to scrape product metadata

**Phase 5-6.5 (Render, Output, Construction)**
- `create_interior_camera_set` (existing)
- `audit_interior_scene` (existing) — extended with 9-dimension gates
- `render_view_set` (existing)
- `export_interior_package` (existing)
- `export_construction_docs(project, formats)` → dimensioned plan/elevation/section + BoM
- `version_snapshot(project, label)` → saves to snapshots/
- `version_restore(project, snapshot_id)` → restore from snapshot
- `version_log_entry(project, level, why)` → records L3/L4 transition

**Cross-cutting**
- `read_design_handbook(chapter, query)` → returns relevant handbook content for runtime AI lookup

All tools return the canonical envelope `{"ok": bool, "data" | "error": ...}` already used by the fork.

## Quality Gates — 9 Dimensions

Severity tiers (γ-mode adapted):

- 🔴 **Hard** — blocks render unless user passes `force=True` to override (one-shot)
- 🟡 **Soft** — warns before render, user presses Enter to continue
- 🔵 **Info** — silently records to audit report

Default levels:

| # | Dimension | Default | Rule |
|---|---|---|---|
| 1 | Materials non-trivial | 🔴 | Every non-temp object has albedo or roughness map |
| 2 | Lighting ≥ 2 layers | 🔴 | At least ambient + accent (not just sun/HDRI) |
| 3 | Kelvin in range | 🟡 | All lights have Kelvin metadata within space-type range |
| 4 | Camera params sane | 🔴 | Focal 18-35mm, height 1.4-1.7m, no wall clipping, near plane <0.05m |
| 5 | Color management | 🔴 | View transform = AgX (fallback Filmic). Auto-fix + notify. |
| 6 | Render samples | 🟡 | Cycles ≥ 64 preview / ≥ 512 hero; EEVEE Next ≥ 32 / ≥ 128 |
| 7 | Prop density | 🟡 | ≥ N props/m² (configurable per space-type); strict on hero shots |
| 8 | Scale sanity | 🔴 | Sofa 0.7-1.1m h, doors 1.9-2.4m h, etc. Normalize on import. |
| 9 | Texture packing | 🔵 | Final + construction-docs auto-upgrade to 🔴 |

Strictness modes:
- **Exploration** (Stages 0-4, L1 loops): only 🔴 enforced
- **Hero render** (Stage 5 final, Stage 6): all tiers active
- **Construction handoff** (Stage 6.5): all tiers + dimension #9 upgraded to 🔴

Override path: `--force` flag on the rendering tool with a required `reason` string written to the audit log.

When a gate fires, the response cites the handbook chapter and offers a one-call fix where possible:

```json
{
  "ok": false,
  "error": {
    "code": "QUALITY_GATE",
    "gate": "lighting_layers",
    "hint": "Scene has only 1 light layer. lighting.md §1.2 requires ambient + accent minimum for interior renders.",
    "suggested_fix": "setup_interior_lighting_plan(zones=['living'], layers=['ambient','accent'])",
    "detail": "..."
  }
}
```

## Discovery Questionnaire — Detailed Spec

Default depth: **Deep (25-30 questions, ~20 minutes)**. Adaptive escape valve: if first 12 answers strongly converge (top style match >0.75), AI offers to skip remaining questions.

### Question types (5)

Each question can have any combination of:
- Single-select preset options
- Multi-select preset options (default for taste questions)
- Free-text input field (always available as fallback)

| Type | Purpose | Example |
|---|---|---|
| 1. Direct | Hard constraints | "Who uses this space? [me / family / customers / coworkers / free-text]" |
| 2. Projective | Subconscious feeling | "Walking in, what do you want to feel in the first second? [warm-hugged / orderly / curious / relaxed / energized / professional / free-text]" |
| 3. Metaphor | Cultural shortcut to style | "If this space were a movie, which? [Grand Budapest / Crouching Tiger / Interstellar / 1900 / Kikujiro / free-text]" |
| 4. Sensory | Body memory > visual memory | "Pick 3 textures you want to touch: [terracotta / linen / leather / velvet / polished marble / rough wood / brushed brass / concrete / fur rug / free-text]" |
| 5. Visual A/B | Triangulate style axes | "12 paired comparisons (warm/cool, sparse/full, wood/stone, high-contrast/soft, aged/new, symmetric/asymmetric, etc.)" |

### Trigger timing — all four enabled

- **A. On project start** — required before entering Moodboard phase
- **B. Skippable** — user can declare an explicit style ("I want Japanese 侘寂") and skip with explicit-preference flag
- **C. Per-space mini** — when entering a new space, ask 2-3 space-specific questions ("What's the last thing you want to see before sleep?" for bedroom)
- **D. Conflict-triggered** — when user statements conflict ("Japanese" then "more gold shine"), AI fires a 1-2 question clarifier mid-conversation

### Mid-questionnaire feedback

Around question 12, AI surfaces inferred style hypothesis:

> "Based on your answers so far, you seem to lean toward 日式侘寂 (78%) and 北欧 (62%). Does that feel right, or am I missing something? [Yes / Sort of, but X / No, redo]"

This catches misaligned questionnaires early instead of finishing 30 questions in the wrong direction.

### Output: taste-profile.json

```json
{
  "version": 1,
  "created_at": "ISO timestamp",
  "project": "name",
  "depth": "deep",
  "explicit_style": null,
  "feeling_anchors": ["温暖", "想发呆", "安静"],
  "style_axes": {
    "warmth": 0.85,
    "complexity": 0.30,
    "natural_vs_polished": 0.70,
    "contrast": 0.40,
    "aged_vs_new": 0.60,
    "symmetric_vs_organic": 0.55
  },
  "material_pull": ["木", "亚麻", "粗陶"],
  "material_avoid": ["镀铬", "亮面瓷砖"],
  "style_match": {
    "日式侘寂": 0.78,
    "北欧": 0.62,
    "新中式": 0.41
  },
  "recommended_style": "日式侘寂",
  "free_text_notes": "用户提到喜欢京都旅行回忆..."
}
```

Downstream tools and skills consume this JSON as input.

## Project State

Layout per project:

```
<project-root>/
├── <project>.blend                 # main Blender file (multi-collection)
├── taste-profile.json              # Discovery output
├── version-log.json                # L3/L4 transition log
├── procurement.json                # SKU list (4.5 output)
├── snapshots/
│   ├── 0-discovery-complete/
│   ├── 2.5-moodboard-v1/
│   ├── 2.5-moodboard-v2-pivot-japanese/
│   ├── 4-shell-complete/
│   └── ...each contains: .blend + jsons + thumb.png
└── exports/
    ├── renders/{stage5,stage6}/
    └── construction/
```

Blender collections inside `<project>.blend`:

```
00_REFERENCES/    01_PLAN/        02_SHELL/       03_ZONES/
04_FINISHES/      05_FIXTURES/    06_LIGHTING/    07_CAMERAS/
08_RENDER_OUT/    09_EXPORT/      90_VARIANTS/

Each space (multi-space project) gets a sub-collection prefix:
  03_ZONES/Living/
  03_ZONES/Bedroom/
  03_ZONES/Kitchen/
```

## Implementation Slices

### Slice 1 — Knowledge Layer (handbook + skills + read tool)

Deliverables:
- 13 handbook chapters drafted (markdown only, no code) — **each chapter sourced via `WebFetch` from authoritative standards (GB, IES, Neufert, Substance, etc.) with inline citations on every numeric value or rule. No chapter may be written from training memory.**
- 18 style files — each citing real named projects or named design publications, never generic "this style uses X" prose
- 8 space-type files — each citing the relevant code section (GB / IBC / Neufert) for clearances and dimensions
- 5 Claude skills with trigger phrases
- 1 new MCP tool: `read_design_handbook(chapter, query)` returning chapter content **with citations preserved**
- Tests for skill triggering and chapter retrieval

**Slice 1 acceptance gate**: a random sample of 10 numeric claims pulled from the handbook can each be traced to a specific cited source section / page / table.

No Blender behavior changes. Goal: an AI talking through the system can already answer design questions using handbook content (with sources) and route them to the right (still-existing) MCP tools.

### Slice 2 — Discovery + Project Skeleton

Deliverables:
- `run_discovery_questionnaire` (Deep + free-input + multi-select + 4-trigger)
- `submit_questionnaire_answers` with mid-feedback at question 12
- `update_taste_profile` / `read_taste_profile`
- `create_interior_project` extended to write taste-profile.json + multi-space scaffolding
- `version_snapshot`, `version_restore`, `version_log_entry`
- `interior-discovery-intake` skill wired up
- Validation: run a full discovery questionnaire end-to-end on a sample project

### Slice 3 — Plan to Render with Quality Gates

Deliverables:
- Existing generic-spec tools (linework, shell, finishes, lighting, cameras, render) wired to handbook (via skills loading style + space-type chapters)
- `audit_interior_scene` extended with 9-dimension quality gates
- `interior-plain-language-edit` skill (move, swap, change verbs → MCP routing)
- `interior-render-direction` skill
- Strictness modes (exploration / hero / handoff)
- `place_furniture_from_style` (style-aware Sketchfab search + placement)
- Validation: take an imported floor plan + completed discovery → produce a hero render that passes all 9 gates

### Slice 4 — Construction Handoff (out of v1 scope but planned)

Deliverables:
- `export_construction_docs` (dimensioned plan, elevation, section)
- `record_sku_purchase` + `extract_sku_from_url` (claude-in-chrome integration)
- BoM generator
- `interior-construction-handoff` skill

### Slice 5 — Style Library Expansion

Add styles beyond the v1 18 (波西米亚, Art Deco, Maximalist, Izakaya, Salon, etc.) based on user demand.

### Slice 6 — PDF Plan Support

PDF page → image conversion for Phase 1 plan import. Optional dependency.

## Acceptance Criteria

The workflow is acceptable when a non-designer user can:

1. Start a new project (residential apartment OR small commercial space).
2. Complete a Discovery questionnaire and see a taste-profile that *feels right* upon mid-feedback.
3. Receive 3-5 AI-generated moodboard candidates that align with the taste-profile, pick one, and lock it.
4. Import a floor plan image and see a calibrated reference + 3D shell.
5. Have AI auto-apply finishes, lighting, and furniture per the locked style — without the user choosing PBR values, Kelvin temperatures, or fixture spacing manually.
6. Render a hero shot that passes all 9 quality gates.
7. Iterate via plain-language commands ("warmer", "less stuff on the table", "swap the rug for something dark") and see the render update.
8. Branch a moodboard variant (L4 loop) without losing the original.
9. Export a final render set + procurement list.
10. Throughout: never see "Kelvin", "PBR", or "焦距" jargon unless they explicitly ask for it. The AI explains decisions in plain language but cites handbook chapter numbers when asked "why".

## Open Questions / Deferred

- **PDF vector extraction** — deferred to Slice 6
- **LiDAR scan auto-walls** — manual overlay only in v1; auto-detection deferred
- **1688/Taobao auto-search** — not feasible without merchant API; v1 uses claude-in-chrome scrape on user-provided URLs
- **Construction-grade dimensioned drawings** — Slice 4; v1 stops at render handoff
- **Multi-language handbook** — v1 is bilingual zh-CN + en headers; full translation deferred
- **Style transfer between projects** — locked-moodboard reuse across projects; deferred

## Relationship to Prior Specs

- `docs/dev/specs/2026-04-29-interior-design-mcp-design.md` — defines the **generic MCP tool layer**. Tools listed there (`create_interior_project`, `import_plan_reference`, `apply_finish`, etc.) remain as-is. This document **extends** that spec with handbook, skills, quality gates, discovery, and workflow orchestration.
- `docs/dev/specs/2026-04-28-blender-mcp-optimization-roadmap.md` — earlier optimization scope; orthogonal to this work.
- `docs/dev/plans/2026-04-29-interior-design-mcp.md` — the implementation plan for the generic MCP layer. A new plan covering Slices 1-3 of this document will be written next.
