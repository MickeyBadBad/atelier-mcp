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

