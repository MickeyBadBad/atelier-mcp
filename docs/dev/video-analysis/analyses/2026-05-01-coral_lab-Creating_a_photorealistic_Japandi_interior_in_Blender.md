# Video Analysis: How to Create a Photorealistic Interior in Blender - Japandi Design

## Source
- URL: https://www.youtube.com/watch?v=Yf9jAlmxEYM
- Channel: coral lab
- Published: 2024-04-22
- Length: 12:14
- Topic: Creating a photorealistic Japandi interior in Blender
- Tutorial style: step-by-step

## TL;DR (5 sentences max)

The creator builds a high-quality Japandi-style living room from a basic cube model to the final render. The target output quality is high photorealism, utilizing Cycles and physically based material principles. The headline technique revolves around using 4 calibration spheres (black, gray, white, chrome) to set accurate HDRI lighting before applying scene materials. The workflow emphasizes efficient texturing, such as using Light Path nodes to remove shadows from sheer curtains and the Magic UV add-on for real-world texture scaling. The final outcome is a well-lit, physically accurate set of interior renders.

## Project shape

- Project type: residential_apartment
- Style closest match: japanese-wabi-sabi
- Final output: view-set
- Overall finish quality: production-photoreal

## Settings extracted (numeric — be exact)

### Render

- Engine: Cycles
- Samples (visible value): 1024
- Adaptive sampling: on, threshold: 0.0100
- Light Tree: (not shown in video)
- Denoiser: OpenImageDenoise
- View transform: AgX
- Look: None
- Resolution: 1000 × 1250
- Render time mentioned: (not shown in video)

### Lighting

- Fixture types observed: hdri
- Number of distinct lights in scene: 1
- Layered model used: ambient-only
- Kelvin values seen on UI: (not shown in video)
- Colors set as RGB instead of Kelvin: yes
- HDRI used: kloppenheim_06_puresky_8k.hdr
- HDRI strength: 5.000
- Sun strength: (not shown in video)

### Camera

- Focal length: 50
- Sensor width: 36
- Camera height (z): 1.033
- Lens shift X / Y: 0.000 / 0.000
- DOF: off
- Clip Start: 0.1 m

### Materials & shading

- Principled BSDF only: no
- Texture sources observed: PolyHaven
- Roughness ranges per category visible:
  - Walls: 0.500
  - Wood floor: (not visible)
  - Metals: (not shown in video)
  - Fabrics: 0.500
  - Glass / clear: (not shown in video)
- Bump / normal map intensity tweaks observed: Normal map strength set to 1.000 for the floor. Displacement node used on the armchair fabric with a scale of 0.020.
- Notable shader graph patterns:
  - Mix Shader combining Transparent BSDF via Light Path (Is Shadow Ray) for shadow-less curtains.
  - Mix Color node in Overlay mode to tint black-and-white textures for the armchair.
  - RGB Curves node applied to the base color texture of the floor to increase contrast.
  - Translucent BSDF mixed with Principled BSDF for the paper lamp material.

### Composition / styling

- Prop density (subjective, 1-5): 2
- Texture variation per surface: 2
- Negative space estimate: 60% bare
- Vignette anchor types observed:
  - Large pendant paper lamp top-center
  - Armchair and side table mid-ground
  - Large dark artwork on the back wall
- Furniture sources: (not shown in video)

### Post-processing (compositing or external)

- In-Blender compositor used: no
- Color grading nodes: (not shown in video)
- Glare / bloom: no
- Vignette in compositor: no
- External program used (Photoshop, Lightroom, etc.): no

## Workflow sequence (chronological)

In the order the creator works:

1. Model the basic room shell from a default cube.
2. Set render engine to Cycles and resolution to 1000x1250.
3. Import four exposure calibration spheres (black, gray, white, chrome).
4. Apply a basic white material to the walls and ceiling.
5. Add an HDRI (`kloppenheim_06_puresky_8k`) and adjust strength to correctly expose the spheres.
6. Create the wood floor material, using the Magic UV add-on to manually scale the planks to exactly 30cm.
7. Import window frames and curtains.
8. Create a custom shadow-less shader for the curtains using a Light Path node.
9. Import and place the main furniture (sofa, armchair, tables) to establish the composition.
10. Tweak HDRI rotation to finalize lighting direction.
11. Add a second camera angle.
12. Create the wood wall panel material using a normal map and hue/saturation adjustments.
13. Create the sherpa fabric material with displacement for the armchair.
14. Create the translucent paper material for the pendant lamp.

## Photorealism techniques (the "secret sauce")

- Calibration spheres: Using 4 reference spheres (black, gray, white, chrome) to objectively tune the HDRI exposure by eye, solving the problem of over- or under-exposed interior renders.
- Shadow-less curtains: Mixing a Transparent BSDF via a Light Path (Is Shadow Ray) node to prevent curtains from blocking ambient light, solving the problem of unnaturally dark interiors without sacrificing visible curtain geometry.
- Exact UV scaling: Using the Magic UV add-on to enforce real-world plank sizes (30cm) on the floor texture, solving the problem of inaccurate scale breaking the illusion of realism.
- Physical displacement for fabrics: Using a displacement node mapped to object space for the sherpa armchair, solving the problem of perfectly smooth silhouettes on fluffy materials.

## Common mistakes the creator calls out

- (not shown in video)

## Direct quotes worth preserving

> "the idea is to have an exposure while the white ball is white and the black is enough black... you can play a little bit with this but it's just something that you have to decide by eye"

> "the trick here is that the curtain is not provoking any kind of shadow so I'm using the mix Shader... so I don't have any kind of Shadows"

> "having a translucent Shader here it does the trick because it really adds some interesting details to it"

## Time estimate (if visible)

- (not shown in video)

## Deltas vs Atelier

### What they do that Atelier already supports

- HDRI lighting setup: encoded in `lighting.md`
- Translucent materials for lampshades: encoded in `materials.md`
- Use of AgX view transform: encoded in `render_settings.md`

### What they do that Atelier does NOT yet support

- **Exposure Calibration Spheres** — should be added to: `lighting.md` as `Use 4 calibration spheres (black, gray, white, chrome) to visually tune HDRI exposure before applying room materials.`
- **Shadow-ray disabling for sheer curtains** — should be added to: `materials.md` as `Use Light Path (Is Shadow Ray) mixed with Transparent BSDF on sheer curtains to prevent harsh shadow casting.`
- **Real-world texture scaling via Magic UV** — should be added to: `materials.md` as `Enforce exact real-world dimensions for floor planks using physical UV scaling techniques.`
- **Mix Color (Overlay) for quick texture adjustments** — should be added to: `materials.md` as `Use a Mix Color node set to Overlay to non-destructively tint or adjust the saturation of grayscale textures.`

### What conflicts with our handbook

- (not shown in video)

## Recommended Atelier project changes (concrete diffs)

- ADD-RULE in `docs/handbook/lighting.md`: "Use 4 calibration spheres (black, gray, white, chrome) to visually tune HDRI exposure before applying room materials."
- ADD-RULE in `docs/handbook/materials.md`: "For sheer curtains, use a Light Path (Is Shadow Ray) node mixed with a Transparent BSDF to disable shadow casting and improve interior light propagation."
- ADD-RULE in `docs/handbook/materials.md`: "Ensure floor textures match physical world dimensions (e.g., 30cm planks) using exact UV scaling rather than visual approximation."
- ADD-RULE in `docs/handbook/materials.md`: "Use Mix Color nodes set to 'Overlay' to tint or adjust the saturation of grayscale textures non-destructively."
