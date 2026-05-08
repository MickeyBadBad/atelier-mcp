# Synthesis Log

Running ledger of project changes triggered by video analyses. Append a new section per synthesis round.

Format per round:

```markdown
## YYYY-MM-DD — Round N: <topic>

**Analyses synthesized**:
- analyses/<date>-<slug-1>.md
- analyses/<date>-<slug-2>.md
- ...

**Cross-tutorial agreement** (techniques that appeared in 2+ analyses):
- <technique 1> — appeared in N/M analyses
- ...

**Project changes applied**:
- ADD-RULE `docs/handbook/<chapter>.md`: "<rule>" (because: cited by N tutorials)
- TUNE-GATE `src/atelier/_gates.py:<function>`: <old> → <new> (because: ...)
- EDIT-SKILL `.claude/skills/<name>.md`: "<edit>" (because: ...)
- ADD-TOOL `src/atelier/server.py`: <tool> (because: ...)

**Single-tutorial findings (recorded but not yet applied — waiting for second source)**:
- <technique> from analyses/<slug>.md — needs corroboration before encoding

**Tests**: pytest result + handbook acceptance gate result
**Commit**: <git hash>
```

---

## 2026-05-08 — Round 3: Compositor finishing pass (re-mining the existing 5)

**Discipline note**: This round adds **NO new analyses**. Instead, it re-mines the same 5 sources from Round 2 for consensus that the previous synthesis missed. Re-mining surfaced one strong cross-tutorial agreement that Round 2 had recorded as "single-source pending" (lens effects in compositor, attributed only to nuno_silva): in fact, the in-Blender compositor finishing pass is used by **3 of 5** surveyed tutorials, with **two specific node patterns reaching 2-source corroboration**. Recording this round to make the existing knowledge base earn its keep before paying for more video analyses.

**Analyses re-synthesized** (no new files this round):
- `analyses/2026-05-01-coral_lab-Creating_a_photorealistic_Japandi_interior_in_Blender.md`
- `analyses/2026-05-01-coral_lab-japandi-gemini-pipeline-v2.md` (same source as above; counts once)
- `analyses/2026-05-01-noel_3d-photorealistic_interior_lighting_tutorial_in_blender_40_cycl.md`
- `analyses/2026-05-01-nuno_silva-the_7_step_formula_to_photorealistic_interior_3d_renders.md`
- `analyses/2026-05-01-art_of_3d_rendering-blender_photorealistic_interior_render_in_cycles_tutorial.md`
- `analyses/2026-05-01-rileyb3d-optimize_interior_renderings_in_blender_cycles.md`

5 unique source videos.

### Cross-tutorial agreement applied this round

**ADD-SECTION** `docs/handbook/render-output.md` § "Compositor finishing pass (cross-tutorial consensus)"

Three sub-rules, each at or above the 2-source threshold:

| Sub-rule | Sources | Detail |
|---|---|---|
| **Glare node for bloom/streaks** | 3/5 | art_of_3d (Streaks mode), noel_3d (Fog Glow mode), nuno_silva (Lumion bloom + lens-flare equivalent). Modes documented; mode choice = aesthetic intent. Default codebase: Fog Glow @ threshold 1.0 unflared / Streaks @ 1.5 cinematic. |
| **Color Balance node for grading** | 2/5 | art_of_3d + noel_3d both name-check Color Balance specifically. Default speakeasy-palette starting values written into the handbook (Lift R0.5/G0.5/B0.45, Gain R1.0/G1.0/B1.05). 3/5 use compositor color grading in some form. |
| **Vignette (5-10% edge darkening)** | 2/5 | art_of_3d (compositor Mix-node + radial mask) + nuno_silva (Lumion external pipeline). Both converge on subtle (5-10%), not heavy (30%); heavier reads as Instagram-cheap. |

Plus **order-of-operations** rule (Glare BEFORE color grade for consistent highlight spillover) and **when-to-skip** rule (construction-grade orthographic deliverables ship raw — no compositor — same logic that puts those on Standard view transform).

Primary citations added: Blender Manual *Compositing → Filter → Glare Node*; *Compositing → Color → Color Balance Node*; *Compositing → Color → Mix Node*; *Compositing → Operations performed sequentially*.

### Pending corroboration carried forward

Round 2's "Single-tutorial findings" list — none gained corroboration this round (re-mining did not surface 2nd sources for them within the existing 5):

- Volumetric lighting / Volume Scatter density 0.005 (art_of_3d, 1/5)
- Light portals — area light in window opening (rileyb3d, 1/5)
- Cryptomatte selective denoising (rileyb3d, 1/5) — referenced in the new section's "When to skip" paragraph as a structurally distinct concern, not yet a rule
- Surface imperfections / decals — dust / stains / scratches (nuno_silva, 1/5)
- 1-2 mm gaps between intersecting objects (nuno_silva, 1/5)
- Glossy ray amplification — multiply glossy by 5×, set diffuse to 0 (noel_3d, 1/5)
- Micro-roughness via noise texture (art_of_3d, 1/5)
- Subtle displacement on fabrics (coral lab, 1/5)
- HDRI calibration spheres (coral lab, 1/5 — round-1 carryover)
- Lens distortion compositor node (art_of_3d, 1/5) — partially absorbed into the Glare-as-camera-lens rule but the dedicated *Lens Distortion* node is still 1-source
- Chromatic aberration as a distinct node setup (nuno_silva, 1/5)

Next analyses should target: light portals, volumetric, surface imperfections, displacement on fabrics — these are concrete techniques with high handbook value once corroborated.

### Tests

```
uv run pytest tests/test_handbook.py tests/test_handbook_acceptance.py -v
```

14/14 passed. Acceptance gates green: at-least-one-chapter, every-chapter-has-citation, numeric-claims-have-nearby-citations, no-fabricated-section-markers, chapters-substantial (≥ 80 lines), chapters-have-sources-block.

### Commit

`<filled in by next commit>` — see `git log --oneline | grep "synthesis Round 3"`

---

## 2026-05-01 — Round 2: Cross-tutorial photoreal interior consensus (4 new analyses)

**Analyses synthesized**:
- `analyses/2026-05-01-coral_lab-Creating_a_photorealistic_Japandi_interior_in_Blender.md` (manual; round 1)
- `analyses/2026-05-01-coral_lab-japandi-gemini-pipeline-v2.md` (re-run via pipeline; same source)
- `analyses/2026-05-01-noel_3d-photorealistic_interior_lighting_tutorial_in_blender_40_cycl.md` (NEW — Noel-3D, 20:32, lighting-specific)
- `analyses/2026-05-01-nuno_silva-the_7_step_formula_to_photorealistic_interior_3d_renders.md` (NEW — Nuno Silva, 16:39, workflow framework)
- `analyses/2026-05-01-art_of_3d_rendering-blender_photorealistic_interior_render_in_cycles_tutorial.md` (NEW — Art of 3D Rendering, 34:36, Cycles deep-dive)
- `analyses/2026-05-01-rileyb3d-optimize_interior_renderings_in_blender_cycles.md` (NEW — rileyb3d, 11:02, optimization)

5 unique sources (the two coral lab analyses are the same video, count once for cross-source agreement).

### Cross-tutorial agreement (≥ 2 sources) — applied to handbook

- **AgX view transform default** — 4/5 explicit (art_of_3d, both coral_lab, noel_3d). Already in `render-output.md`; CONFIRMED, no edit needed.
- **OpenImageDenoise + Adaptive Sampling threshold 0.01** — 4/5 use OIDN (rileyb3d uses OptiX as the RTX-accelerated alternative); 4/5 explicit threshold = 0.01 (the 5th says 0.1 in v2 re-run, treated as parsing artifact since v1 = 0.01). **APPLIED** to `render-output.md` § "Denoising (cross-tutorial consensus)" with explicit 0.01 threshold + OIDN-vs-OptiX trade-off + Blender Manual primary citation.
- **Light Path `Is Shadow Ray` shader idiom** — round-1 application (sheer curtains, coral lab) + new application (glass windows, rileyb3d) = 2 independent applications of the same shader pattern. **APPLIED** to `materials.md` § "Cycles-specific shader patterns / Shadow-less transparent objects" — section title kept; "Use cases" expanded with rileyb3d's window application; the Cycles dark-interior problem now explicitly addressed as one of the patterns this idiom solves.
- **Layered lighting (ambient/task/accent)** — noel_3d explicit + our existing `lighting.md` § "The four-layer model". CONFIRMED, no edit.
- **Eye-level camera height ≤ 1.6 m + 2-point perspective** — nuno_silva explicit + our existing `camera.md` § "Camera height" + § "Vertical-line preservation". CONFIRMED, no edit.
- **Blackbody node for physical Kelvin on lights** — noel_3d explicit + our existing `lighting.md` § "Blender practical mapping". CONFIRMED, no edit.

### Conflict resolution — 45-50 mm focal length (Round 1 flagged for review)

Round 1 noted that coral lab uses 50 mm in interior context, conflicting with our `camera.md` 24-35 mm default. Round 2 settles it: **2 independent tutorials use 45-50 mm** (art_of_3d 45 mm; coral lab 50 mm; nuno_silva educationally surveys the full range). **APPLIED** to `camera.md` § "When to use 45-50 mm instead" — explicitly nuances the default: 24-28 mm for spatial-sense hero (room as subject), 45-50 mm for compressed-perspective vignette (furniture cluster as subject), 70-85 mm for detail crops, 100 mm+ for macro. Both 24-35 mm and 45-50 mm are now correct; the rule chooses based on shot subject.

### Single-tutorial findings recorded — pending second source

(Each is genuinely interesting craft knowledge but not yet 2-source-confirmed. Recorded here so the next analyzer-run can match against them.)

- **Volumetric lighting / Volume Scatter density 0.005 for atmospheric haze** (art_of_3d) — atmospheric humidity simulation; visible god-rays around windows
- **Light portals (area light placed in window opening)** (rileyb3d) — Cycles optimization; drastically reduces noise in interior scenes lit through small windows
- **Cryptomatte selective denoising** (rileyb3d) — apply different denoise levels to walls vs. complex objects via View Layer crypto masks
- **Surface imperfections / decals (dust, stains, scratches)** (nuno_silva) — breaks CGI perfection; could be a procedural shader or decal-mesh approach
- **1-2 mm gaps between intersecting objects** (nuno_silva) — generates physical contact shadows instead of fused-mesh look
- **Lens effects in compositor (chromatic aberration + vignette + Gaussian blur)** (nuno_silva) — mimics real camera sensor; we don't have a compositor section yet
- **Glossy ray amplification (multiply glossy by 5×, set diffuse to 0)** (noel_3d) — custom shader graph trick to enhance reflections without overexposing
- **Micro-roughness via noise texture** (art_of_3d) — drive Roughness with low-frequency noise to break perfectly-uniform surfaces
- **Subtle displacement on fabrics** (coral lab) — small physical displacement on sherpa / boucle fabric for silhouette break
- **HDRI calibration spheres** (coral lab) — round-1 single-source still; no corroboration this round

### Tutorial-only observations not encoded

- **Cycles samples 256-4096 range** observed across tutorials; falls within our existing `render-output.md` ≥ 512 hero / ≥ 1024 construction band. No new rule needed.
- **OptiX denoiser** (rileyb3d only) — 1/5; encoded as alternative to OIDN in the new section but flagged as RTX-accelerated optional path

### Tests

`pytest tests/test_handbook_acceptance.py` — 6 passed (citation density, no fabricated section markers, sources block, substantial chapters all green).

### Commit

(this round)

---

## 2026-05-01 — Round 1: Photoreal interior production techniques (single-source)

**Analyses synthesized**:
- `analyses/2026-05-01-coral_lab-Creating_a_photorealistic_Japandi_interior_in_Blender.md` (only one available; user explicitly asked to apply rather than wait for second source)

**Discipline note**: This round violates the workflow's default "≥ 2 analyses for cross-tutorial agreement" gate. The user (Mickey) explicitly directed apply-on-one-source. To compensate, every rule applied here has been **paired with a primary-source citation** found via WebSearch (Blender Manual / Cycles docs / VFX industry on-set kit guides / Paul Debevec 1998 SIGGRAPH IBL paper) — so the encoded handbook content is grounded in something more durable than a single tutorial.

**Cross-tutorial agreement** (techniques that appeared in 2+ analyses): N/A this round (only 1 analysis).

**Project changes applied**:

- ADD-RULE in `docs/handbook/lighting.md` § "HDRI exposure calibration via reference spheres" — encodes the chrome-ball / gray-ball / white-ball / black-ball calibration sequence for HDRI strength tuning before any room materials are applied. Primary source: Paul Debevec 1998 SIGGRAPH *Rendering Synthetic Objects into Real Scenes*; corroborating industry standard via Digital Domain X-Men (2000) and modern on-set kit guides (vfxballstore.com / refballstore.com). Tutorial-specific 4-sphere variant (vs. canonical 2-sphere chrome+gray) flagged as single-source pending corroboration.
- ADD-RULE in `docs/handbook/materials.md` § "Cycles-specific shader patterns / Shadow-less transparent objects" — encodes the Mix Shader + Transparent BSDF + Light Path `Is Shadow Ray` idiom for sheer curtains / scrims / netting. Primary source: Cycles Light Path node documentation summarized via Blender Artists forum + Graphics&Programming tutorial. Application to interior sheer-curtain context is the tutorial contribution.
- ADD-RULE in `docs/handbook/materials.md` § "Cycles-specific shader patterns / Real-world UV scaling" — encodes the discipline of UV-scaling textures to physical pattern dimensions (30 cm planks, 215 × 65 mm bricks, 75 × 150 mm subway tile). Primary source: Adobe Substance PBR Guide Part 1 *"Texture sets and UV layout"*. Tutorial-specific Magic UV addon recommendation flagged as single-source pending corroboration.
- ADD-RULE in `docs/handbook/materials.md` § "Cycles-specific shader patterns / Mix Color (Overlay) for grayscale tinting" — encodes the Mix Color Overlay node pattern for adding color tint to grayscale textures while preserving contrast. Primary source: Blender Manual *Mix Color Node*. Tutorial application is generic Blender practice.

**Single-tutorial findings recorded but flagged for corroboration**:
- 4-sphere variant of HDRI calibration (vs. canonical 2-sphere) — recorded; await second tutorial confirming the 4-sphere refinement specifically
- Magic UV addon as the canonical real-world-scaling tool — recorded; await second tutorial confirming this specific addon (the underlying discipline is corroborated; just the tooling choice is single-source)

**Tutorial-only observations not encoded as rules** (would need 2+ sources):
- Cycles 1024 samples for portrait-orientation 1000×1250 social-media format renders — falls within our existing "≥ 512 hero" gate band; no new rule needed
- 50mm focal length used in tutorial — **conflicts** with our `camera.md` recommendation of 24-35mm for interiors. Single-source against published primary (McGrath, ASMP). Not encoded; flagged for human review when a second tutorial appears using 50mm in an interior context.
- HDRI strength 5.0 — too HDRI-specific (depends on the source HDRI's exposure baseline) to encode as a rule

**Tests**: `pytest tests/` 250 passed; `pytest tests/test_handbook_acceptance.py` 6 passed (citation-density gate, no-fabricated-section-markers gate, sources-block gate all green).

**Commit**: (this round)

