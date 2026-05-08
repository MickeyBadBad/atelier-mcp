# Render Output and View Transforms

> Sources: Blender Manual (5.1 / latest) - Color Management, Cycles Sampling, EEVEE Next Sampling, Packed Data; Blender Developer Documentation 4.0 - Color Management release notes; Troy Sobotka - filmic-blender README and AgX repository; ACES Central; HomeJab "Step-by-Step Guide to Bracketing Interiors"; PropertyPixel "HDR Real Estate Photography: Bracketing Guide"; Esoft "Mastering HDR Photography Through Bracketing"; the workflow spec at `docs/dev/specs/2026-04-29-interior-design-workflow-design.md` (Quality Gate #5, #6, #9).
> Last updated: 2026-04-29

## Purpose

This chapter is the source of truth for render-side decisions on interior shots: which view transform to apply, how many samples to fire in Cycles vs EEVEE Next, what exposure brackets a hero shot needs, what view set to deliver, and why every handoff `.blend` must arrive with textures packed. The downstream consumer is the AI agent that calls `mcp__blender__render_image` / `mcp__blender__quick_export` and explains its choices to a non-designer user.

## View transform: AgX is the default

Set the **View Transform** to **AgX** for every interior render unless there is a specific reason to override. AgX is Blender's default since 4.0 and replaces Filmic in new files (per Blender Developer Documentation, *Release Notes 4.0 - Color Management*, surfaced via the Blender Manual: "The AgX view transform has been added, and replaces Filmic as the default in new files. This view transform provides better color handling in over-exposed areas compared to Filmic. In particular bright colors go towards white, similar to real cameras"). The Blender Manual *Color Management* page describes AgX as "a tone mapping transform that improves on Filmic, giving more photorealistic results", offering "16.5 stops of dynamic range" and desaturating "highly exposed colors to mimic film's natural response to light" (per Blender Manual *Color Management*, Latest, View Transform section).

Available looks within AgX (Base / Punchy / Greyscale / etc.) are stylistic — Base is the neutral default, Punchy adds contrast and saturation to mimic a finished commercial photograph (per Blender Manual *Color Management*, Latest, Look section). For interior hero shots in this codebase, prefer **AgX Base** unless the brief explicitly calls for a "punchy" commercial look.

### Why not Standard sRGB

Do not render hero shots with the **Standard** view transform. Standard is the non-tone-mapped baseline — it exists "to display the viewport in solid mode and to show colors in color pickers" (per Blender Manual *Color Management* / *Displays and Views*, Latest), not for finished pictures. Troy Sobotka, who authored both Filmic and AgX, is direct on this point: the sRGB OETF view transform "Should be avoided at all costs for CGI work" because the sRGB transfer functions "were designed to describe an aspect of device response and never for rendering" (per Troy Sobotka, *filmic-blender* README, GitHub `sobotka/filmic-blender`).

Concretely, an interior with bright window light or amber 2200 K bulbs (the speakeasy palette this project locks in) will clip pure-channel highlights to neon primaries under Standard sRGB, then snap into ugly hue rotations as the brightest areas blow out. AgX preserves the gradient by desaturating extreme highlights toward white in a film-like way (per *AgX in Blender 4.0*, Evermotion tutorial; corroborated by the CGCookie post *The Secret to Rendering Vibrant Colors with AgX in Blender* which describes AgX's behavior as "what high-end cinema cameras do to capture as much data as possible" and explicitly frames the desaturation of highlights as "an important feature and not a bug").

### Filmic as fallback

**Filmic** remains a valid fallback when an existing scene was authored against it and shots already match. The Blender Manual notes that Filmic "can be useful to give the renders a particular look, e.g. as if they have been printed on real camera film" (per Blender Manual *Color Management*, Latest). Sobotka's filmic-blender README presents it as "a closer-to-photorealistic view transform for your renders" delivering "significant dynamic range and lighting capabilities" (per Troy Sobotka, *filmic-blender* README).

If you must render an old scene that was lit and graded against Filmic, keep Filmic — switching transforms after-the-fact will shift the white point and saturation of every material. New scenes use AgX. **ACES** (the *ACES 2.0* view transform now bundled in Blender's standard config) is appropriate only when the deliverable feeds into a downstream ACES pipeline — e.g. a film-VFX vendor handoff (per Blender Manual *Color Management*, Latest; ACES Central defines ACES as "a global standard for interchanging digital image files, managing color workflows and creating masters for delivery and archiving").

This is enforced by **Quality Gate #5** in the workflow spec: "View transform = AgX (fallback Filmic). Auto-fix + notify." (per workflow spec `2026-04-29-interior-design-workflow-design.md`, Quality Gates §, gate #5, severity 🔴 Hard).

## Sample-count guidance

The Blender Manual defines two knobs that matter for interior renders. For Cycles: **Render Samples** is "the number of paths to trace per pixel in the final render. A higher number results in a cleaner image at the cost of a longer render time" and **Viewport Samples** is "the number of paths to trace per pixel in the 3D Viewport (when using the Rendered shading mode)" (per Blender Manual *Cycles - Sampling*, Latest). For EEVEE Next: **Render samples** is "the number of samples to use in the final render" and **Viewport samples** is "the number of samples to use in the 3D Viewport" — anti-aliasing is sample-driven via Temporal Anti-Aliasing, so "the more samples the more aliasing is reduced at the cost of performance" (per Blender Manual *EEVEE - Sampling*, Latest).

The Blender Manual itself does not publish prescriptive sample counts for "interior render" — it describes the trade-off. The values below are the project's defaults, calibrated against the trade-off the manual states and against **Quality Gate #6** in the workflow spec which defines minimum thresholds the gate will warn on:

| Render mode | Cycles samples | EEVEE Next samples | Source |
|---|---|---|---|
| Exploration / preview | ≥ 64 | ≥ 32 | Workflow spec gate #6 minimums (per workflow spec, Quality Gates §, gate #6 🟡); the manual notes that lower sample counts trade noise against time (per Blender Manual *Cycles - Sampling*, Render Samples) |
| Hero | ≥ 512 | ≥ 128 | Workflow spec gate #6 minimums for hero (per workflow spec, gate #6); aligns with the manual's "higher number results in a cleaner image" (per Blender Manual *Cycles - Sampling*) |
| Construction-grade / archive | ≥ 1024 | ≥ 256 | Project default for handoff renders that get printed at A3+ — extends the gate-#6 hero floor by one step. The Blender Manual leaves this calibration to the artist (per Blender Manual *Cycles - Sampling*, Render Samples description) |

When the noise budget is tight, enable **Adaptive Sampling**: "If the Noise Threshold checkbox is enabled, Cycles will use adaptive sampling, cutting short the sampling process in areas that have become less noisy than the specified threshold value" (per Blender Manual *Cycles - Sampling*, Adaptive Sampling). Use the default **Min Samples** of 0, which lets "Cycles automatically pick a value determined by the Noise Threshold" (per Blender Manual *Cycles - Sampling*, Min Samples). Always pair high-sample Cycles renders with the OpenImageDenoise denoiser for hero shots — sample count and denoising are complementary, not substitutes.

For EEVEE Next, raytracing samples and screen-space samples are separate knobs from main sampling and increase quality "at the cost of more noise" trade-offs of their own (per Blender Manual *EEVEE - Raytracing*, Latest). Treat the EEVEE numbers in the table as a floor for **TAA passes**; if raytraced reflections look noisy, raise the raytracing settings, not the main sample count.

## Denoising (cross-tutorial consensus)

For interior renders, **OpenImageDenoise** is the de-facto standard denoiser (4 of 5 production photoreal interior tutorials surveyed in synthesis Round 2 use it: coral lab, art_of_3d_rendering, noel_3d, plus the Round 1 baseline; rileyb3d uses **OptiX** as an NVIDIA-accelerated alternative). The Blender Manual documents both; OIDN is preferred for image quality and CPU/GPU portability, OptiX for raw speed on RTX hardware (per Blender Manual *Cycles → Render Settings → Denoising*; cross-tutorial agreement from 4/5 named photoreal interior tutorials surveyed 2026-05).

Pair denoising with adaptive sampling for the best noise/time tradeoff:

| Setting | Value | Rationale |
|---|---|---|
| Denoiser | OpenImageDenoise (default) / OptiX (RTX speed) | Cross-tutorial consensus |
| Adaptive Sampling | On | Cross-tutorial consensus (4/5 surveyed) |
| Noise Threshold | **0.01** | Cross-tutorial consensus — coral lab, art_of_3d, rileyb3d, noel_3d all use 0.01; the Blender Manual recommends "around 0.01" as a starting point for production scenes (per Blender Manual *Cycles → Sampling*; cross-tutorial agreement from 4/5 named photoreal interior tutorials surveyed 2026-05) |
| Min Samples | 0 (Cycles auto-pick) | Per Blender Manual default |

The 0.01 noise threshold means Cycles stops sampling pixels once their estimated noise drops below 1% of the pixel's value. Going lower (0.001) gives slightly cleaner output but rarely worth the render time on a denoised hero render; going higher (0.1) leaves visible noise that even denoising won't fully clean.

## Exposure bracketing

Hero shots ship as a 3-frame bracket: **-1, 0, +1 stops**. The 0-stop frame is the canonical render and goes into the deck; the -1 and +1 frames document highlight and shadow latitude so the user can pick a different mood without re-rendering.

This convention mirrors real-estate / architectural photography practice. PropertyPixel's *HDR Real Estate Photography: Bracketing Guide* lists "5 exposures under the shutter speed of -2, -1, 0, +1, +2" or the conservative "3 exposures: -2, 0, +2" as standard, where "0 presents the correctly exposed photo" (per PropertyPixel, *HDR Bracketing Guide*). HomeJab's *Step-by-Step Guide to Bracketing Interiors* notes that "most architectural scenes require at least three exposures" and that interior bracketing is "essential to balance interior and exterior light, ensuring that details in shadows are visible while windows are not blown out" (per HomeJab, *Bracketing Interiors*). Esoft's *Mastering HDR Photography Through Bracketing* corroborates the 3-7 exposure 1-2-stop range as the professional norm (per Esoft, *Mastering HDR Photography Through Bracketing*). See `camera.md` for the deeper architectural-photography citation chain (ASMP, McGrath).

In Blender this is a one-line change to **Render Properties › Color Management › Exposure**: render at +0, then -1.0, then +1.0, saving each output to `renders/<zone>/<shot>_-1.png`, `_0.png`, `_+1.png`. Do **not** bracket by changing light intensity — exposure is a post-transform display knob (per Blender Manual *Color Management*, Latest, Exposure).

## Compositor finishing pass (cross-tutorial consensus)

Interior renders ship with an in-Blender compositor pass for grade and bloom — surveyed in **3 of 5** production photoreal interior tutorials (art_of_3d_rendering, noel_3d, rileyb3d use the Blender compositor; nuno_silva does the equivalent in Lumion + Photoshop; only coral_lab ships raw render with no comp). The Blender Manual frames the compositor as "post-processing the rendered image" via "compositing nodes ... operations performed sequentially" (per Blender Manual *Compositing*, Latest, Introduction; cross-tutorial agreement from 3/5 named photoreal interior tutorials surveyed 2026-05).

### Glare node — bloom and streaks

Use the **Glare** node to add light-bleed effects that real cinema cameras and architectural lenses produce. Choose the mode by intent:

- **Streaks** — anamorphic / star-shaped flare from highlights. Used by art_of_3d_rendering for the speakeasy / cinematic look. Most aggressive; reads as "stylized photography".
- **Fog Glow** — soft halo around bright sources. Used by noel_3d for warm-luxury interior lighting. Subtle; reads as "atmospheric haze in a lit room".
- **Bloom / Ghosts** — brighter sources spread; ghost reflections of internal lens elements. Used selectively for sci-fi / film-look pieces.

The Blender Manual notes Glare "simulates optical effects in a camera lens" and lists the Streaks / Fog Glow / Bloom / Ghosts modes (per Blender Manual *Compositing → Filter → Glare Node*, Latest). Mode is the single biggest aesthetic decision; **Threshold** (which highlights bloom) is the secondary tunable. Defaults for this codebase: Fog Glow at threshold 1.0 for unflared interiors; Streaks at threshold 1.5 for cinematic. **Cross-tutorial consensus: 2/5 surveyed name-checked Glare directly** (art_of_3d Streaks + noel_3d Fog Glow), with a 3rd corroborating use in nuno_silva's external pipeline (Lumion bloom + lens flares).

### Color grading nodes

After the Glare pass, color grade with one of:

- **Color Balance** node — three-way grade (Lift / Gamma / Gain or Offset / Power / Slope). Used by art_of_3d_rendering AND noel_3d. The most common interior-render grade tool.
- **RGB Curves** — per-channel tone shaping. art_of_3d_rendering pairs it with Color Balance.
- **LUT** (Color Lookup Table via the *Color Lookup* compositor node) — applies a preset look from a `.cube` file. nuno_silva uses one in the Lumion pipeline equivalent.

The Blender Manual describes Color Balance as offering "Lift Gamma Gain or ASC-CDL controls" for non-destructive color grading (per Blender Manual *Compositing → Color → Color Balance Node*, Latest). Default starting point for the codebase's locked speakeasy palette: Color Balance with Gamma 1.0, then nudge Lift toward warm neutral (≈ R 0.5 / G 0.5 / B 0.45) and Gain toward cool highlights (≈ R 1.0 / G 1.0 / B 1.05). **Cross-tutorial consensus: 2/5 use Color Balance specifically** (art_of_3d + noel_3d); 3/5 use compositor color grading in some form.

### Vignette

A subtle radial darkening at the frame edges focuses attention on the room's negative-space anchor. Build via a Mix node: rendered image + radial gradient mask + Multiply blend at ≈ 85% factor. The Blender Manual covers the underlying Mix node (per Blender Manual *Compositing → Color → Mix Node*, Latest). A vignette is typically a **5-10%** darkening at the edges, not 30%; heavier vignettes read as Instagram-cheap rather than architectural-photography. **Cross-tutorial consensus: 2/5** (art_of_3d compositor-vignette via Mix-node mask + nuno_silva external-pipeline vignette via Lumion).

### Lens Distortion node — dispersion + barrel together (cross-tutorial consensus)

A single Blender compositor node — **`Lens Distortion`** — handles both **chromatic aberration** (color fringing on high-contrast edges) and **barrel / pincushion warping** (subtle geometric curvature). Two pending single-source items from Rounds 2-3 (art_of_3d's Lens Distortion node use + nuno_silva's chromatic aberration use) merge here: the CGi Jutsu tutorial "Chromatic Aberration and Lens Distortion in Compositing!" (surveyed 2026-05) clarifies they are not two separate setups — they are two parameters on one node.

Concrete parameters and ranges:

- **Dispersion** — chromatic aberration. Real values: **0.01 - 0.03**. CGi Jutsu specifies **0.02** as the production sweet spot. Above 0.03 the color fringing reads as "video glitch" not "real lens" (per CGi Jutsu, "Don't over-use this imperfection, because it starts hurting the viewer's eyes after a while").
- **Distort** — barrel (positive) or pincushion (negative) curvature. Real values: **0.01 - 0.02**. CGi Jutsu specifies **0.01**. Above 0.05 reads as "GoPro fisheye" not architectural lens (per Blender Manual *Compositing → Lens Distortion Node*, Latest, which describes Distort as the "barrel/pincushion warp" parameter).
- **Fit** checkbox — **always enable**. Without it, positive Distort values leave black borders in the corners. The Manual confirms: "Scales the image so black areas are not visible (only works for positive distortion)" (per Blender Manual *Compositing → Lens Distortion Node*, Latest, Fit option).
- **Jitter** checkbox — leave OFF for hero shots. The Manual notes Jitter "adds jitter to the distortion — faster, but noisier" (per Blender Manual, Latest); useful for animation previews, not stills.

The **Lens Distortion node belongs after the color grade** in the compositor chain — applying the lens artifact AFTER tone is established matches how a real photograph is captured (the lens is between the scene and the sensor, before any grading). Round 6 surveyed agreement: 2 of 8 surveyed photoreal interior tutorials apply this in some form (art_of_3d_rendering uses Lens Distortion in its compositor chain alongside Glare and Color Balance; CGi Jutsu walks the same node with explicit recommended values; nuno_silva applies the chromatic-aberration half via Lumion + Photoshop — equivalent effect, different toolchain).

### Order of operations (revised)

The standard compositor chain for a hero interior render is:

```
Render Layers  →  Glare (Fog Glow or Streaks)
                     →  Color Balance (Lift / Gamma / Gain)
                          →  RGB Curves (optional fine tone-shaping)
                               →  Lens Distortion (Dispersion 0.02 + Distort 0.01, Fit ON)
                                    →  Vignette (Mix node + radial mask, optional)
                                         →  Composite output
```

Glare BEFORE color grade matters: grading on top of bloomed highlights gives consistent spillover; grading first then blooming the graded result tends to over-saturate the bloom (per Blender Manual *Compositing → Operations performed sequentially*, Latest, Introduction). Lens Distortion AFTER grade matters for the same reason — the lens artifact is a sensor-side effect, last in the optical path.

### When to skip the compositor

Construction-grade orthographic elevations and material reference renders — the deliverables that go to the contractor sheet, not the client deck — ship raw. No Glare, no grade, no vignette. The point of those renders is dimensional and chromatic literalness, not mood. This pairs with the **Standard view transform** exception called out in §"View set composition" item 5 (orthographic plans).

## Cryptomatte as a routing mask for selective post-effects (cross-tutorial consensus)

Beyond the global compositor finishing pass (Glare → grade → Lens Distortion → vignette), there's a second architectural pattern surveyed across photoreal tutorials: **use a Cryptomatte node's matte output as the factor input on a Mix node that selectively applies a post-effect to specific objects.** The pattern is the same regardless of which effect you gate; only the effect changes. Two of nine surveyed tutorials apply this pattern explicitly:

| Source | Cryptomatte gates which effect | Goal |
|---|---|---|
| rileyb3d "Optimize Interior Renderings in Blender Cycles" (Round 2) | **Denoising** — different denoise levels for walls vs. complex objects | Reduce flat-wall over-smoothing while keeping detail noise on furniture |
| Francesco Milanese "CryptoMatte for Masks with Motion Blur" (Round 7) | **Glare** — Glare streaks applied only to specific moving objects | Prevent background highlights from polluting motion-blur streaks |

**Generalized recipe** (the architectural pattern, not specific to either effect):

```
Render Layers → Cryptomatte (Object/Material/Asset pass)
                  ↓ matte output
               Mix node (Factor input)
                  ├─ image input 1: render WITHOUT the effect
                  └─ image input 2: render WITH the effect (denoise / glare / color-correct / sharpen / blur)
                  ↓
                Composite output
```

Concrete steps:
1. **Enable a Cryptomatte pass** in View Layer properties → Passes → Cryptomatte. Choose Object (per-object masks), Material (per-material), or Asset (per-asset-group), depending on grouping needs (per Blender Manual *Render Layer → Cryptomatte Passes*, Latest).
2. **Set output to Multi-layer OpenEXR** so the Cryptomatte data is preserved in the rendered file (per Blendergrid, *From Blender to Natron with Cryptomattes and AOVs*; corroborated by Francesco Milanese's tutorial).
3. **Add a Cryptomatte node in the Compositor**, connect render image to its image input, click the "Pick" button + eyedropper-click the object(s) you want masked (per Blender Manual *Compositing → Mask → Cryptomatte Node*, Latest).
4. **Route the matte output to a Mix node's Factor input.** The two Mix inputs receive (a) the unprocessed render and (b) a processed version. Where the Cryptomatte mask is 1.0, the processed version shows; where it's 0.0, the unprocessed shows; intermediate values blend (handles motion blur and AA cleanly because Cryptomatte stores coverage data, not binary masks — per Francesco Milanese vs. legacy ID Mask comparison).

**When to use this pattern over a global effect**:
- The effect is too aggressive when applied uniformly (rileyb3d's denoising case — flat walls over-smooth and lose subtle texture variation)
- The effect should only apply to specific subjects (Francesco Milanese's glare case — background lights would otherwise pollute the motion-blur streaks)
- You need to preview a localized post-pass change without re-rendering (the artisticrender.com workflow advantage of "change objects/materials instead of re-rendering")

**Cryptomatte stores coverage, not binary masks** — the `Pick` output divides scene elements by colors assigned automatically; the `Matte` output is a continuous-value mask that handles depth of field, motion blur, and anti-aliasing on edges (per Blender Manual *Cryptomatte Node*, Latest; corroborated by Francesco Milanese's explicit comparison against legacy ID Mask which is binary).

**Cross-tutorial consensus**: 2 of 9 surveyed (rileyb3d + Francesco Milanese). Note: the **specific** rileyb3d application (Cryptomatte → mix → DIFFERENT denoising for different objects) is single-source within this pattern; the **architectural pattern** itself is corroborated. If you want to apply the pattern to denoising specifically, treat the technique as production-ready but be aware it's an inference from the corroborated pattern, not from two tutorials applying it identically.

## View set composition

A complete hero delivery for a single zone is **5 shots**:

1. **Hero (3-quarter)** — primary marketing shot. ~24-28 mm, eye-level, framed to show two walls + ceiling + floor with the focal feature on the third-line. Cross-ref `camera.md` §"Lens choice".
2. **Corner shot** — 35-50 mm, taken from a corner showing the longer diagonal of the room. Sells volume and depth.
3. **Eye-level cross-room** — 28-35 mm, camera at 1.5-1.6 m, parallel to the floor (no upward / downward tilt) so verticals stay vertical. Reads as a documentary-style record of the space.
4. **Detail crop** — 70 mm or longer, isolating a single material moment (a hardware element, a wall-mounted artwork, a bar-edge inlay, a focal-wall texture). Per `camera.md`: "70 mm and longer for detail crops — 'isolating specific architectural details' and 'compress[ing] perspective'."
5. **Plan / elevation** — top-down orthographic for plan, straight-on orthographic for each elevation. Use Blender's **Orthographic** camera mode and set ortho scale to room dimensions. These are deliverables for the contractor, not marketing — render them with Standard or Raw view transform (the only legitimate use of Standard) so dimensions and colors read literally on the printed sheet.

For a full multi-zone project, that is 5 shots per zone (e.g. a 6-zone job → 30 final renders), plus exposure brackets where the brief calls for them.

## Texture packing for handoff

Every `.blend` that leaves this machine — to the contractor, to the client, to a render farm — must have its textures packed. The Blender Manual explains the mechanism: "Blender has the ability to encapsulate (incorporate) various kinds of data within the blend-file that is normally saved outside of the blend-file. For example, an image texture that is an external image file can be put 'inside' the blend-file via Pack Into blend-file. When the blend-file is saved, a copy of that image file is put inside the blend-file. The blend-file can then be copied or emailed anywhere, and the image texture moves with it" (per Blender Manual *Packed Data*, Latest / Introduction).

Operationally, use **File › External Data › Pack Resources** before saving a final, or pass `pack_textures=True` to `mcp__blender__quick_export` for GLB/FBX/USD deliverables (the GLB format also embeds textures by default). For per-image control, the Manual notes "a single file can be packed by clicking on the little 'gift box' icon to the left of its file-path UI widget" (per Blender Manual *Packed Data*, Latest).

This is enforced by **Quality Gate #9** in the workflow spec: in exploration phases packing is 🔵 Info-only, but on Final renders and Construction Handoff it auto-upgrades to 🔴 Hard — a missing-textures `.blend` will not export (per workflow spec `2026-04-29-interior-design-workflow-design.md`, Quality Gates §, gate #9; Strictness modes §). The reason is concrete: a contractor opening an unpacked `.blend` sees pink-and-black checkerboards everywhere; that is a project-credibility failure, not a technical inconvenience.

## Worked examples

**Example 1 — Hero render of a focal-wall booth zone.** Cycles, AgX Base, 1024 samples (between hero and construction-grade because this is the cover shot for the whole project), Adaptive Sampling on with default Min Samples = 0, OpenImageDenoise enabled. Render at exposure 0, then -1, then +1 to `renders/<zone>/hero_-1.png`, `_0.png`, `_+1.png`. Save the `.blend` with **Pack Resources** ticked.

**Example 2 — Construction elevation of a bar back-wall.** EEVEE Next is fine — no caustics, no GI complexity needed. **Standard** view transform (this is one of the only places it is correct) so material sample colors print at literal sRGB values. Orthographic camera, 256 EEVEE samples, no exposure bracket. Export the `.blend` with `pack_textures=True` plus a PDF of the rendered orthographic for the contractor sheet.

## Common mistakes

1. **Rendering with Standard view transform.** Highlights clip to neon primaries, materials look chromatic-aberration-cheap. Switch to AgX (per Quality Gate #5).
2. **Low-sample noisy hero shot.** 64 samples of Cycles is exploration-grade; pushing it to a client's deck reads as amateur. Hero floor is 512 (per workflow spec gate #6). Pair with OpenImageDenoise.
3. **Unpacked textures in delivered `.blend`.** Pink-and-black checkerboards on the contractor's screen. Always use *File › External Data › Pack Resources* or `quick_export(pack_textures=True)` (per Blender Manual *Packed Data*, Latest).
4. **Bracketing by changing lights instead of Exposure.** Re-rendering with stronger lamps changes the GI bounce; re-rendering with the Color Management Exposure slider does not. Bracket via Exposure (per Blender Manual *Color Management*, Exposure).
5. **Switching view transforms mid-project.** A scene lit and material-tuned against Filmic will shift in white point and saturation when flipped to AgX. Pick the transform at the start of a project and stay with it.

## See also

- `camera.md` — framing, lens choice, ASMP / McGrath citations for the architectural-photography conventions referenced here.
- `lighting.md` — light Kelvin and lux ranges; the speakeasy 2200-2400 K palette is what makes the AgX-vs-Standard difference visible.
- `materials.md` — material color-space settings (sRGB for albedo, Non-Color for roughness / normal / metallic) interact with the view transform on the output side.
