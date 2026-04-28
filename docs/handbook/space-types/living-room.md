# Space Type: Living Room (起居室 / 客厅)

> Sources: Neufert *Architects' Data* (2nd International English ed., UCEB civbook archive PDF); Panero & Zelnik *Human Dimension & Interior Space* (Whitney Library of Design, 1979, Internet Archive copy); GB 50096-2011 《住宅设计规范》§5.1-5.2 (zlglpt.com / jianbiaoku reproduction); GB 50034-2013 《建筑照明设计标准》§5.1 Table 5.1.1 (gongbiaoku reproduction; Code of China English version); SMPTE EG-18-1994 / THX viewing-angle standards (Wikipedia "Optimum HDTV viewing distance"; What Hi-Fi 4K TV distance guide); Layak Architect "Living Room Dimensions (Design & Interior Guide)" citing Neufert / Time-Saver / Metric Handbook; Homes & Gardens "How to Get Your Living Room Layout Right"; Castlery "The Best Ways to Arrange Your Living Room Layout"; Angi "Living Room Size: Guide to Standard Dimensions".
> Last updated: 2026-04-29

## Purpose

The living room (起居室 / 客厅) is the household's primary social and relaxation space — its job is to host conversation, media viewing, and lounging around a clear focal anchor. This chapter is the source of truth for AI agents scaffolding a residential living-room space: it pins the area envelope, the must-hold clearances, the furniture inventory, the layered lighting recipe, and the camera view set used for renders. Downstream consumers are the `interior-discovery-intake` and `interior-plain-language-edit` skills plus the 9-dimension quality gates.

## Typical area range

| Region / context | Range (m²) | Source |
|---|---|---|
| Chinese urban apartment, regulatory floor | ≥ 10 m² usable area (使用面积) | (per GB 50096-2011 §5.2.2: "起居室（厅）的使用面积不应小于10㎡"; reduced from the 12 m² floor of GB 50096-1999 per the §5.2 条文说明) |
| Chinese urban apartment, typical built range | 12–30 m² | (per GB 50096-2011 §5.2.2 floor of 10 m² combined with the §5.2.3 guideline that a furniture-bearing wall length should exceed 3 m, and developer "product-uplift" practice cited in jianbiaoku §5.2 commentary noting many projects target ≥ 12 m² with 3.6 m × 3.9 m clear) |
| Western (US) residential, urban apartment | 14–23 m² (≈ 150–250 ft²) | (per Angi "Living Room Size" citing 12 × 18 ft / 216 ft² national average and 150–250 ft² urban-apartment band) |
| Western (US) residential, suburban / new-build | 28–46 m² (≈ 300–500 ft²) | (per Angi "Living Room Size" suburban band; Castlery layout guide corroborates 200–400 ft² typical) |
| Neufert "small dwelling" living room | ≥ 18 m² | (per Neufert *Architects' Data* 2nd International English ed. dwelling-types section, UCEB PDF §"Houses · Living Areas") |

GB 50096-2011 §5.1.2 also fixes the套型 (whole-unit) floor: a unit with separate bedroom + living-room + kitchen + bath must be ≥ 30 m² usable; a studio merging bed and living must be ≥ 22 m² (per GB 50096-2011 §5.1.2). When the living area is below 12 m², drop the secondary seating row from the inventory (see "Furniture inventory" optional tier).

## Required clearances

All values are clear distances between finished furniture / wall faces. Cross-referenced with `spatial.md` — keep in sync when editing.

| Clearance | Range (mm) | Source |
|---|---|---|
| Sofa front edge → coffee-table edge | 400–460 | (per Layak Architect "Living Room Dimensions" citing Neufert / Time-Saver / Metric Handbook: "leave at least 45 cm between the sofa and the table on all sides"; Arcedior "Coffee Table Size Guide" corroborates the 45 cm minimum) |
| Coffee-table top height above floor | 380–440 | (per Layak Architect / Arcedior coffee-table size guide: "between 38 cm and 44 cm in height for most residential sofas"; matches typical sofa seat-cushion height minus 0–50 mm) |
| Coffee-table length vs. sofa length | ≈ 2/3 of sofa length (rectangular); ≈ 1/2 of sofa length (round diameter) | (per Layak Architect / Arcedior proportional rule citing Neufert living-room layouts) |
| Walking path through cluster (single person) | ≥ 600 mm | (per Layak Architect citing Neufert / Metric Handbook: "a minimum of 600–750 mm of space is required for one person to move freely"; corroborates `spatial.md` single-person circulation band) |
| Walking path past a seated person | ≥ 750 mm | (per Layak Architect upper bound of the 600–750 mm circulation band; Panero & Zelnik 1979 part 3 residential anthropometric drawings cover seated-clearance dimensions in the same range) |
| TV / screen → primary sofa, viewing distance | 1.0×–1.6× screen diagonal (for 4K UHD) | (per Wikipedia "Optimum HDTV viewing distance" summarising SMPTE EG-18-1994 30° = ~1.6× diagonal and THX 36–40° = ~1.2× diagonal; What Hi-Fi 4K-TV guide: "for a 4K TV you sit between 1 and 1.5 times the size of it away from its screen"; default to **1.2× diagonal** as the THX immersive midpoint) |
| TV centre height above floor | 1050–1200 (centre at seated eye-level) | (per Hi-Rise Camera "Adjusting Camera Height" seated-eye band 1.1–1.2 m, identical to the seated-anthropometric figures cited in Panero & Zelnik 1979 part 2) |
| Conversation grouping (chair-to-chair, face-to-face) | ≤ 2.4 m (≈ 8 ft) between facing seats | (per Castlery "Best Ways to Arrange Your Living Room Layout": "chairs should be no more than 8 feet apart to facilitate conversation"; Homes & Gardens "Get Your Living Room Layout Right" corroborates the same 8-ft rule for conversation areas) |
| Furniture-bearing wall, minimum straight length | ≥ 3000 mm | (per GB 50096-2011 §5.2.3: "起居室（厅）内布置家具的墙面直线长度宜大于3m") |
| Doors opening into the living room | minimise count | (per GB 50096-2011 §5.2.3: "套型设计时应减少直接开向起居厅的门的数量"; soft requirement) |
| Window: floor-area-to-window ratio (daylight) | ≥ 1/7 | (per GB 50096-2011 §7.1.5 mandatory clause: "卧室、起居室（厅）、厨房的采光窗洞口的窗地面积比不应低于1/7") |

## Furniture inventory

### Must-have

- **Sofa cluster** = one sofa (2- or 3-seater) + coffee table (per Layak Architect citing Neufert living-room layouts; the sofa + low table is the canonical residential living-room core).
- **Focal anchor** — exactly one of: TV / fireplace / window-view / feature wall (per Homes & Gardens "Get Your Living Room Layout Right": "every room begins with a focal point — something to give the scheme direction"; Castlery: "great living room layouts start with identifying your focal point... fireplace, television, window view, or architectural feature").
- **Area rug under the cluster** when the floor is hard (wood / tile / SPC) — anchors the seating zone visually and acoustically (per Homes & Gardens layout guide: "area rugs… can define the different spaces while maintaining an overall sense of flow"; absorption role corroborated by `acoustics.md` cross-ref).

### Common

- Side / accent chair (1–2) angled toward the focal anchor (per Castlery: "chairs angle toward conversation areas"; Homes & Gardens: "main piece should face the room's focal point").
- Side table (end-of-sofa or between chairs) at ~ sofa-arm height (per Layak Architect side-table guidance, height to within 50 mm of sofa-arm top).
- Floor lamp at the conversation cluster perimeter, doubling as reading light (per GB 50034-2013 Table 5.1.1 reading-task 300 lx requirement, which the ambient layer alone cannot meet; floor-lamp role detailed in `lighting.md`).
- Storage console / sideboard against a non-cluster wall (per Castlery layout-guide examples; not regulated by code).

### Optional

- Secondary seating (loveseat, ottoman, bench) — drop this tier when usable area falls below 12 m² (per GB 50096-2011 §5.2.3 furniture-wall-length advisory: a < 3 m wall cannot host a second seating row).
- Bookshelf / display shelving as secondary focal point (per Homes & Gardens: "secondary focal points add depth and interest. Artwork, mirrors, or beautiful console tables create visual interest beyond your primary anchor").
- Window-side reading nook with a single chair + task light (per GB 50034-2013 Table 5.1.1 "起居室 书写、阅读" 300 lx task value, which justifies a dedicated reading station as a discrete sub-zone).

## Lighting layer recipe

| Layer | Target (lx) | Kelvin | Fixture | Source |
|---|---|---|---|---|
| Ambient | 100 lx maintained on a 0.75 m horizontal plane | 2700–3000 K (residential warm-white) | Overhead pendant, recessed downlights, or cove uplighting | (per GB 50034-2013 Table 5.1.1 row "起居室 一般活动": 100 lx, 0.75 m horizontal plane, Ra ≥ 80; Kelvin band per `lighting.md` residential-warm cross-ref) |
| Task / reading accent | 300 lx maintained at the reading position | 2700–3000 K | Adjustable wall sconce, floor lamp with directable head, or table lamp at the reading chair | (per GB 50034-2013 Table 5.1.1 row "起居室 书写、阅读": 300 lx with mixed-lighting `*` notation indicating task fixtures supplement ambient; Ra ≥ 80) |
| Decorative pools | not metered | 2200–2700 K | Table lamps, picture lights, candle-equivalent low-output points around the room | (per `lighting.md` decorative-layer cross-ref; ambient/task gates in GB 50034-2013 do not regulate decorative pools, so Kelvin is set lower for atmosphere; warmer-than-task K range matches contemporary residential moodboards in Homes & Gardens layout features) |

Operationalising the recipe:
- The ambient and task layers together must satisfy the GB 50034-2013 floor — ambient alone is insufficient at the reading chair (100 lx vs. 300 lx target). The quality gate "Lighting ≥ 2 layers" (per workflow spec § Quality Gates #2) is therefore mandatory for any living-room scene before render.
- Mix Kelvin **across** layers, not within a single layer. All ambient sources should match each other to within ±100 K to avoid the "two-suns" effect (per `lighting.md` Kelvin-coherence rule).
- Dim the ambient layer to ≈ 50 % when the TV is the active focal mode — keeps screen contrast usable while preserving room legibility (per Wikipedia HDTV viewing-distance article note that ambient-light reduction extends comfortable viewing time at the 30–40° angle band).

## Camera view set

Default render bundle for a living-room hero deliverable. Lens / height bands cite `camera.md`, which in turn cites D5 Render archviz, Hi-Rise Camera, and Austin LaRue Photography.

| View | Lens (full-frame eq.) | Height (m) | Framing intent | Source |
|---|---|---|---|---|
| Hero (3-quarter from entry) | 24–28 mm | 1.40–1.55 | Two walls + ceiling line + floor; focal anchor on a thirds intersection; Shift Y +0.10–0.15 to lift ceiling without pitching | (per `camera.md` "Standard framings · Hero shot" citing Austin LaRue Photography sweet-spot 21–28 mm and D5 Render archviz height range; Wikipedia rule-of-thirds for the focal-anchor placement) |
| Sofa-cluster corner (conversation read) | 21–24 mm | 1.20–1.40 | Camera tucked into a non-cluster corner facing the diagonal corner; reads sofa + coffee-table + accent chair as one social unit | (per `camera.md` "Corner shot" citing Austin LaRue Photography ultra-wide caution; Hi-Rise Camera lower 1.2–1.4 m band; Castlery conversation-area arrangement principle) |
| Coffee-table detail (styling proof) | 50–85 mm | object-centroid ± 100 mm | Tight crop on coffee-table top + sofa edge + rug texture — proves material quality and styling density without selling space | (per `camera.md` "Detail crop" citing 50–85 mm + object-centroid placement; `styling.md` cross-ref for vignette construction) |
| Cross-room axial (focal-anchor read) | 28–35 mm | 1.40–1.55, centred on focal-anchor axis | Symmetric framing onto TV / fireplace / window when the room has true bilateral architecture | (per `camera.md` "Eye-level cross-room" framing; Wikipedia rule-of-thirds note that symmetry is reserved for genuinely bilateral spaces) |
| Plan view (top-down, layout reference) | orthographic, top view | n/a (orthographic) | Whole-room plan with furniture footprints and clearance dims overlaid; deliverable for layout review and contractor handoff | (per `render-output.md` view-set rules for plan / elevation deliverables; Blender orthographic camera per Blender Manual 5.1 "Cameras" referenced in `camera.md` Blender setup section) |

## Cross-references

- Clearances also live in [`spatial.md`](../spatial.md) — keep the 600 mm circulation, 400–460 mm sofa-to-table, and seated-eye 1.1–1.2 m bands synchronised.
- Lighting Kelvin-coherence and decorative-pool conventions live in [`lighting.md`](../lighting.md).
- The GB 50096-2011 daylight ratio (§7.1.5), the GB 50034-2013 illuminance table (§5.1 Table 5.1.1), and any future fire-egress rules sit in [`codes.md`](../codes.md).
- Standard sofa, coffee-table, side-table dimensions sit in [`furniture.md`](../furniture.md).
- Vignette construction for the coffee-table detail shot lives in [`styling.md`](../styling.md).
- Lens / sensor / Shift-Y mechanics for every view above live in [`camera.md`](../camera.md).
- Output bundle (AgX view transform, plan-view orthographic export, file-naming) lives in [`render-output.md`](../render-output.md).

## Worked examples

**4 m × 5 m living room, 55-inch 4K TV focal anchor, urban apartment.**
Usable area = 20 m² → comfortably above the GB 50096-2011 10 m² floor (per §5.2.2) and inside the typical 12–30 m² Chinese-apartment band. 55-inch diagonal ≈ 1.40 m, so primary-sofa front edge sits 1.40 m × 1.2 = **1.68 m** from the screen for the THX immersive read, or 1.40 m × 1.6 = **2.24 m** for the SMPTE comfort read (per Wikipedia "Optimum HDTV viewing distance"; What Hi-Fi 4K-TV guide). Coffee table sits **0.45 m** off the sofa front edge (per Layak / Arcedior 45 cm rule) and is sized to ≈ 2/3 of a 2.20 m sofa = **1.45 m long, 0.42 m tall** (per Layak proportional rule). Hero camera at 24 mm, height 1.55 m, in the entry corner, Shift Y +0.12 (per `camera.md` worked-example pattern). Ambient ceiling fixture sized for 100 lx maintained at 0.75 m (per GB 50034-2013 Table 5.1.1) plus a floor lamp at the cluster delivering 300 lx at the reading chair (per same table, "书写、阅读" row).

**3.2 m × 3.5 m living room, < 12 m² band, studio apartment.**
Usable area = 11.2 m² — passes the GB 50096-2011 10 m² floor (per §5.2.2) but loses the secondary-seating tier per the §5.2.3 furniture-wall-length advisory (no 3 m straight wall available after door + window deductions). Inventory drops to: sofa + coffee table + one accent chair + one floor lamp + rug. TV mounts on the longest wall; sofa parallel; conversation grouping ≤ 2.4 m chair-to-sofa spacing (per Castlery 8-ft rule). Skip the cross-room axial view — at this room scale the hero + sofa-corner + detail crop trio is enough.

## Common mistakes

- **TV too close to sofa, immersive-mode misread.** Putting a 55-inch screen at 1.0 m from the sofa exceeds the THX 40° angle and forces head-turning to read the corners (per Wikipedia "Optimum HDTV viewing distance" THX-40° = 1.2× diagonal lower bound). Default to 1.2×–1.6× diagonal; only go below 1.2× when the user has explicitly asked for cinema immersion.
- **Coffee table at sofa-arm height.** The coffee-table top should sit 380–440 mm — at sofa-arm height (550–650 mm) it competes visually with the sofa silhouette and breaks the "low-table-anchors-the-cluster" read (per Layak / Arcedior proportional rule).
- **Furniture pushed against all four walls.** Empties the room centre and breaks the conversation-area model (per Castlery: "unless the room is especially small, avoid pushing all the furniture against the walls"; Homes & Gardens corroborates). Pull the sofa cluster off the wall by ≥ 200 mm whenever circulation behind it is not required.
- **No focal anchor, or two competing anchors at 90°.** A living room without a clear primary anchor reads as a transit corridor; two anchors on perpendicular walls force visitors into a swivel-or-pick choice (per Homes & Gardens layout guide on opposite focal points: "not ideal… make a decorator's job rough"). Pick one primary; demote the other to a secondary read via swivel chair.
- **Ambient layer alone, no task layer at the reading chair.** Fails GB 50034-2013 Table 5.1.1 reading-task 300 lx target and trips the "Lighting ≥ 2 layers" quality gate before render (per workflow spec § Quality Gates #2; per GB 50034-2013).
