# Gemini full-video extraction prompt

> Copy everything below the `---` line into Gemini (AI Studio or API), with a YouTube URL attached. Replace `<URL>` in the first line of the prompt with the same URL for traceability.

---

You are analyzing a Blender interior design tutorial video for the **Atelier** project — an open-source AI interior design tool that ships handbook-grounded design rules + a Blender MCP server. We use this analysis to (a) update our 39-chapter handbook, (b) tune our 9-dimension quality gates, (c) refine our 5 Claude skills, and (d) decide whether to add new MCP tools.

**Source video**: <URL>

# Your job

Watch the **entire** video carefully. Your output is a single markdown file conforming **exactly** to the schema below. The consumer is another LLM that parses your output programmatically — structural fidelity matters more than prose polish. If a section's data is not present in the video, write `(not shown in video)` rather than skipping the section.

Pay equal attention to **what the creator says** (audio narration), **what they do** (UI clicks, slider drags, panel navigation), and **what's on screen** (panel values, color picker positions, render output, before/after comparisons). Visual settings shown but not narrated still count — note them.

For numeric values: prefer values **read from the UI** over values inferred from speech. If a creator says "I'm cranking up samples" but the camera doesn't show the value, write `(narrated but value not visible)`. If they show 512 in the samples field, write `512`.

Quote-mark direct narration ≤ 3 lines. Synthesize anything longer.

# Output schema (follow exactly)

```markdown
# Video Analysis: <video title>

## Source
- URL: <url>
- Channel: <channel name>
- Published: <YYYY-MM-DD if visible in description; else (not shown)>
- Length: <hh:mm:ss>
- Topic: <one-line topic, ≤ 80 chars>
- Tutorial style: <step-by-step | timelapse-with-narration | comparison | finished-walkthrough | other>

## TL;DR (5 sentences max)

<What the creator builds, the target output quality, the headline technique, and the final outcome.>

## Project shape

- Project type: <one of: residential_apartment | residential_house | cafe_lounge | restaurant_full_service | retail_boutique | office_small | other>
- Style closest match: <one of: scandinavian | japanese-wabi-sabi | modern-minimal | new-chinese | french-cream | mid-century-modern | muji-minimal | american-classic | mediterranean | quiet-luxury | industrial-loft | speakeasy | insta-cafe | japanese-tea-cafe | chinese-tea-house | boutique-retail | modern-chinese-restaurant | coworking-office | industrial-cafe | other (specify)>
- Final output: <hero-render | view-set | animation | VR | construction-grade | demo-only | other>
- Overall finish quality: <low | mid | high | production-photoreal>

## Settings extracted (numeric — be exact)

### Render

- Engine: <Cycles | EEVEE Next | Octane | Corona | other>
- Samples (visible value): <int or "(not visible)">
- Adaptive sampling: <on/off>, threshold: <float or "(not visible)">
- Light Tree: <on/off | (not shown)>
- Denoiser: <OpenImageDenoise | OptiX | none | (not shown)>
- View transform: <AgX | AgX Punchy | Filmic | Standard | Raw | other>
- Look: <None | Low/Medium/High Contrast | Punchy | other>
- Resolution: <W × H if shown>
- Render time mentioned: <if mentioned, e.g. "12 min on RTX 4080">

### Lighting

- Fixture types observed: <comma list: pendant | downlight | strip | sun | hdri | area | spot | mesh-emission>
- Number of distinct lights in scene: <int or "(not shown)">
- Layered model used: <ambient-only | ambient+accent | ambient+accent+task | 4-layer-with-decorative | (not classifiable)>
- Kelvin values seen on UI: <list of Kelvin values visible in light data panels>
- Colors set as RGB instead of Kelvin: <yes/no — if yes, this is a sign the creator isn't using physical color>
- HDRI used: <name if shown / "custom" / "no HDRI">
- HDRI strength: <float if shown>
- Sun strength: <float if shown>

### Camera

- Focal length: <int mm or "(not visible)">
- Sensor width: <mm if shown — Blender default is 36>
- Camera height (z): <m if visible>
- Lens shift X / Y (for vertical correction): <floats if shown>
- DOF: <on/off>, f-stop: <if on>
- Clip Start: <if shown>

### Materials & shading

- Principled BSDF only: <yes/no — if no, what custom shaders>
- Texture sources observed: <comma list: PolyHaven | AmbientCG | Substance Designer | Substance Source | Quixel Megascans | self-photo | procedural-only | other>
- Roughness ranges per category visible:
  - Walls: <range or "n/a">
  - Wood floor: <range>
  - Metals: <range>
  - Fabrics: <range>
  - Glass / clear: <range>
- Bump / normal map intensity tweaks observed: <description>
- Notable shader graph patterns: <bullet list of notable techniques: ColorRamp on roughness, AO mix into base color, RGB Curves on roughness, displacement vs bump trade-off, etc.>

### Composition / styling

- Prop density (subjective, 1-5): <1=bare, 5=cluttered>
- Texture variation per surface: <2 | 3 | 4+>
- Negative space estimate: <% bare>
- Vignette anchor types observed: <bullet list>
- Furniture sources: <comma list: Sketchfab | PolyHaven | self-modeled | BlenderKit | Quixel Megascans | other>

### Post-processing (compositing or external)

- In-Blender compositor used: <yes/no>
- Color grading nodes: <bullet list if shown — Color Balance, RGB Curves, Hue/Sat, Lift/Gamma/Gain>
- Glare / bloom: <yes/no, settings if shown>
- Vignette in compositor: <yes/no>
- External program used (Photoshop, Lightroom, etc.): <yes/no, what for>

## Workflow sequence (chronological)

In the order the creator works:

1. <action 1>
2. <action 2>
3. ...
N. <last action>

Note **stage transitions** explicitly when the creator says something like "now let's set up lighting" or "time to add materials" — these mark Atelier workflow phase boundaries.

## Photorealism techniques (the "secret sauce")

Bullet list of specific tricks that elevate the result beyond a default Blender render. For each, write what it is + what problem it solves.

- <technique 1>: <what it does, what problem it solves>
- <technique 2>: ...

## Common mistakes the creator calls out

What the creator explicitly tells viewers NOT to do.

- "<verbatim quote ≤ 1 line>" — <synthesized rationale>
- ...

## Direct quotes worth preserving

≤ 3 quotes, each ≤ 3 lines. Pick quotes that capture the creator's *philosophy* or a memorable rule of thumb.

> "..."

## Time estimate (if visible)

If the creator gives stage timings ("the lighting took me 30 minutes", "modeling was an evening"), list them.

- <stage>: <time>

## Deltas vs Atelier

This section is the most important — it drives the synthesis step.

### What they do that Atelier already supports

Bullet list of techniques in the video that Atelier already encodes (in handbook chapters or MCP tools). Cross-reference our chapters by name when possible.

- <technique>: encoded in `<chapter>.md` / `<tool>` / `<gate>`

### What they do that Atelier does NOT yet support

The high-value list. Each item: what they do + which Atelier surface (handbook chapter / gate / skill / tool) needs to gain it.

- **<technique>** — should be added to: `<target file>` as `<short rule statement>`
- ...

### What conflicts with our handbook

Where the video says one thing and our handbook says another. For each: cite our handbook chapter, cite the video moment (timestamp), and offer your judgment on which is likely right (you don't have to be definitive — flag for human review).

- `lighting.md` says X, video at 14:32 says Y → likely <X | Y | both depending on context>; recommend human review.

## Recommended Atelier project changes (concrete diffs)

Final, actionable list. Format each as a one-line "do this":

- ADD-RULE in `docs/handbook/<chapter>.md`: "<rule text>"
- TUNE-GATE in `src/atelier/_gates.py:<function>`: change `<old value>` → `<new value>`
- EDIT-SKILL `.claude/skills/<name>.md`: add the instruction "<text>"
- ADD-TOOL in `src/atelier/server.py`: new tool `<name>(<sig>)` doing `<purpose>`

If no project change is warranted (the video confirms what we already do), say:

> No project changes recommended — video confirms current Atelier defaults.
```

# Reminders

- The schema above is what Claude will parse. Stay structurally faithful.
- Numeric values: prefer UI-visible over narrated.
- If you can't determine a value, write `(not shown)` or `(narrated but value not visible)` — never guess or fabricate.
- The "Deltas vs Atelier" + "Recommended changes" sections are the high-value output. Spend the most effort there.
- If the video is *not actually* about photorealistic interior rendering (e.g. it's a hard-surface modeling tutorial mistakenly tagged), say so up front and stop after the TL;DR.
