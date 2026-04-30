# Atelier — Overview

A 5-minute read for anyone trying to understand what Atelier is and how its parts fit together.

## What Atelier is

Atelier is a complete interior-design workflow assistant. It assumes the user has zero formal design knowledge or talent — the AI carries the design judgment, the user supplies rough direction and "I like this / I don't like this" feedback. Atelier produces design-quality outputs (renders, dimensioned plans, contractor-ready BoMs) that hold up against real-world execution.

## What it is *not*

- Not a tool for trained designers who want manual control over every parameter
- Not a one-click generator that hides the design decisions
- Not a CAD/BIM replacement (the construction-doc output is for visual handoff, not permit-grade engineering)
- Not a multi-tenant platform (single-user local toolchain)

## The five layers

```
┌─────────────────────────────────────────────────────────────────────┐
│ 👤 You — rough direction · "I like this / I don't" · plain-language│
│      "make the cafe feel cozy", "swap the sofa", "make it warmer"   │
├─────────────────────────────────────────────────────────────────────┤
│ 🧠 The Designer (AI) — runs discovery, locks style, makes decisions │
│      Trained on the handbook; cites it before applying any rule.    │
├─────────────────────────────────────────────────────────────────────┤
│ 📖 The Handbook (knowledge)  · 🧠 Skills (how to use it)           │
│  39 cited chapters             5 trigger-based Claude skills        │
│  GB/IES/Neufert/Disney BSDF    discovery, style-lock, edit, render, │
│  + 19 styles + 8 space types   handoff                              │
├─────────────────────────────────────────────────────────────────────┤
│ 🛡️ Quality Gates · 📐 Project State · 🛒 Procurement              │
│  9 dimensions     multi-space    SKU tracking + BoM generator       │
│  refuse / warn /  .blend +       1688/Taobao/JD/Sketchfab vendors   │
│  inform           snapshots/                                        │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 Atelier CLI · 🔌 MCP Server · 🪟 Blender addon                  │
│  no AI client    Claude/Cursor/  Native socket commands for         │
│  needed          Codex via MCP   audit, scaffold, snapshot          │
└─────────────────────────────────────────────────────────────────────┘
```

## How a session typically flows

1. **Discovery** (~20 min, 25 questions across 5 types: direct, projective, metaphor, sensory, paired-visual). Output: a `taste-profile.json` capturing your style axes (warmth, complexity, natural-vs-polished, contrast, aged-vs-new, symmetric-vs-organic) and matched against the 19 published style chapters.
2. **Direction & moodboard**. The AI generates 3-5 candidate moodboard images grounded in the matched style chapter (palette hex, materials, Kelvin, camera bias). You pick one. Atelier locks the palette + material vocab.
3. **Floor plan + 3D scene**. The AI imports your measured plan or LiDAR scan, scaffolds the project in Blender (11 standard collections + per-space sub-collections), applies finishes, layered lighting, and style-aware furniture from Sketchfab.
4. **Iterate via plain language**. "Swap the sofa for a tufted one in walnut", "the lighting feels cold", "more plants on the bookshelf". Atelier classifies the edit by cost (L1 → L4 loops) and auto-snapshots before any expensive change.
5. **Render with audit**. Before any "hero" render, Atelier runs the 9-dimension quality audit. If a gate fires (e.g. only one light layer; not AgX color management; sofa scaled to 0.6m wide), the AI surfaces the citation and offers a one-call fix. No render until the gates pass.
6. **Handoff**. Atelier emits a markdown / CSV BoM with vendor URLs + prices in RMB, a finish schedule, an audit report, and (Slice 7, queued) dimensioned plan + elevation PDFs.

## Where to read more

- **The Handbook** — `docs/handbook/` — the design knowledge itself. 39 chapters, all cited. Read [`codes.md`](handbook/codes.md), [`lighting.md`](handbook/lighting.md), [`materials.md`](handbook/materials.md) to see the citation policy in action.
- **Architecture** — [`ARCHITECTURE.md`](ARCHITECTURE.md) — for developers / extenders. Code layout, module responsibilities, how the addon talks to the MCP server.
- **Workflow design** — `docs/dev/specs/2026-04-29-interior-design-workflow-design.md` — the full design spec (505 lines) covering every component.
- **Test plan** — `docs/dev/specs/2026-04-30-test-plan.md` — 4-layer verification plan from pure-Python tests up to full live workflow.

## Source policy

A hard rule: every numeric value, range, rule, or code reference in this project must be fetched from an authoritative public source and cited inline. The user has zero design background and is fully delegating design judgment to the AI; if the AI invents rules, the user has no way to detect bad output. Fabricated citations are worse than no citations.

Authoritative sources used: GB 50096-2011, GB 50034-2013, GB 50352-2019, GB 50763-2012, GB 50016-2014, GB 50118-2010, IBC 2021, ADA 2010, ISO 3382-2:2008, ASHRAE 55, Neufert *Architects' Data*, Panero & Zelnik *Human Dimension & Interior Space*, Time-Saver Standards, IES Lighting Handbook, CIE 13.3 / 015, Disney BSDF (Burley 2012), Adobe Substance PBR Guide, Blender Manual, NKBA, BIFMA, Beranek *Concert Halls and Opera Houses*, plus named publications (Architectural Digest, Dezeen, Wallpaper*, AD China, 安邸, Dwell) and named designers' published projects.
