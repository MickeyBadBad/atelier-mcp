# Materials and Color

> Sources: Brent Burley, "Physically-Based Shading at Disney" (SIGGRAPH 2012); Walt Disney Animation Studios reference BRDF (`wdas/brdf`, GitHub); Khronos glTF 2.0 Specification (registry.khronos.org); Khronos "Art Pipeline for glTF" blog; Marmoset, "Basic Theory of Physically-Based Rendering" (marmoset.co); LearnOpenGL, "PBR / Theory" chapter (learnopengl.com); Blender Manual — Principled BSDF (docs.blender.org/manual/en/latest); Yale University Press, Josef Albers, *Interaction of Color* (1963 / 50th-anniversary ed.); Munsell Color Company, "How Color Notation Works" (munsell.com); Pantone, via Wikipedia "Pantone" (en.wikipedia.org); Homes & Gardens "60-30-10 rule" (homesandgardens.com); Livingetc "60-30-10 rule" (livingetc.com).
> Last updated: 2026-04-29

## Purpose

This chapter gives an AI agent (and the non-designer user reviewing its output) the smallest set of physically-grounded numbers needed to (1) author Blender Principled BSDF materials that read as real, and (2) compose a 3-color palette that does not look like a hardware-store catalog. Every numeric range below is sourced; values without a citable source are flagged "(uncited — convention)" so they can be challenged later.

## PBR principles

### Energy conservation

Energy conservation is the rule that **outgoing reflected light must not exceed incoming light** for a non-emissive surface. LearnOpenGL's "PBR / Theory" page states the principle as *"outgoing light energy should never exceed the incoming light energy (excluding emissive surfaces)"* (per LearnOpenGL — PBR/Theory, "Energy conservation" section). Marmoset adds the corollary that *"reflection and diffusion are mutually exclusive"* — a photon that reflects off the surface cannot also be diffused inside it (per Marmoset, "Basic Theory of Physically-Based Rendering", "Energy Conservation" section).

The Disney "principled" BRDF (Burley 2012) is the model Blender's Principled BSDF inherits from. It is described in the reference implementation and academic summaries as *"a hybrid of physically-derived mathematics, artist-friendly parameters, and empirically-backed resulting appearances"* (per UIUC CS418 lecture notes — "Burley's Principled BRDF"). Practically: do not crank Specular, Sheen, and Coat all to 1 on the same material. The shader will *let* you, but you are stacking lobes that each reflect energy and the result will look hot.

### Roughness banding by material category

Roughness is the perceptual smoothness control: 0 is a perfect mirror, 1 is fully matte. The Disney reference defines `roughness` as a 0-1 parameter with default 0.5 (per `wdas/brdf/src/brdfs/disney.brdf`, parameter declarations). In microfacet theory, *"the rougher a surface is, the more chaotically aligned each microfacet will be"* (per LearnOpenGL — PBR/Theory, "The microfacet model" section), which scatters reflections into a wider, dimmer cone.

Substance's published roughness chart for material categories was not directly accessible to fetch (the Adobe-hosted PBR Guide returned 403 / timed out at the time of writing). The values below are therefore drawn from publicly fetchable PBR theory references and standard graphics-pedagogy practice; each cell is labeled with what is cited vs. conventional.

| Material category | Roughness range | Source |
|---|---|---|
| Polished metal (chrome, mirror) | 0.0 – 0.1 | (per LearnOpenGL — PBR/Theory, "Microfacet model" — smooth surfaces produce sharp reflections; specific 0.0–0.1 banding is convention, uncited) |
| Brushed / satin metal (brass, brushed steel) | 0.2 – 0.4 | (uncited — convention; aligns with Disney `anisotropic` parameter intent per `wdas/brdf` reference) |
| Glass, clear plastic, polished ceramic | 0.0 – 0.1 | (per LearnOpenGL — PBR/Theory; per Marmoset "Basic Theory of PBR", smooth dielectrics) |
| Painted gloss surfaces (lacquered wood, gloss tile) | 0.1 – 0.3 | (per Marmoset — "paints and plastics tend to come in a variety of different finishes from matte to glossy", "Microsurface" section; banding is convention) |
| Painted matte surfaces (wall paint, matte plaster) | 0.6 – 0.9 | (per Marmoset, same section; banding convention) |
| Plastics (general) | 0.3 – 0.5 | (uncited — convention summarized in community Blender guides citing the Blender manual) |
| Wood, varnished | 0.2 – 0.5 | (uncited — convention) |
| Wood, raw / oiled | 0.5 – 0.8 | (uncited — convention) |
| Fabrics (cotton, linen, wool) | 0.7 – 1.0 | (per Disney `sheen` parameter, defined for cloth/fabric grazing-angle response, `wdas/brdf` reference) |
| Concrete, brick, stone | 0.7 – 1.0 | (uncited — convention) |
| Rubber | 0.8 – 1.0 | (per Marmoset — "rubber is generally rougher than plastic", "Microsurface" section) |

For the cafe palette specifically: walnut SPC floor (raw-feel wood) sits at roughness 0.6–0.7; weathered red brick at 0.85; brushed brass fittings at 0.25–0.35; matte-black ceiling spray at 0.85–0.95; emerald velvet (where used) at 0.9 with sheen.

### Albedo (base color) ranges

Two rules govern base color in a metal-roughness PBR workflow:

1. **Metals get their reflection color from `baseColor`.** Their diffuse component is zero. Marmoset states *"Conductors (Metals): Reflectivity reaches '60-90%' with potential spectral tinting (gold, copper, brass) and minimal diffuse component due to light absorption rather than scattering"* (per Marmoset "Basic Theory of PBR", dielectric vs. conductor section).
2. **Dielectrics (everything else) get a fixed F0 specular reflectance of about 4%, regardless of color.** LearnOpenGL: *"a base reflectivity of 0.04 holds for most dielectrics and produces physically plausible results without having to author an additional surface parameter"* (per LearnOpenGL — PBR/Theory, "Fresnel equation" section). Marmoset gives a wider band: *"Dielectrics (Insulators): Reflectivity ranges 'in the 0-20% range'"* (Marmoset, same section).

| Surface type | Albedo (sRGB, 0-1) range | Source |
|---|---|---|
| Snow, fresh white paint (practical white max) | ≤ 0.95 | (per common Blender-community guidance summarizing the Blender manual: "for dielectrics keep the color values above the 10% darkest and below the 5% lightest" — captured in the Principled BSDF search result citing docs.blender.org/manual; ceiling of 0.95 is convention) |
| Charcoal / fresh asphalt (practical black floor) | ≥ 0.05 | (same source as above; 5% floor is convention to avoid energy-eating "true black") |
| Worn matte-black (cafe ceiling spray) | 0.04 – 0.07 | (uncited — convention; do not go below 0.04) |
| Walnut wood, mid-tone | 0.10 – 0.20 | (uncited — convention; falls inside the 0.05–0.95 dielectric envelope) |
| Brick, weathered red | 0.18 – 0.30 | (uncited — convention) |
| Polished brass (metal) | RGB ≈ (0.90, 0.65, 0.30) | (per `wdas/brdf` reference — metals tint specular by `baseColor`; specific RGB is convention from MERL-database measurements summarized in Burley 2012) |
| Polished gold (metal) | RGB ≈ (1.00, 0.78, 0.34) | (per UIUC CS418 — Burley's Principled BRDF lecture notes) |
| Polished copper (metal) | RGB ≈ (0.95, 0.64, 0.54) | (per UIUC CS418 — same source) |

Practical rule: in sRGB, no dielectric base color should have *any* channel below ~0.05 or above ~0.95. If a wall paint chip in real life looks blacker than a charcoal briquette, the chip is lying — and so is your render if you author it that way.

### ORM channel packing

The glTF 2.0 specification defines a fixed channel layout for the metal-roughness texture and the occlusion texture, which most engines combine into a single "ORM" RGB image:

| Channel | Component | Source |
|---|---|---|
| R | Ambient Occlusion | (per Khronos blog "Art Pipeline for glTF" — "Red: Ambient Occlusion, Green: Roughness, Blue: Metallic") |
| G | Roughness | (per glTF 2.0 spec, `material.pbrMetallicRoughness.schema.json`: "The roughness values are sampled from the G channel") |
| B | Metallic | (per glTF 2.0 spec, same schema: "The metalness values are sampled from the B channel") |
| A | unused / ignored | (per glTF 2.0 spec — "If other channels are present (R or A), they MUST be ignored for metallic-roughness calculations") |

Blender's glTF exporter follows this packing by default. Note that **Unity URP/HDRP uses a different layout**, so ORM textures may need channel swaps when moving between engines (per Khronos community / engine documentation, summarized in Khronos "Art Pipeline for glTF").

## Color theory

### The 60-30-10 split

The 60-30-10 rule is a long-standing interior-design convention for proportioning a 3-color palette in a single space:

- **60%** — dominant color, typically walls and large soft surfaces (per Homes & Gardens, "60-30-10 rule" — "The dominant color, typically applied to walls as the room's anchor").
- **30%** — secondary color, used at half the volume of the primary (per Homes & Gardens, same article — "furniture, curtains, feature walls").
- **10%** — accent color, in artwork and small decorative objects (per Homes & Gardens, same article — "approximately 10% of furnishings").

Livingetc adds the framing: *"60 percent of the scheme should be one color, 30 percent should be a second accented color, displayed on chairs, rugs, sofas, and 10 percent should be a third color dotted around the room in the form of artwork, small touches, and accessories"* (per Livingetc, "60-30-10 rule" article, attributed to Martin Waller of Andrew Martin).

Origin — interior designers commonly trace the rule's underpinning to the Golden Section / classical proportion theory, but the *named publication* anchor for this chapter is Homes & Gardens and Livingetc. (Apartment Therapy was unreachable at fetch time and is not relied on.)

As an applied example for a hospitality interior with a deep-emerald + retro-purple palette:
- 60% — deep emerald `#1a3a2e` (dominant wall surfaces, booth, bar front).
- 30% — walnut + matte black (floor + ceiling + bar-top frame).
- 10% — retro purple `#3d2449` + brushed brass (a single photo-wall door, neon, fittings). When the design intent treats purple as a focal point rather than a third equal color, push the visible-area ceiling tighter than 10% (e.g. <8%) so it reads as a deliberate accent rather than a competing dominant.

### Color adjacency (Albers / simultaneous contrast)

Albers' *Interaction of Color* (1963) rests on the claim that color is contextual, not absolute. The Yale University Press description of the book lists his demonstrated principles as *"color relativity, intensity, and temperature; vibrating and vanishing boundaries; and the illusion of transparency and reversed grounds"* (per Yale University Press catalog, *Interaction of Color* description). Albers' own framing is captured in the *Wikipedia* article on the book: *"Every perception of colour is an illusion … we do not see colors as they really are. In our perception they alter one another"* (per Wikipedia, "Interaction of Color" article).

The practical takeaway for Blender material authoring:

- **A swatch's appearance changes based on what surrounds it.** A grey looks warm next to a cool field and cool next to a warm one. If you are color-picking a material from a reference photo, you must keep the material's *neighbours* the same as in the reference, or recalibrate.
- **Saturated complements vibrate.** Pure red against pure green (or in our case, saturated purple against saturated emerald) produces flickering, hard-to-read edges. Desaturate one side, or insert a neutral spacer (matte black, walnut).
- **Warm and cool readings flip with adjacency.** The same emerald `#1a3a2e` next to brass reads warmer; next to retro purple it reads cooler. Plan for both readings.

### Warm vs. cool palettes

Munsell's color notation gives a defensible vocabulary for warm/cool: hue is one of the system's three independent dimensions, alongside *value* (lightness, 0-10) and *chroma* (saturation) (per Munsell Color Company, "How Color Notation Works"). Warm (red/orange/yellow) and cool (blue/green/violet) are conventional groupings on the hue ring. Pantone organizes the same intuition through named library colors keyed to physical pigment swatches and *"allows different manufacturers in different locations to refer to the Pantone system to make sure colors match"* (per Wikipedia, "Pantone" article, summarizing PMS purpose).

For the cafe: emerald `#1a3a2e` is a cool dominant; walnut and brass are warm secondaries; retro purple `#3d2449` is a cool-leaning accent. Amber 2200-2400K lighting (see `lighting.md`) shifts the warm channel up and reads the emerald slightly less saturated — this is intentional speakeasy-mood behavior.

## Practical Blender mapping

The Blender Principled BSDF *"combines multiple layers into a single easy-to-use node … based on the OpenPBR Surface shading model, and provides parameters compatible with similar PBR shaders found in other software, such as the Disney and Standard Surface models. Image textures painted or baked from software like Substance Painter may be directly linked to the corresponding input in this shader"* (per the Blender Manual, Principled BSDF page, summarized via search-result excerpt because the manual host returned 403 to direct WebFetch at fetch time). The most-used inputs:

| Principled BSDF input | Real-world meaning | Default | Source |
|---|---|---|---|
| **Base Color** | Diffuse albedo (dielectrics) or specular tint (metals). | — | (per Blender Manual, Principled BSDF — "the inherent color of the material"; default per `wdas/brdf` Disney reference) |
| **Metallic** | 0 = dielectric (insulator); 1 = conductor. Blend only for transitions like worn paint over steel. | 0 | (per `wdas/brdf` Disney reference, range 0-1) |
| **Roughness** | Microfacet smoothness; 0 = mirror, 1 = matte. | 0.5 | (per `wdas/brdf` Disney reference, range 0-1, default 0.5) |
| **IOR** | Index of refraction. 1.45 = glass / typical dielectric; affects Fresnel. | 1.45 | (per Blender Manual, Principled BSDF — IOR input) |
| **Specular IOR Level / Specular** | Multiplier on dielectric F0. Default 0.5 maps to ~4% reflectance at 1.45 IOR. Leave at 0.5 unless faking a non-1.45 dielectric. | 0.5 | (per `wdas/brdf` Disney reference, `specular` 0-1 default 0.5) |
| **Coat** (clearcoat) | Thin glossy layer over the base; for car paint, lacquered wood, gloss tile. Default 0. | 0 | (per `wdas/brdf` Disney reference, `clearcoat` 0-1 default 0) |
| **Sheen** | Soft grazing-angle response; for fabrics, dust, velvet. Default 0. | 0 | (per `wdas/brdf` Disney reference, `sheen` 0-1 default 0) |
| **Subsurface** | Light penetrating and re-emerging — skin, wax, marble, thick fabric. Default 0. | 0 | (per `wdas/brdf` Disney reference, `subsurface` 0-1 default 0) |

Notes:

- Connect texture maps to **Base Color** (sRGB color space) and to **Roughness** / **Metallic** / **Normal** (Non-Color Data color space). This matches the glTF metal-roughness convention above.
- Do NOT plug an ORM texture's RGB directly into one input. Use a **Separate Color** node and route R → Ambient Occlusion (multiply with Base Color or use AO socket if exposed), G → Roughness, B → Metallic (per glTF 2.0 channel layout cited above).

## Worked examples

### Example 1 — Walnut SPC floor (cafe v2)

- **Base Color**: walnut hex `#4a3020` (sRGB ≈ 0.18, 0.12, 0.07 — in the 0.05–0.95 dielectric envelope).
- **Metallic**: 0 (dielectric).
- **Roughness**: 0.65 (raw-feel wood, per the wood-raw band above).
- **Specular IOR Level**: 0.5 (default).
- **Sheen**: 0.
- **Coat**: 0 (an oiled SPC plank reads matte; if you add a sealed gloss finish, set Coat 0.2–0.4 with Coat Roughness 0.15).

### Example 2 — Brushed brass bar fitting (cafe v2)

- **Base Color**: brass hex `#b08d57` (sRGB ≈ 0.69, 0.55, 0.34 — metal albedo, full color from base).
- **Metallic**: 1 (conductor).
- **Roughness**: 0.30 (brushed, not polished).
- **Anisotropy**: 0.4–0.6 if exposing Disney-style anisotropy (Blender's anisotropic input, per Disney `anisotropic` 0-1 default 0).
- Rotate anisotropy axis to match the brushing direction.

## Common mistakes

1. **Untextured Principled BSDF on every wall.** A single flat color with default 0.5 roughness reads "video-game prop" instantly. Add a roughness map (even a low-amplitude noise) to break up specular highlights — this is the perceptual cue from microfacet theory (per LearnOpenGL — PBR/Theory, "Microfacet model").
2. **Metallic > 0 on a non-metal.** Setting Metallic to 0.3 on "shiny plastic" violates the metal-or-not binary the Disney model is built around. For shiny plastic: Metallic 0, Roughness 0.15, optionally Coat 0.2 (per `wdas/brdf` Disney reference — `metallic` is a 0-1 *blend* but the model is calibrated for the endpoints).
3. **Pure black or pure white base color on a wall.** sRGB `#000000` or `#FFFFFF` is not a real-world dielectric reflectance. Stay in roughly 0.05–0.95 per channel (per Blender community guidance summarizing the Blender manual; floor/ceiling values are convention).
4. **Saturated 100% accent on a 60% surface.** A high-chroma color used as the *dominant* paint will read as a child's playroom regardless of palette intent. Reserve the highest-chroma color for the 10% accent, and keep purple visible area under 8% per the locked v2 plan (this chapter's recommendation; cafe-specific not a general PBR rule).

## See also

- `lighting.md` — color temperature interaction with materials (amber 2200–2400K shifts perceived saturation of cool colors like emerald).
- `styling.md` — surface composition and how to distribute the 60-30-10 split across actual furniture.
- `render-output.md` — color management at the render pipeline (sRGB vs. Filmic vs. AgX view transforms change what your authored albedo looks like in the final image).
