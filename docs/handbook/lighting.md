# Lighting Design

> Sources: GB 50034-2013 (建筑照明设计标准), IES Lighting Handbook (10th ed., as summarised by Archtoolbox and Modern.Place IES handouts), CIE 13.3-1995, EN 12464-1, Wikipedia (Color Rendering Index, Color Temperature, Lighting), ERCO Lighting Knowledge Base, Blender 4.5 LTS Manual.
> Last updated: 2026-04-29

## Purpose

This chapter defines the lighting parameters an AI agent must pick or validate when designing or rendering an interior: layer composition, Kelvin (correlated color temperature, CCT), maintained illuminance (lux), color rendering index (Ra / CRI), and fixture-spacing rules of thumb. Downstream consumers use it to (a) select Blender light properties, (b) flag layering or temperature mismatches at quality-gate time, and (c) explain a choice to a non-designer user in plain language.

Hard rule: every number below is sourced. If a primary standards document is paywalled or returned 403 in our fetch, the cite reads "(per <summary publication> summarising <standard>; primary section not verified online)" — we do not invent section numbers.

## The four-layer model

Architectural lighting practice resolves a room into three or four functional layers. The Wikipedia "Lighting" overview (per the Wikipedia "Lighting" article, "Forms of lighting" section) names three: **task**, **accent**, and **general (ambient)** lighting. Practising designers add a fourth — **decorative** — to cover sources whose primary purpose is to be looked at (chandeliers, neon, candle stand-ins).

| Layer | Purpose | Typical lux contribution at the work plane | Source |
|---|---|---|---|
| Ambient (general) | Baseline visibility for circulation; sets the room's "fill" | 50–80 lux for lounge / 200–500 lux for office | (per Wikipedia "Lighting" art. — three-layer taxonomy; per IES residential summary on Super Bright LEDs — bedroom/living general 20 fc ≈ 200 lux; per Archtoolbox citing IESNA Handbook — open office 30–50 fc) |
| Accent | Directs the eye to focal objects (art, product, architectural feature) | 3–5× the ambient level on the focal object | (per ERCO Lighting Knowledge "Arranging luminaires" — accent illuminance contrast ratio rule of thumb; primary IES section not verified online) |
| Task | Local illumination for an activity (reading, food prep, retail counter, bar) | 300–750 lux at the task surface | (per Archtoolbox citing IESNA Handbook — kitchen task 70 fc ≈ 750 lux; per Super Bright LEDs IES summary — vanity task 80 fc, kitchen counter 70 fc) |
| Decorative | The fixture itself is a visual element; lumen output is secondary | 20–40 lux contribution typical | (per Wikipedia "Lighting" article — accent / decorative distinction; specific numeric range is convention, not standard) |

The four-layer breakdown above is interior-design convention rather than a numbered clause in any single standard. When citing it to a client, frame it as practice-based, not code-mandated.

## Kelvin by space type

Color temperature is reported in kelvin (K) along the Planckian (blackbody) locus. Lower K reads warmer (yellow/orange); higher K reads cooler (blue-white). The Kelvin scale itself is grounded in CIE colorimetry (per Wikipedia "Color temperature" article — definition via the ideal Planckian emitter; primary CIE 015:2004 section not verified online — cf. summary in the Wikipedia article).

| Space type | Recommended CCT (K) | Source |
|---|---|---|
| Residential — living, bedroom, dining | 2700–3000 K | (per LEDLightExpert / Lumens / Centerlight industry guidance — "warm white" residential default; corroborated by Super Bright LEDs IES residential guide) |
| Hospitality — hotel lobby, bar, lounge, cafe | 2700–3500 K | (per Lumens "Kelvin Color Temperature Chart"; per Luminate Lighting commercial guide — "warm-to-neutral creates cozy, inviting atmosphere") |
| Restaurant — fine dining | 2400–2700 K | (per Luminate Lighting commercial guide — quick-serve 2700–3500 K, fine dining biased warmer; primary IES RP-3 / hospitality publication not verified online) |
| Restaurant — casual / fast-casual | 2700–3500 K | (per Luminate Lighting commercial guide; corroborated by Centerlight "What is color temperature" guide) |
| Office — general | 3500–4000 K | (per BenQ home-office guide; per Guocio commercial-office guide; corroborated by Luminate commercial guide — "neutral white 3500–4000 K balances comfort and focus") |
| Retail — boutique / luxury | 3000–4000 K | (per Luminate commercial guide — "luxury retail extends to 4000 K to highlight merchandise") |
| Retail — general / supermarket | 4000–5000 K | (per IKIO commercial CCT guide; per Luminate commercial guide — "general retail biased cooler for high-visibility merchandising") |
| Workshop / lab / clinical | 4000–5000 K | (per IKIO commercial CCT guide; per Centerlight guide — "cool white for detailed tasks") |

GB 50034-2013 organises lamps into 三组 (three CCT groups): warm color < 3300 K, intermediate 3300–5300 K, cool > 5300 K (per GB 50034-2013, color appearance group classification; primary § not verified online — cf. summaries on Casyoo and Recolux Lighting reproducing the table).

A speakeasy / shisha-lounge style typically locks 2200–2400 K — warmer than the residential default — so the space reads as bar/lounge rather than living room. This is a style-driven call layered on top of the GB/IES range, not a standards-derived number; see `styles/speakeasy.md` (when it lands) for the convention.

## Maintained illuminance (Lux) by space type

"Maintained illuminance" means the average lux at the working plane after lamp lumen depreciation and dirt-on-luminaire factors are applied. GB 50034-2013 Table 5.x and the IES Lighting Handbook are the two canonical sources.

| Space type | Recommended (lux) | Source |
|---|---|---|
| Residential — living room, general | 100–300 lux | (per Wosen LED standard-lux summary; corroborated by Archtoolbox citing IESNA Handbook — dormitory living quarters 20–30 fc ≈ 200–300 lux) |
| Residential — bedroom, general | 75–150 lux | (per Wosen LED standard-lux summary; per Super Bright LEDs IES residential — bedroom 20 fc ≈ 200 lux maximum) |
| Residential — kitchen, task at counter | 500–750 lux | (per Super Bright LEDs IES residential — kitchen task 70 fc ≈ 750 lux; corroborated by Wosen LED chart) |
| Residential — bathroom, vanity task | 300–800 lux | (per Super Bright LEDs IES residential — vanity 80 fc ≈ 800 lux) |
| Office — general / open-plan | 300–500 lux | (per Archtoolbox citing IESNA Handbook — office open 30–50 fc; per GB 50034-2013 ordinary office 300 lx, high-grade office 500 lx, summarised in Casyoo lighting calculation guide; primary GB Table 5.x clause not verified online) |
| Office — conference / executive | 500–750 lux | (per Modern.Place IES standards summary — conference 750 lux, executive 500 lux; corroborated by Lumitron IES handout) |
| Retail — general sales floor | 200–500 lux | (per Archtoolbox citing IESNA Handbook — retail sales 20–50 fc) |
| Retail — feature / product highlight | 750–1500 lux | (per Wosen LED chart citing industry retail practice; primary IES RP-2 retail clause not verified online) |
| Hospitality — hotel lobby | 200–300 lux | (per Archtoolbox citing IESNA Handbook — lobby 20–30 fc) |
| Hospitality — lounge / bar | 100–300 lux | (per Archtoolbox citing IESNA Handbook — lounge/breakroom 10–30 fc; for low-key bar settings the lower end of the range applies, per industry practice on Centerlight) |
| Restaurant — fine dining | 50–100 lux | (per IES Lighting Handbook 10th ed., restaurant § as summarised by the GB 50034-2013 commentary on Recolux Lighting — fine-dining 75 lx avg; primary IES § not verified online) |
| Restaurant — cafeteria / quick-serve | 200–300 lux | (per Archtoolbox citing IESNA Handbook — cafeteria eating 20–30 fc) |
| Warehouse — general | 100–200 lux | (per Recolux Lighting summary of GB 50034-2013 warehouse clause — 100–200 lx; primary GB § not verified online) |
| Circulation — corridor / hallway | 50–100 lux | (per Wosen LED chart; corroborated by Lumitron IES handout) |

For the cafe project the v2 plan calls 50–80 lx ambient / 150–300 lx accent / 20–40 lx per-table. Those numbers sit at the lower end of the hospitality lounge band above and are deliberate for the speakeasy aesthetic.

## CRI (Ra) minimums

CIE 13.3-1995 defines **how** to compute Ra (the General Color Rendering Index, average of R1–R8 against a reference Planckian or daylight illuminant) but does **not** prescribe a minimum acceptable value (per CIE 13.3-1995 — "Method of measuring and specifying colour rendering properties of light sources"; primary § not directly verified due to PDF-stream extraction failure — cf. Wikipedia "Color rendering index" summary describing the ten-step calculation and the von Kries chromatic-adaptation step).

Application minimums come from companion standards:

| Space type | Minimum Ra | Source |
|---|---|---|
| General interior workplace | Ra ≥ 80 | (per EN 12464-1 — "Lighting of indoor workplaces" — minimum for most activities; summarised in Wikipedia "Color rendering index" article and XAL "CRI Colour rendering" knowledge note) |
| Office (visual tasks involving color judgement) | Ra ≥ 80 | (per EN 12464-1 default; corroborated by ISO/CIE 8995 as summarised on Tandfonline article *LED lighting system for better color rendition space*) |
| Retail — apparel / cosmetics / food | Ra ≥ 90 | (per industry practice for color-critical merchandise; primary IES RP-2 retail clause not verified online — cf. summary on Tandfonline *LED lighting system for better color rendition space* — "retail interiors needing better color rendition have Ra > 80, often > 90") |
| Hospitality — restaurant, hotel, lounge | Ra ≥ 80, ideally ≥ 90 for food | (per EN 12464-1 baseline; the food-display ≥ 90 figure is industry practice corroborated on multiple LED-vendor knowledge bases) |
| Residential | Ra ≥ 80 | (per de-facto practice since the CFL/LED transition; per US DOE Energy Star adoption of CIE Ra ≥ 80, summarised in Wikipedia "Color rendering index") |
| Galleries / museums / color-critical work | Ra ≥ 90, R9 ≥ 50 | (per industry practice; primary IES RP-30 museum clause not verified online — TM-30 Rf / Rg metrics increasingly preferred over Ra alone, per Wikipedia "Color rendering index" §"Newer metrics" and DOE TM-30 tutorial) |

Where TM-30 is available, prefer Rf ≥ 78 and Rg between 95 and 105 (per ANSI/IES TM-30, summarised in DOE *Background and Guidance for Using the ANSI/IES TM-30* — primary TM-30 clause not verified online).

## Fixture spacing rules

The two operational rules of thumb for downlight pitch:

- **Half-the-ceiling-height rule:** spacing on-centre ≈ ceiling height ÷ 2. An 8 ft (≈ 2.4 m) ceiling → ~ 1.2 m pitch; a 10 ft (≈ 3 m) ceiling → ~ 1.5 m pitch (per industry rule of thumb summarised on takethreelighting.com and obals.com — primary IES Lighting Handbook § not verified online).
- **Spacing-criteria (S/MH) method:** S = SC × MH, where SC is published per fixture (typically 0.5–1.5) and MH is mounting height above the work plane (per IES Spacing Criteria definition, summarised on abenetworks.com glossary — primary IES § not verified online; corroborated by ERCO Lighting Knowledge "Arranging luminaires" — uniform general lighting tolerates spacing up to 1.5× the height of the luminaire above the working plane).

For wall offset:

- First row of downlights sits at **half the inter-fixture spacing** from the wall. Corner luminaires are mounted on the 45° line so the two illuminated wall segments match (per ERCO Lighting Knowledge "Arranging luminaires" article).
- For wall-grazing (showcasing texture on a finished wall), the fixture is placed **150–300 mm out from the wall** and aimed near-parallel to the surface; for wall-washing (uniform vertical illuminance) the fixture sits **at distance ≈ ⅓ of mounting height** from the wall (per ERCO Lighting Knowledge "Arranging luminaires" — wall-wash and wall-graze geometry; primary IES § not verified online).

For a typical small-commercial ceiling (≈ 2.7 m), this gives a downlight pitch in the 1.0–1.4 m range and a wall offset of ~0.5–0.7 m before the first row.

## HDRI exposure calibration via reference spheres

Photoreal interior renders depend on getting the HDRI strength **objectively right** before any room materials are applied — otherwise every subsequent material decision compensates for under- or over-exposure and the scene drifts. The professional VFX practice is to plant **calibration reference spheres** (a chrome ball + a neutral 18% gray ball + sometimes white and matte black balls) in the scene, then tune HDRI strength until each sphere reads correctly under the chosen view transform (per Paul Debevec's seminal 1998 SIGGRAPH paper *Rendering Synthetic Objects into Real Scenes*, the IBL paper that established the chrome+gray reference-sphere pattern in production VFX; canonized into a standard on-set kit by Digital Domain on *X-Men* (2000), the first feature-film VFX workflow to use chrome balls for HDRI capture per *befores & afters* "VFX Firsts" 2021).

Calibration check (after planting the spheres in the empty room shell, before applying scene materials):

- **Chrome sphere** — should clearly show the surrounding HDRI environment without highlights blowing out
- **18% gray sphere** — should read as middle gray under the active view transform (AgX / Filmic), not too bright nor crushed
- **White sphere** — should approach white but retain texture in highlights (no clipping)
- **Black sphere** — should read deeply but not pure-black-clipped — the back-shadow side should still have some shape

If any sphere fails its check, adjust the HDRI strength and re-render, not the camera exposure. The HDRI is the physical light source; treating it as the variable-of-record is what makes the rest of the scene predictable. The 4-sphere variant (black + gray + white + chrome) is a refinement of the 2-sphere on-set reference kit (chrome + 18% gray), with the extra two spheres giving better signal at the dynamic-range extremes (per VFX-industry on-set kit guides at *vfxballstore.com* / *refballstore.com*; observed in coral lab "Photorealistic Japandi Interior in Blender" tutorial 2024-04, single-source for the 4-sphere variant — corroboration from a second tutorial pending).

Once calibrated, apply room materials and re-check that the spheres still read correctly. Re-tune HDRI strength only if they drift; do NOT keep adjusting it as you add materials, or you'll chase your tail.

## Blender practical mapping

Blender Light objects accept Kelvin two ways:

1. **Light data colour as a Blackbody node.** In the shader editor for the light, add a `Converter → Blackbody` node, set its Temperature input in Kelvin, and feed its output into the light's Color input (or directly into an Emission shader's Color for emissive materials). The Blackbody node converts a blackbody temperature to RGB (per Blender 4.5 LTS Manual page *Blackbody Node* — "converts a blackbody temperature to RGB value … useful for materials that emit light at natural occurring frequencies"; primary Blender Manual page returned 403 in our fetch — cf. summaries via Blender Artists forum threads and the Medium tutorial *This Trick Gives You Ultra-Realistic Light Colors*).
2. **Direct RGB on the light's Color picker.** Acceptable for stylised work but loses physical correspondence between scene lights at different CCTs.

Caveats:

- Blender treats 6500 K as pure white because that matches the sRGB D65 whitepoint (per Blender Artists forum *Blackbody, Kelvin, sRGB, physical lights* thread — note that perceptually this reads cool/blue in interior contexts, so 3000–3500 K is the practical "neutral white" on screen; primary Blender Manual statement on D65 not verified online).
- Pair Blackbody-driven light with **AgX or Filmic** view transform (set in Render Properties → Color Management). Standard sRGB view will clip warm light into orange muddiness (per Blendergrid *Using Physically Correct Brightness in Cycles* — "switch to Filmic Color Management … allows working in a far more dynamic color space"; corroborated in our `render-output.md`).
- For a speakeasy palette (2200–2400 K amber), feed `2300` directly into the Blackbody node's Temperature; do not eyeball an orange RGB value.

## Worked examples

**Example 1 — Speakeasy lounge, 25 m² seating zone.**

Style-driven targets (one example deviation from GB/IES residential defaults): ambient 50–80 lx, accent 150–300 lx, per-table 20–40 lx, all at 2200–2400 K. Approach:

- Ambient: matte-black ceiling track of 8–10 small downlights, 1.2 m pitch, S/MH = 0.5 over a 2.4 m mounted height (per the half-ceiling rule above).
- Accent: 3–4 picture-light fixtures aimed at the focal wall surfaces at 200–300 lx (≥ 4× the ambient level, per the four-layer accent contrast rule).
- Per-table: pendants at 1.5 m above the table providing 20–40 lx local fill (lower than IES restaurant cafeteria 200–300 lx — style convention for speakeasy ambience).
- All fixtures: Blackbody node @ 2300 K → Emission, AgX view transform, render-engine Cycles.

**Example 2 — Validating an AI-proposed plan.**

User asks for "a bright, modern cafe at 4000 K". Quality gate cross-checks against this chapter:

- 4000 K sits in the office band, not hospitality (per the Kelvin table). Flag.
- Suggest 2700–3500 K from the hospitality row.
- If the user insists on 4000 K, surface the trade-off: cooler light reads alert/clinical, kills the warm column glow off any volumetric haze, and reduces perceived intimacy in a hospitality context.

## Common mistakes

- **Mixing CCTs unintentionally.** Two adjacent fixtures more than ~ 300 K apart will read as "broken" to the eye. Use one CCT per layer unless contrast is the design intent (per Lumens *Kelvin Chart* and Centerlight guide — pro-tip on intentional vs. accidental CCT mixing).
- **Optimising lumens, ignoring lux.** Lumen is a fixture rating; lux is what hits the work plane. Always design to the maintained-illuminance target after distance and reflectance losses (per IES Lighting Handbook foundational distinction — summarised on Wosen LED and Archtoolbox).
- **Over-cool retail.** Pushing > 5000 K in apparel retail makes skin and warm fabrics read sallow; Ra ≥ 90 is more important than higher K (per Tandfonline *LED lighting system for better color rendition space* — color rendition outweighs CCT for merchandise).
- **Ignoring CRI on warm LEDs.** Cheap 2700 K LEDs often ship with Ra 70–75; below the EN 12464-1 minimum of 80 (per EN 12464-1 summary in Wikipedia "Color rendering index"). For a hospitality interior, specify Ra ≥ 90 explicitly.

## See also

- `codes.md` — emergency / egress lighting requirements (separate from design illuminance)
- `materials.md` — how surface reflectance changes the lux you actually see
- `render-output.md` — AgX / Filmic view transforms required to render Blackbody-driven lights correctly
- `space-types/` — per-space-type chapters override the generic ranges above with the specific clause cited
