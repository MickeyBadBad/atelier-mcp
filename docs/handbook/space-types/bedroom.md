# Space Type: Bedroom (卧室)

> Sources: Neufert *Architects' Data* (2nd / 4th International English ed., Internet Archive PDF, residential / accommodation chapters); Panero & Zelnik *Human Dimension & Interior Space* (Whitney Library of Design, 1979, residential anthropometric figures); GB 50096-2011 《住宅设计规范》§5.2 / §5.5 / §7.1 (jianbiaoku / soujianzhu reproductions; cross-ref `codes.md`); GB 50034-2013 《建筑照明设计标准》§5.1 Table 5.1.1 (Recolux / Wosen LED / Casyoo summaries; cross-ref `lighting.md`); Layak Architect "Bedroom Dimensions (Master Bedroom Design & Interior Guide)" citing Neufert / Time-Saver / Metric Handbook; Tetto Homes "Guide on Recommended Room Sizes" reproducing Neufert single/double bedroom figures; Sleep Foundation "Bedroom Environment" recommendations.
> Last updated: 2026-04-29

## Purpose

The bedroom (卧室) is the primary sleep and private retreat space in a residential unit — its job is to support uninterrupted sleep, dressing, and (where space allows) reading or quiet work. This chapter is the source of truth for AI agents scaffolding a bedroom: it pins the area envelope, the bed-perimeter clearances, the wardrobe/dresser inventory, the layered lighting recipe (which bottoms out below the living-room floor on purpose), and the camera view set. Downstream consumers are the `interior-discovery-intake` and `interior-plain-language-edit` skills plus the 9-dimension quality gates.

## Typical area range

| Region / context | Range (m²) | Source |
|---|---|---|
| Chinese residential, double bedroom regulatory floor (双人卧室) | ≥ 9 m² usable area | (per GB 50096-2011 §5.2.1 item 1: "双人卧室的使用面积不应小于9㎡"; cross-ref `codes.md` minimum-room-dimensions block) |
| Chinese residential, single bedroom regulatory floor (单人卧室) | ≥ 5 m² usable area | (per GB 50096-2011 §5.2.1 item 2: "单人卧室的使用面积不应小于5㎡") |
| Chinese residential, bedroom doubling as living space (兼起居) | ≥ 12 m² usable area | (per GB 50096-2011 §5.2.1 item 3: "兼起居的卧室使用面积不应小于12㎡") |
| Neufert "single" / "double" separate bedroom recommendations | 7 m² single / 12 m² double | (per Neufert *Architects' Data* accommodation chapter as reproduced on Tetto Homes "Guide on Recommended Room Sizes" — "If the bedroom is separate, the recommended size is 7 m² for a single and 12 m² for a double room") |
| Layak Architect / Neufert standard bedroom | 3000 × 3600 mm = 10.8 m² | (per Layak Architect "Bedroom Dimensions" citing Neufert / Time-Saver / Metric Handbook: "Standard bedroom: 3000 mm × 3600 mm") |
| Layak Architect / Neufert master bedroom | 4200 × 4800 mm ≈ 20.2 m² | (per Layak Architect "Bedroom Dimensions" master-bedroom block citing the same source set) |

GB 50096-2011 §5.5.2 also fixes the **interior net height ≥ 2.40 m** for bedrooms; partial low-area allowed at ≥ 2.10 m provided the low area covers ≤ 1/3 of the usable area (per GB 50096-2011 §5.5.2; cross-ref `codes.md`). When the bedroom area drops below 9 m² (single-bedroom band), drop the dressing/work surfaces from the inventory — there is no bed-perimeter circulation to spare.

## Required clearances

All values are clear distances between finished furniture / wall faces. Cross-referenced with `spatial.md` — keep in sync when editing.

| Clearance | Range (mm) | Source |
|---|---|---|
| Bed long-side → wall (no door arc) | 600–750 | (per Layak Architect "Bedroom Dimensions" citing Neufert / Metric Handbook: "around bed perimeter: 600–750 mm for smooth movement and bed-making"; corroborates Neufert 75 cm bed-to-wall figure summarised on Tetto Homes) |
| Bed foot → opposite wall / wardrobe (operating clearance) | ≥ 1000 | (per Neufert as summarised on Tetto Homes "Guide on Recommended Room Sizes": "1 meter between the end of the bed and the closet"; corroborates Layak Architect wardrobe-front clearance band) |
| Bed making clearance (working strip alongside bed) | 450–600 | (per Layak Architect "Bedroom Dimensions": "Bed clearance for making: 450–600 mm") |
| Single-person walking circulation through bedroom | ≥ 600 | (per Layak Architect / Neufert Metric-Handbook circulation band: "a minimum of 600–750 mm of space is required for one person to move freely"; cross-ref `spatial.md` single-person band) |
| Wardrobe front operating clearance | 900–1200 | (per Layak Architect "Bedroom Dimensions": "Operating clearance: 900–1200 mm minimum in front" of wardrobe) |
| Wardrobe depth (hang rod accommodation) | 600 | (per Layak Architect "Bedroom Dimensions": "Wardrobe depth: 600 mm" — drives a clear floor-plan setback for any wall-hung built-in) |
| Bed height with mattress, top of mattress to floor | 400–650 | (per Layak Architect "Bedroom Dimensions": "Bed height (with mattress): 400–650 mm") |
| Bedside table top height (≈ mattress top) | 450–550 | (per Layak Architect "Bedroom Dimensions": "Bedside table: 450–550 mm" — sized to land within ± 50 mm of the mattress top) |
| Window: floor-area-to-window ratio (daylight) | ≥ 1/7 | (per GB 50096-2011 §7.1.5 mandatory clause: "卧室、起居室（厅）、厨房的采光窗洞口的窗地面积比不应低于1/7"; cross-ref `codes.md`) |
| Bathroom directly above bedroom (vertical stacking) | not allowed | (per GB 50096-2011 §5.4.4 mandatory provision: a bathroom must not sit directly above a bedroom of the unit below — affects multi-storey townhouse layouts; cross-ref `codes.md`) |

Standard bed footprints used for clearance arithmetic: **King 1800 × 2100 mm**, **Queen 1500 × 2050 mm**, **Double 1350 × 2050 mm**, **Single 900 × 2050 mm** (per Layak Architect "Bedroom Dimensions" bed-size table; corroborates Neufert hotel-room bed sizes as summarised in the Layak Architect study-room guide).

## Furniture inventory

### Must-have

- **Bed** sized to occupant count (single / double / queen / king per the table above) — anchors the layout. The bed long side wants the 600–750 mm clear side band on at least one side (per Layak Architect / Neufert clearance rules above).
- **Bedside table** at ± 50 mm of mattress top, one per sleeper for double+ bed (per Layak Architect height band 450–550 mm; common-pair convention from Panero & Zelnik 1979 residential figures).
- **Wardrobe** with 600 mm depth and 900–1200 mm front operating clearance — minimum closed storage for a residential unit; built-in / freestanding handled identically (per Layak Architect "Bedroom Dimensions" wardrobe block).
- **Window with daylight ratio ≥ 1/7** of floor area (per GB 50096-2011 §7.1.5 — code-mandatory, not optional).

### Common

- **Reading / task light at the bedside** — table lamp on the bedside table or a wall sconce above it. Justified by GB 50034-2013 Table 5.1.1 reading-task value of 150 lx vs. 75 lx general (per GB 50034-2013 §5.1 as summarised in Wosen LED standard-lux summary; cross-ref `lighting.md` Maintained-Illuminance table).
- **Dressing table / desk** at 750–800 mm height (dressing) or 750 mm (study) — drops out below the 9 m² double-bedroom floor (per Layak Architect "Bedroom Dimensions": "Study table: 750 mm; Dressing table: 750–800 mm").
- **Full-length mirror** on a wardrobe door or freestanding — typical residential convention; not regulated by GB or Neufert.

### Optional

- **Reading nook / accent chair** at a window — only when usable area exceeds 12 m² (i.e. above the GB 50096-2011 兼起居 threshold). Justified by GB 50034-2013 Table 5.1.1 reading-task 300 lx as a discrete sub-zone target (per GB 50034-2013 §5.1).
- **Blackout window treatment** — Sleep Foundation bedroom-environment guidance: "Light is one of the most important external factors that affect sleep — the room should be as dark as possible during sleep" (per Sleep Foundation "Bedroom Environment" guidance, as summarised in Sleep Foundation "What is the best room temperature and lighting for sleeping?"; specific sleep-research clause not reproduced inline). Drives a 100% blockout curtain or shade rather than a sheer-only treatment.
- **TV opposite the bed** — drop unless the room is ≥ 14 m² and the bed → TV distance reaches the THX 1.2× diagonal viewing band (per `space-types/living-room.md` viewing-distance row citing Wikipedia "Optimum HDTV viewing distance"). Most bedrooms below 12 m² cannot host a TV without compressing the foot-of-bed clearance.

## Lighting layer recipe

| Layer | Target (lx) | Kelvin | Fixture | Source |
|---|---|---|---|---|
| Ambient (general) | 75 lx maintained on a 0.75 m horizontal plane | 2700–3000 K (residential warm-white) | Overhead pendant or recessed downlights; dimmable to ~ 30 % for pre-sleep | (per GB 50034-2013 §5.1 Table 5.1.1 row "卧室 一般活动" 75 lx, 0.75 m horizontal plane, Ra ≥ 80, as summarised in Wosen LED standard-lux summary and Recolux Lighting GB-50034 commentary; cross-ref `lighting.md` residential band 75–150 lx) |
| Task / reading | 150 lx maintained at the reading position | 2700–3000 K | Bedside table lamp or wall sconce on a swing arm | (per GB 50034-2013 §5.1 Table 5.1.1 row "卧室 床头、阅读" 150 lx as summarised in Wosen LED / Recolux summaries; cross-ref `lighting.md`) |
| Decorative pools | not metered | 2200–2700 K | Picture light, low-output table lamp; off during sleep | (per `lighting.md` decorative-layer cross-ref; the GB 50034-2013 ambient + task floors are not a ceiling on decorative additions, so Kelvin is set lower for atmosphere) |

Operationalising the recipe:
- The ambient and task layers together must satisfy the GB 50034-2013 floor — ambient alone is below the reading target (75 lx vs. 150 lx). The quality gate "Lighting ≥ 2 layers" (per workflow spec § Quality Gates #2) is therefore mandatory before render.
- Bedrooms run **dimmer** than living rooms by design (75 lx vs. 100 lx ambient floor) — the GB 50034-2013 table reflects sleep-environment expectations and matches Sleep Foundation guidance that pre-sleep light should be low and warm (per Sleep Foundation bedroom-environment guidance summarising melatonin-suppression research at higher CCT / lux).
- Avoid downlights placed directly above the pillow line — supine-eye glare hits before the user reaches the switch. Place ambient fixtures off the bed centerline by ≥ 600 mm.

## Camera view set

Default render bundle for a bedroom hero deliverable. Lens / height bands cite `camera.md`.

| View | Lens (full-frame eq.) | Height (m) | Framing intent | Source |
|---|---|---|---|---|
| Hero (3-quarter from door) | 24–28 mm | 1.40–1.55 | Two walls + ceiling line + bed on a thirds intersection; Shift Y +0.10–0.15 to lift ceiling without pitching | (per `camera.md` "Standard framings · Hero shot"; Wikipedia rule-of-thirds for bed-headboard placement) |
| Bed-head straight-on (headboard read) | 35 mm | 1.30–1.45 | Symmetric framing onto the headboard wall to read bedding + sconce + art layering | (per `camera.md` "Eye-level cross-room"; symmetric framing reserved for genuinely bilateral compositions) |
| Bedside detail (styling proof) | 50–85 mm | bedside-table top ± 100 mm | Tight crop on lamp + book + clock — proves material quality and styling density | (per `camera.md` "Detail crop" 50–85 mm; `styling.md` vignette-construction cross-ref) |
| Wardrobe / dressing axis | 28–35 mm | 1.40–1.55 | Camera at the bed foot facing the wardrobe wall — verifies the 900–1200 mm operating clearance is real | (per `camera.md` "Eye-level cross-room"; clearance verification framing convention from `render-output.md`) |
| Plan view (top-down, layout reference) | orthographic, top view | n/a | Whole-room plan with bed footprint + wardrobe footprint + bed-perimeter clearances dimensioned | (per `render-output.md` plan / elevation deliverable rules; Blender orthographic camera per `camera.md` Blender setup) |

## Cross-references

- Code minimums and the §5.4.4 stacking rule live in [`codes.md`](../codes.md).
- Bed-perimeter clearances and circulation bands live in [`spatial.md`](../spatial.md) — keep the 600–750 mm bed-side and 1000 mm bed-foot bands synchronised.
- Lighting Kelvin and lux ranges (and the residential 75 lx ambient floor) live in [`lighting.md`](../lighting.md).
- Standard bed, wardrobe, bedside-table dimensions live in [`furniture.md`](../furniture.md).
- Bedside-vignette construction lives in [`styling.md`](../styling.md).
- Lens / sensor / Shift-Y mechanics for every view above live in [`camera.md`](../camera.md).
- Output bundle (AgX view transform, plan-view orthographic export) lives in [`render-output.md`](../render-output.md).

## Worked examples

**3.0 m × 3.6 m double bedroom (10.8 m²), queen bed, urban apartment.**
Usable area = 10.8 m² → above the GB 50096-2011 9 m² double-bedroom floor (per §5.2.1 item 1) and matches the Layak Architect "standard bedroom" 3000 × 3600 mm footprint (per Layak Architect "Bedroom Dimensions"). Queen bed footprint **1500 × 2050 mm** (per Layak Architect bed-size table). Place the bed long side along the 3.6 m wall: side clearances become **(3000 − 1500) ÷ 2 = 750 mm** each — exactly hitting the upper Neufert bed-side band (per Layak Architect 600–750 mm). Bed foot to opposite wall = **3600 − 2050 − 100 (headboard) = 1450 mm** — clears the 1000 mm Neufert bed-foot rule (per Tetto Homes / Neufert summary). Wardrobe on the foot wall, 600 mm deep, leaves 850 mm operating clearance — at the lower end of the 900–1200 mm Layak band, acceptable for a 1-person operating envelope. Hero camera at 24 mm, height 1.55 m, in the door-wall corner, Shift Y +0.12 (per `camera.md` worked-example pattern). Ambient pendant offset 700 mm from the bed centerline, sized for 75 lx maintained at 0.75 m (per GB 50034-2013 §5.1 Table 5.1.1 卧室 一般活动); two bedside lamps at 150 lx on the reading plane (per GB 50034-2013 §5.1 Table 5.1.1 床头/阅读).

**2.5 m × 2.4 m single bedroom (6 m²), single bed, studio dorm.**
Usable area = 6 m² → above the GB 50096-2011 5 m² single-bedroom floor (per §5.2.1 item 2). Single bed **900 × 2050 mm** along the 2.5 m wall; one side clearance set to **800 mm** (sole circulation), the other to **0 mm** against the wall (acceptable for single-occupant access since the second long side is not used). Bed foot to opposite wall = **2500 − 2050 = 450 mm** — fails the 1000 mm Neufert rule, so the bed orients **head-to-end-wall** instead with a slim 350 mm bedside shelf rather than a bedside table. Drop the dressing table; wardrobe shrinks to a 1200 × 600 mm built-in with door swing into the entry corner. Hero + bed-head views only — wardrobe-axis and detail crops collapse into the hero at this scale.

## Common mistakes

- **Bed bisecting a window or door arc.** Windows want unobstructed daylight transmission for the GB 50096-2011 §7.1.5 1/7 ratio (per GB 50096-2011); a bed in front of an inward-swing door blocks egress. Always clear the door arc (per `furniture.md` door-arc rules) and keep the bed off the window mullion line.
- **Single-side circulation on a queen+ bed.** Queen and king beds want 600–750 mm clear on **both** long sides (per Layak Architect "Bedroom Dimensions"). Pushing one side flush to the wall forces a knee-walk for the wall-side sleeper and breaks the bed-making strip.
- **TV in a sub-12 m² bedroom.** Most bedrooms below 12 m² cannot host a TV at the THX 1.2× diagonal viewing distance without compressing the bed-foot clearance below the Neufert 1000 mm rule (per `space-types/living-room.md` viewing-distance row). Default to no TV; suggest a tablet on a swing arm if media is required.
- **Cool-white (≥ 4000 K) ambient.** Pushes melatonin-suppressing blue content right before sleep and breaks the residential 2700–3000 K convention (per `lighting.md` Kelvin-by-space-type table; per Sleep Foundation bedroom-environment guidance summarising melatonin research). Lock to 2700–3000 K for any bedroom layer.
- **Skipping the task layer.** Ambient alone delivers 75 lx — below the GB 50034-2013 §5.1 Table 5.1.1 床头/阅读 150 lx target. Trips the "Lighting ≥ 2 layers" quality gate before render (per workflow spec § Quality Gates #2; per GB 50034-2013).
