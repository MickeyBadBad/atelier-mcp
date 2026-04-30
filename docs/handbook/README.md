# Interior Design Handbook

This handbook is the **source of truth** for design knowledge consumed by the Interior Design Workflow MCP. Every numeric value, range, rule, or code reference herein is fetched from authoritative public sources and cited inline.

> **Hard rule (per the Sources & Citation Policy):** Do not write content from training memory. Do not invent section numbers. Do not paraphrase a "common-sense" interior-design rule without an inline citation. If no authoritative source can be located for a claim, state so explicitly rather than fabricating a number.
>
> See `docs/dev/specs/2026-04-29-interior-design-workflow-design.md` § "Sources & Citation Policy" for the full policy.

## Chapter index

### Core knowledge chapters

- [`codes.md`](codes.md) — Building codes: China GB safety / accessibility / fire egress + ADA reference
- [`lighting.md`](lighting.md) — Layered lighting: Kelvin ranges, Lux targets, fixture spacing
- [`spatial.md`](spatial.md) — Clearances, circulation, ergonomics, eye-level
- [`materials.md`](materials.md) — PBR principles, color theory, finish adjacency
- [`camera.md`](camera.md) — Architectural photography conventions, lens choice, framing
- [`styling.md`](styling.md) — Composition, vignette construction, prop curation
- [`render-output.md`](render-output.md) — View transforms (AgX), exposure, hero shot conventions
- [`furniture.md`](furniture.md) — Furniture types, standard dimensions, when-to-use
- [`acoustics.md`](acoustics.md) — Absorption coefficients, NRC, sound isolation
- [`discovery.md`](discovery.md) — Discovery questionnaire mechanics, scoring, output schema
- [`project-types.md`](project-types.md) — Multi-space organization rules per project type

### Style chapters (one per style)

Located under `styles/`. Each style chapter cites real named projects and named publications — never generic "this style usually uses X" prose.

### Space-type chapters (one per space type)

Located under `space-types/`. Each space-type chapter cites the relevant code section (GB / IBC / Neufert) for clearances and dimensions.

## Citation format

Every numeric claim or rule **must** carry an inline citation. Acceptable formats:

```markdown
Living-room sofa-to-coffee-table clearance: 400-460mm
(per Neufert Architects' Data, 5th ed., §"Living Rooms";
 Panero & Zelnik 1979 fig. 130 corroborates).
```

```markdown
Restaurant maintained illuminance: 75 lx average
(per GB 50034-2013 §5.1.5 Table 5.1.5; IES Lighting Handbook
 10th ed. §29 corroborates 50-100 lx for fine dining).
```

When sources disagree or no canonical source exists:

```markdown
Convention varies across sources. Defaulting to range Z based on
majority practice across [Source A], [Source B], [Source C].
```

## Adding a new chapter

1. **Identify authoritative sources first.** Listed in priority order in the spec § "Authoritative source list".
2. **WebFetch each source URL** before writing. If a URL is paywalled / 403, fall back to a published summary or government statute aggregator and cite it as the indirect source.
3. **Extract the specific numeric values and rules** with source attribution preserved.
4. **Write the chapter** using the **Chapter Template** below.
5. **Verify every numeric claim has an inline citation.** Run `pytest tests/test_handbook_acceptance.py` before commit.
6. **Update this index.**

## Chapter Template

```markdown
# <Chapter Title>

> Sources: <comma-separated list of primary sources used>
> Last updated: YYYY-MM-DD

## Purpose

Brief statement (2-3 sentences) of what this chapter covers and what
downstream consumers (skills, quality gates, AI explanations) do with it.

## Rules

### <Rule Group 1>

- Rule statement (numeric value where applicable) (inline citation)
- ...

### <Rule Group 2>

- ...

## Worked examples

Optional: 1-2 examples showing how to apply the rules in practice.

## Common mistakes

Optional: 2-4 typical failure modes that the rules in this chapter prevent.

## See also

- Cross-references to other chapters (e.g. `lighting.md` for downstream
  consumers of color rules in `materials.md`).
```
