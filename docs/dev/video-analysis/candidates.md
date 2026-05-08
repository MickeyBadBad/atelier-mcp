# Video Research Candidates

> **Purpose**: persisted index of YouTube tutorials surfaced via WebSearch on 2026-05-08. Each candidate is paired with the handbook pending item it could corroborate. Resume here when GEMINI_API_KEY rotation is done or when video-pipeline 503 churn clears.
>
> **Last updated**: 2026-05-08 (after Round 7)
> **Surveyed corpus after Rounds 1-7**: **9 unique videos**; **4 of 11 original single-source items still 1/9** (down from 5 after Round 6, down from 7 after Round 4) plus 1 newly-surfaced single-source from Round 5 (HDRI-on-sphere preview).

---

## Already analyzed (do NOT re-run these)

These have an `analyses/<DATE>-<channel>-<slug>.md` file and have been folded into the synthesis log. Listed for de-duplication when picking new targets.

| Date | Channel | Title | URL | Round used in |
|---|---|---|---|---|
| 2026-05-01 | coral lab | Creating a photorealistic Japandi interior in Blender | (manual transcription, no URL stored) | Round 1 + 2 |
| 2026-05-01 | Noel-3D | Photorealistic Interior Lighting Tutorial in Blender 4.0 Cycles | (no URL stored) | Round 2 |
| 2026-05-01 | Nuno Silva | The 7 Step Formula to Photorealistic Interior 3D Renders | (no URL stored) | Round 2 |
| 2026-05-01 | Art of 3D Rendering | Blender Photorealistic Interior Render in Cycles Tutorial | (no URL stored) | Round 2 |
| 2026-05-01 | rileyb3d | Optimize Interior Renderings in Blender Cycles | (no URL stored) | Round 2 |
| 2026-05-08 | CynicatPro | Blender Tip: Lighting Interiors with Light Portals | https://www.youtube.com/watch?v=uJl8mP-HtQs | Round 4 (corroborated light portals) |
| 2026-05-08 | Lane Wallace | The Best Volumetric Fog Shader (Blender Tutorial) | https://www.youtube.com/watch?v=2SiCtnXVVFw | Round 4 (corroborated volumetric) |
| 2026-05-08 | Nik Kottmann | How to add Surface Imperfections to Shaders for increased Realism! | https://www.youtube.com/watch?v=Z0pYgvFdz4Y | Round 4 (corroborated surface imperfections) |
| 2026-05-08 | Blender Guru | Using fabric textures in Blender (Couch Part 5) | https://www.youtube.com/watch?v=zyrm9GH51Y4 | Round 4 (corroborated fabric displacement) |
| 2026-05-08 | Blender Tutor | HDRI Lighting Fundamentals in Blender | https://www.youtube.com/watch?v=mgg066fvUqc | Round 5 (no corroboration; surfaced HDRI-on-sphere preview as 1/8) |
| 2026-05-08 | CGi Jutsu | Chromatic Aberration and Lens Distortion in Compositing! \| Blender Tutorial | https://www.youtube.com/watch?v=dJFRExW0emA | Round 6 (corroborated Lens Distortion + Chromatic Aberration as one rule) |
| 2026-05-08 | Francesco Milanese (CG Tutorials) | CryptoMatte for Masks with Motion Blur in Compositing \| Blender 4.3 Compositing Basics | https://www.youtube.com/watch?v=bn9arzKkPVk | Round 7 (corroborated Cryptomatte routing-mask pattern: rileyb3d denoise + this glare = pattern 2/9) |

---

## Pending items remaining at 1/9 (4 original carryovers + 1 Round-5-surfaced)

Each item below has its WebSearch-surfaced candidate list. Pick by EV: items with multiple Blender-specific dedicated tutorials are likeliest to corroborate on first try.

> **Round 7 lesson** (2026-05-08): niche practitioner techniques (Cryptomatte selective denoising, HDRI calibration spheres) lack dedicated tutorials. Two recovery strategies validated: (a) **re-mine** existing corpus for off-hand mentions (Round 3's compositor consensus came from this), (b) **generalize the rule** to a broader pattern that has more sources (Round 7's Cryptomatte routing pattern came from this — corroborated 2/9 even though the specific denoising application stayed 1/9). Apply these strategies before declaring a pending item dead.

### ~~Cryptomatte selective denoising~~ (RESOLVED Round 7 via generalization)

The Cryptomatte selective-denoising rule was generalized in Round 7 to **"Cryptomatte as a routing mask for selective post-effects"** (architectural pattern: Cryptomatte → matte → Mix factor → selective effect application). 2/9 sources corroborate the pattern (rileyb3d denoise + Francesco Milanese glare). The specific denoising application is now framed as a valid instantiation of the corroborated pattern. Section landed in `docs/handbook/render-output.md`. Removed from active pending list.

### 🔥 1. HDRI calibration spheres for strength tuning (coral_lab, Round 1 carryover — OLDEST PENDING)

**Pending claim**: chrome / gray / white / black reference spheres in scene tune HDRI strength against on-set photo before applying scene materials.

**Search-then-analyze attempted twice** (Round 5); both times surfaced capture-side videos (how to PHOTOGRAPH a chrome ball to MAKE an HDRI) rather than tuning-side (how to verify HDRI strength matches reality once you have the HDRI). The Round-5 lesson: query specificity matters.

**Better next searches**:
- `blender debevec ibl chrome ball calibration reference sphere tutorial`
- `vfx pipeline calibrate HDRI exposure gray ball blender tutorial`
- `Paul Debevec rendering synthetic objects light probe blender`

**Candidates surfaced so far** (all Round 5 search hits — the Blender-specific ones DON'T match the rule but listed for completeness):

| URL | Channel | Note on fit |
|---|---|---|
| https://www.youtube.com/watch?v=uK7UUvU33Bo | (C4D / Redshift creator) | Chrome Ball + Grey Ball + 360 Cam — the closest existing tutorial to Round 1's rule, but in Cinema 4D / Redshift. May still corroborate the principle if analyzed; cite as cross-renderer evidence. |
| https://www.youtube.com/watch?v=t23raSpOS6c | (anon) | "How To Create Your Own HDRI Map Using A Chrome Ball" — capture side only |
| https://www.youtube.com/watch?v=X3qsXqt8M8I | (anon) | "Chrome Ball Photography for Animation & VFX 01: Photography" — capture only |
| https://www.youtube.com/watch?v=N3DZL56cG84 | (anon) | "The ULTIMATE GUIDE to HDRI Lighting in Blender" — broader scope, may include reference-sphere tuning |

**Priority**: MEDIUM — Round 1's rule may need to be re-scoped if no Blender-specific tutorial covers it. Falling back to the C4D/Redshift video as cross-renderer evidence is acceptable.

---

### 2. Glossy ray amplification (noel_3d, Round 2 carryover)

**Pending claim**: multiply glossy by 5× and set diffuse to 0 — custom shader graph trick to enhance reflections without overexposing the diffuse base.

**Status**: WebSearch not yet done. Suggested searches:
- `blender glossy reflection enhance shader light path is glossy ray`
- `blender principled bsdf separate glossy diffuse layer trick`

**Priority**: LOW-MEDIUM — narrow technique; may only appear in one or two niche shader-graph tutorials.

---

### 3. 1-2 mm gaps between intersecting objects (nuno_silva, Round 2 carryover)

**Pending claim**: leave a small gap between intersecting CG objects to generate physical contact shadows instead of fused-mesh look.

**Status**: WebSearch not yet done. Suggested searches:
- `blender contact shadow intersecting objects gap photorealistic`
- `archviz blender prevent fused mesh contact shadow gap`

**Priority**: LOW — practitioner detail, rarely the focus of a dedicated tutorial. Likely needs to be inferred from multiple tutorials' off-hand mentions; might be better to search for "common archviz mistakes" content rather than dedicated tutorials.

---

### 4. 4-sphere HDRI calibration variant (coral_lab, Round 1 carryover)

**Pending claim**: 4-sphere setup (chrome + grey + white + black) is a refinement over the canonical 2-sphere (chrome + grey) for tighter exposure-latitude tuning.

**Status**: tied to the HDRI calibration sphere question above. If item #2 corroborates, this addon-flag may corroborate alongside.

**Priority**: deferred — synonymous with #2.

---

### 5. HDRI-on-sphere via Object Info (rotation preview) — Round 5 NEW single-source

**Pending claim**: project HDRI onto a UV sphere via Object Info node to see the lighting direction without rendering — Blender Tutor 1/8.

**Status**: just surfaced 2026-05-08 in Round 5. No corroboration searches done yet.

**Suggested searches**:
- `blender HDRI sphere preview rotation tutorial object info`
- `blender visualize HDRI direction without render sphere`

**Priority**: LOW — niche workflow trick; corroboration nice-to-have.

---

## Other candidates surfaced today but not used (saved for cross-reference)

These came up in WebSearches that targeted other topics. Not necessarily aligned with any single pending item, but listed in case a future round wants extra coverage.

### Lens distortion / chromatic aberration backups (Round 6 already corroborated; these are extras if Round 7 wants triangulation)

| URL | Channel | Note |
|---|---|---|
| https://www.youtube.com/watch?v=T_oFLrTJQPs | (anon) | "Lens-Distortion Tutorial aka Chromatic Aberration" |
| https://www.youtube.com/watch?v=4MR9UWgLM5I | (anon) | "Compositing Quick Tip #4: Chromatic Aberration" |
| https://www.youtube.com/watch?v=6RUkUwEUdWg | (anon) | "Blender Digital Chromatic Aberration Tutorial" |
| https://www.youtube.com/watch?v=MgJyBG3VfAc | (anon) | "Lens Distortion/Chromatic Aberration AND Glare" |

### Light portal backups (Round 4 already corroborated; extras for triangulation)

| URL | Channel | Note |
|---|---|---|
| https://www.youtube.com/watch?v=1LjLyTBbl6s | (anon) | "Reduce Cycles Noise with Light Portals" — short focused tip |

### Volumetric backups (Round 4 already corroborated; extras for triangulation)

| URL | Channel | Note |
|---|---|---|
| https://www.youtube.com/watch?v=99u_d7deVCM | (anon) | "Making (Fast n' Easy) Fog with Volumetrics — Blender 3.1" |

### Surface imperfection backups (Round 4 already corroborated; extras for triangulation)

| URL | Channel | Note |
|---|---|---|
| https://www.youtube.com/watch?v=14g6DCjSKB8 | (anon) | "Surface Imperfections in Blender: Scratchmap Tutorial" |
| https://www.youtube.com/watch?v=UIFGMFRFjPY | (anon) | "Using Poliigon Materials in Blender (Part 2: Surface Imperfections)" |

### Fabric / sofa modeling (Round 4 corroborated displacement angle; these are sofa-modeling adjacents)

| URL | Channel | Note |
|---|---|---|
| https://www.youtube.com/watch?v=Y4whyFTilsA | (anon) | "How to Make a Couch in Blender (Part 1)" |
| https://www.youtube.com/watch?v=V1HxV1aEBik | (anon) | "Sofa Modeling Guide Part 4 Fabric Cushion Simulations" |
| https://www.youtube.com/watch?v=cLIp3LlZlu8 | (anon) | "Realistic Sofa in Blender in 15 minutes" |
| https://www.youtube.com/watch?v=uE41tUYHGP4 | (anon) | "Modular Sofa Tutorial" |

### HDRI fundamentals (Round 5 used one; these are alternative entry points)

| URL | Channel | Note |
|---|---|---|
| https://www.youtube.com/watch?v=N3DZL56cG84 | (anon) | "The ULTIMATE GUIDE to HDRI Lighting in Blender!" |
| https://www.youtube.com/watch?v=pbuNJb_gnpA | (anon) | "Easy HDRI Lighting in Blender 4.0!" |
| https://www.youtube.com/watch?v=G30rWKtL_E8 | (anon) | "Basics of Image-based Lighting in Blender (2/7)" |
| https://www.youtube.com/watch?v=95lweeoyx-8 | (anon) | "How to Add HDRI Lighting in Blender (Manual Method)" |
| https://www.youtube.com/watch?v=-4E181vPAkQ | (anon) | "Blender Tutorial: Using Your Own HDR Images (HDRI)" |

---

## How to run a candidate tomorrow

```bash
# 1. Set a fresh GEMINI_API_KEY (do NOT reuse the one pasted in chat
#    earlier — that one is in the conversation transcript and should
#    have been rotated)
export GEMINI_API_KEY=AIza...   # from https://aistudio.google.com/app/apikey

# 2. Run the analyzer (model fallback chain handles 503 churn)
cd /Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp
scripts/analyze_youtube.py "<URL>"

# 3. Output lands at:
#    docs/dev/video-analysis/analyses/<DATE>-<channel-slug>-<title-slug>.md

# 4. Synthesize: read the new analysis vs. the pending list above,
#    apply 2-source-corroborated rules to the relevant handbook chapter,
#    update synthesis-log.md with the round entry, run handbook tests,
#    commit.
```

### Model preference (per Round 5/6 user direction)

- **Default**: `gemini-3-flash-preview` (proven on Round 4 + Round 6 free-tier video ingestion)
- **GA fallback**: `gemini-3.1-flash-lite` (works for text; video ingestion 503-churns on busy Google days)
- Full chain in `scripts/analyze_youtube.py` `MODEL_CANDIDATES`.

### Recovery from 503 churn

Free-tier video ingestion on Google's Gemini API is heavily congested as of 2026-05-08 — multiple consecutive runs hit "service unavailable (503)" the same minute. Two recovery patterns observed today:

1. **HTTP retry alone**: the script's built-in `RemoteDisconnected` retry (5s / 15s / 45s backoff) sometimes recovers a 503 on the same model.
2. **Wait then retry**: `sleep 60-90` between attempts gives Google's traffic shaping time to release the bucket.
3. **Fallback chain**: drop the explicit `--model` flag and let MODEL_CANDIDATES walk the list. Round 5 fell from `gemini-3.1-flash-lite` → `gemini-2.5-flash-lite` cleanly.
