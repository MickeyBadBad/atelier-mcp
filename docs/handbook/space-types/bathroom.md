# Space Type: Bathroom (卫生间)

> Sources: Neufert *Architects' Data* (4th International English ed., Internet Archive PDF, residential bathroom chapter); Panero & Zelnik *Human Dimension & Interior Space* (Whitney Library of Design, 1979, residential anthropometric figures, dimensions.com summarised); NKBA *Bathroom Planning Guidelines with Access Standards* (National Kitchen & Bath Association, 2022 ed., publicly hosted PDF; CRD Design Build summary of numbered guidelines); GB 50096-2011 《住宅设计规范》§5.4 / §5.5.4 (jianbiaoku reproduction; cross-ref `codes.md`); GB 50763-2012 《无障碍设计规范》§3.5 / §3.9 (accessibility; cross-ref `codes.md`); GB 50034-2013 《建筑照明设计标准》§5.1 Table 5.1.1 (Wosen LED / Recolux summaries; cross-ref `lighting.md`); Layak Architect "Bathroom Dimensions" citing Neufert / Time-Saver; IRC 2021/2024 plumbing-fixture-clearance summary on Building Code Geek and CRD Design Build; Dimensions.com "Bathroom Layout Clearances".
> Last updated: 2026-04-29

## Purpose

The bathroom (卫生间) is the household's hygiene and grooming space — its job is to support showering / bathing, toileting, and washing within a wet-rated, code-bound envelope. This chapter is the source of truth for AI agents scaffolding a bathroom: it pins the area envelope (with three GB 50096 sub-types), the fixture clearances (which carry the strictest legal floors of any residential space), the lighting recipe, and the camera view set. Downstream consumers are the `interior-discovery-intake` and `interior-plain-language-edit` skills plus the 9-dimension quality gates — particularly `validate_dimensions` and `validate_accessibility`.

## Typical area range

| Region / context | Range (m²) | Source |
|---|---|---|
| Chinese residential, three-fixture full bath (toilet + shower/tub + washbasin) | ≥ 2.50 m² usable area | (per GB 50096-2011 §5.4.1: "卫生间应包括便器、洗浴器和洗面器，使用面积不应小于2.50㎡"; cross-ref `codes.md`) |
| Chinese residential, two-fixture (toilet + washbasin) | ≥ 1.80 m² usable area | (per GB 50096-2011 §5.4.2 item 1: "设便器、洗面器的卫生间使用面积不应小于1.80㎡") |
| Chinese residential, two-fixture (toilet + bath) | ≥ 2.00 m² usable area | (per GB 50096-2011 §5.4.2 item 2) |
| Chinese residential, single-fixture (toilet only / powder) | ≥ 1.10 m² usable area | (per GB 50096-2011 §5.4.2 item 3: "设便器的卫生间使用面积不应小于1.10㎡") |
| Western (US) half-bath / powder room | ≈ 1.4 m² (5 ft × 3 ft) | (per Layak Architect / dimensions.com bathroom layout summary citing Neufert + IRC: "Half bathroom dimensions (toilet and corner sink, pocket door) 5 ft × 3 ft (1.5 m × 0.9 m)") |
| Western (US) full bath, minimum-code | ≈ 3.6 m² (5 ft × 8 ft) | (per Layak Architect / dimensions.com summary: "Full bathroom (bath/shower with toilet and sink) 5 ft × 8 ft (1.5 m × 2.4 m)") |
| Western (US) master / accessible bath | ≥ 5.6 m² (60 in turning circle clear) | (per ADA 2010 §304.3.1 / GB 50763-2012 §3.5.3 1525 mm turning-circle requirement; floor area sized to keep the circle outside fixture footprints) |

GB 50096-2011 §5.5.4 also fixes the **bathroom interior net height ≥ 2.20 m** (per GB 50096-2011 §5.5.4; cross-ref `codes.md`); the IRC equivalent is 6 ft 8 in ≈ 2.03 m above plumbing fixtures (per IRC R305.1 as summarised on howtolookatahouse.com). When sizing a residential bathroom for accessibility, push above the §5.4.1 floor by ~ 1.5 m² to make room for the GB 50763 turning circle.

## Required clearances

All values are clear distances between finished surfaces. Cross-referenced with `codes.md` (legally binding floors) and `spatial.md` (comfort bands above code).

### Fixture clearances

| Clearance | Range (mm) | Source |
|---|---|---|
| Toilet centerline → side wall / adjacent fixture | ≥ 380 (15 in) IRC floor; 460 (18 in) NKBA recommended | (per IRC 2021 §P2705.1 item 5 as summarised on Building Code Geek "Bathroom Fixture Spacing Requirements"; NKBA Bathroom Planning Guidelines #3 as summarised on CRD Design Build: "IRC requires 15 in minimum; NKBA recommends 18 in") |
| Toilet front clearance (to opposite wall / fixture) | ≥ 533 (21 in) IRC floor; ≥ 760 (30 in) NKBA recommended | (per IRC 2021 R307.1 / Figure R307.1 as summarised on Building Code Geek; NKBA Bathroom Planning Guidelines #5 as summarised on CRD Design Build) |
| Sink (lavatory) centerline → side wall | ≥ 380 (15 in) IRC floor; ≥ 510 (20 in) NKBA recommended | (per IRC 2021 P2705.1 item 5 as summarised on Building Code Geek; NKBA Bathroom Planning Guidelines #11 as summarised on CRD Design Build) |
| Between double-sink centerlines | ≥ 760 (30 in) IRC floor; ≥ 915 (36 in) NKBA recommended | (per IRC P2705.1 / NKBA Bathroom Planning Guidelines #11 on CRD Design Build) |
| Vanity height (residential) | 810–865 (32–34 in) | (per NKBA Bathroom Planning Guidelines #19 as summarised on CRD Design Build: "vanities should be 32–34 in in height"; Neufert summary on Scribd "Neufert Standards House Bathroom" corroborates 800–900 mm range) |
| Sink rim height (accessible) | ≤ 850 (≤ 33.5 in) | (per GB 50763-2012 §3.9.3 accessible-fixture clauses; cross-ref `codes.md`) |
| Shower interior, minimum size | ≥ 760 × 760 (30 × 30 in) IRC floor; ≥ 915 × 915 (36 × 36 in) NKBA preferred | (per IRC 2021 R307.2 as summarised on Building Code Geek "minimum interior shower size is 30 × 30 in or 900 sq in"; NKBA Bathroom Planning Guidelines #18 as summarised on CRD Design Build prefers 36 × 36 in) |
| Shower / tub head ceiling clearance above 30 × 30 in zone | ≥ 2032 (80 in) IRC floor; ≥ 1930 (76 in) per IRC R305.1 alt | (per IRC R307.2 / R305.1 as summarised on Building Code Geek and howtolookatahouse.com) |
| Tub front clearance | ≥ 760 (30 in) per NKBA | (per NKBA Bathroom Planning Guidelines #15 as summarised on CRD Design Build) |
| Activity clearance around fixture (single user) | ≥ 610 (24 in) | (per Panero & Zelnik 1979 anthropometric figures as summarised on Dimensions.com "Bathroom Layout Clearances": "an activity clearance of at least 24 in (61 cm) provides the minimum necessary space around bathroom fixtures for individual use") |
| Circulation clearance for shared bath (pass-by) | ≥ 760 (30 in) | (per Panero & Zelnik 1979 as summarised on Dimensions.com: "30 in (76 cm) ensures that in shared bathroom environments, there is ample space for one person to move or pass by another") |
| Accessible turning circle inside bathroom | 1525 (60 in) ø | (per ADA 2010 §304.3.1; GB 50763-2012 §3.5.3 item 4 corroborates "直径不小于1.50 m"; cross-ref `codes.md`) |
| Bathroom doorway clear width | ≥ 800 (NKBA / GB 50763) — preferred 815–915 (32–36 in) | (per GB 50763-2012 §3.5.3 item 3: "≥ 800 mm" for accessibility; per ADA 2010 §404.2.3: "≥ 32 in (815 mm)"; per NKBA Bathroom Planning Guidelines #2 on CRD Design Build: "at least 32 in"; cross-ref `codes.md`) |
| Bathroom directly above bedroom / living / kitchen | not allowed | (per GB 50096-2011 §5.4.4 mandatory provision; cross-ref `codes.md`) |
| Bathroom interior net height | ≥ 2.20 m | (per GB 50096-2011 §5.5.4; cross-ref `codes.md`) |

Standard fixture footprints used for clearance arithmetic: **Toilet 380 × 700 mm** (with seat); **Wall-hung sink 500 × 400 mm**, **Vanity sink 600 × 460 mm**; **Walk-in shower stall 900 × 900 mm** (NKBA preferred 915 × 915 mm); **Standard tub 1525 × 760 mm (60 × 30 in)** (per Layak Architect / Neufert / Time-Saver bathroom layouts; corroborated by Building Code Geek IRC summary).

## Furniture inventory

### Must-have

- **Toilet** with the IRC 380 mm side / 533 mm front clearance band (per IRC 2021 R307.1 as summarised on Building Code Geek). Wall-hung toilets save 100–150 mm of front clearance vs. floor-mounted.
- **Sink** (wall-hung, pedestal, or vanity) with the 380 mm centerline-to-wall clearance (per IRC 2021 P2705.1 on Building Code Geek; NKBA #11 on CRD Design Build).
- **Bathing fixture** (shower stall and/or tub) with the 760 × 760 mm IRC floor or 915 × 915 mm NKBA preferred (per IRC R307.2 / NKBA #18 on CRD Design Build). The §5.4.1 three-fixture bath requires this; §5.4.2 two-fixture sub-types may drop one bathing fixture.
- **Mechanical ventilation** — code-mandatory in residential wet-rated rooms (per GB 50096-2011 ventilation clauses; specific clause summarised in `codes.md`).
- **Waterproof floor + 1.8 m wet-zone wall membrane** at the shower / tub (per GB 50096-2011 §5.4.5 commentary as summarised on jianbiaoku; cross-ref `materials.md`).

### Common

- **Vanity countertop with mirror above** at 810–865 mm vanity height + mirror bottom edge ~ 1000–1050 mm AFF (per NKBA Bathroom Planning Guidelines #19 vanity-height range on CRD Design Build).
- **Towel bar** at 1100–1200 mm AFF, length ≥ 600 mm (per Neufert *Architects' Data* bathroom chapter as summarised on Scribd "Neufert Standards House Bathroom"; not regulated by code).
- **Storage niche or cabinet** in the wet zone — built-in tile niche over 600 × 300 mm preferred for shower-product storage (per Neufert bathroom chapter standard; not regulated by code).

### Optional

- **Bidet** — additional fixture, 380 × 600 mm footprint with the same 380 mm centerline-to-wall clearance as a toilet (per IRC P2705.1 / Neufert bathroom chapter).
- **Freestanding tub** at 1700 × 800 mm with the 760 mm front clearance — only when usable area exceeds 5.6 m² (per NKBA Bathroom Planning Guidelines #15 on CRD Design Build; tub footprint per Layak Architect / Time-Saver tub-size table).
- **Heated towel rail** in the dressing area outside the wet zone — Neufert bathroom chapter convention; not regulated by code.
- **Grab bars + roll-in shower** (wheelchair-accessible bath) — required when GB 50763 accessibility applies (per GB 50763-2012 §3.9 / cross-ref `codes.md`).

## Lighting layer recipe

| Layer | Target (lx) | Kelvin | Fixture | Source |
|---|---|---|---|---|
| Ambient (general) | 100 lx maintained on a 0.75 m horizontal plane | 2700–3000 K | IP44+ ceiling fixture or recessed downlights | (per GB 50034-2013 §5.1 Table 5.1.1 row "卫生间 一般活动" 100 lx, 0.75 m horizontal plane, Ra ≥ 80, as summarised on Wosen LED standard-lux summary; cross-ref `lighting.md` Residential bathroom row 300–800 lx vanity task) |
| Task (vanity / mirror) | 300–800 lx maintained at the vanity face | 3000–4000 K (color judgement for grooming) | Vertical sconces flanking the mirror, IP44+ rated | (per Super Bright LEDs IES residential summary "vanity 80 fc ≈ 800 lux"; corroborated by Wosen LED chart; cross-ref `lighting.md` Residential bathroom row) |
| Task (shower) | 100–200 lx maintained inside the wet zone | 3000–4000 K | IP65+ recessed downlight inside the shower stall | (per IES residential summary on Super Bright LEDs and industry IP-rated wet-zone practice; primary IES wet-rated clause not verified online — cf. `lighting.md` lux-by-space-type table) |
| Decorative / night | not metered | 2200–2700 K | Low-output LED strip at toe-kick or under vanity for night use | (per `lighting.md` decorative-layer cross-ref; common residential convention) |

Operationalising the recipe:
- Ambient + vanity-task layers are mandatory to satisfy GB 50034-2013 — ambient alone is well below the vanity target (100 lx vs. 300–800 lx). Trips the "Lighting ≥ 2 layers" quality gate (per workflow spec § Quality Gates #2).
- All bathroom luminaires must meet **IP44 outside the wet zone** and **IP65 inside the shower / tub zone** (per IEC 60529 IP-rating convention; specific IEC clause not verified online — cf. `lighting.md` fixture-IP cross-ref). Standard residential downlights are not adequate inside the shower.
- Side-mount the vanity task fixtures, not above — overhead mirror lighting throws shadows onto the user's eye sockets and chin; flanking sconces at 1500–1700 mm AFF give even facial illumination (per Neufert bathroom-grooming chapter; corroborates Layak Architect bathroom-lighting convention).

## Camera view set

Default render bundle for a bathroom hero deliverable. Lens / height bands cite `camera.md`.

| View | Lens (full-frame eq.) | Height (m) | Framing intent | Source |
|---|---|---|---|---|
| Hero (3-quarter from doorway) | 24–28 mm | 1.40–1.55 | Vanity wall + bathing fixture + ceiling line on a thirds composition; Shift Y +0.10–0.15 to lift ceiling | (per `camera.md` "Standard framings · Hero shot") |
| Vanity straight-on (mirror read) | 35 mm | 1.40 | Symmetric framing onto the mirror + sink + sconces; reads grooming task setup | (per `camera.md` "Eye-level cross-room" symmetric framing rule) |
| Shower / wet-zone read | 24–28 mm | 1.50 | Camera at the doorway facing the shower — verifies the 760 × 760 mm IRC / 915 × 915 mm NKBA clear floor | (per `camera.md` "Standard framings"; IRC R307.2 / NKBA #18 verification) |
| Material detail (wet-zone tile + niche) | 50–85 mm | tile-niche centroid ± 100 mm | Tight crop on tile pattern + grout + fixture spec — proves material quality and waterproofing detailing | (per `camera.md` "Detail crop" 50–85 mm; `styling.md` cross-ref) |
| Plan view (top-down, layout reference) | orthographic, top view | n/a | Whole-room plan with toilet / sink / shower footprints + clearance dims overlaid | (per `render-output.md` plan / elevation deliverable rules; Blender orthographic camera per `camera.md`) |

## Cross-references

- Mandatory code minimums (GB 50096-2011 §5.4 area floors, §5.4.4 stacking rule, §5.5.4 net height; GB 50763-2012 accessibility) live in [`codes.md`](../codes.md).
- Activity / circulation / accessible bands (610 / 760 / 1525 mm) also live in [`spatial.md`](../spatial.md).
- Vanity 300–800 lx, Kelvin and IP-rating choices live in [`lighting.md`](../lighting.md).
- Fixture footprints (toilet, sink, shower, tub) live in [`furniture.md`](../furniture.md).
- Wet-zone waterproofing and tile detailing live in [`materials.md`](../materials.md).
- Lens / Shift-Y mechanics live in [`camera.md`](../camera.md).
- Output bundle (AgX view transform, plan-view orthographic export) lives in [`render-output.md`](../render-output.md).

## Worked examples

**1.5 m × 1.7 m three-fixture compact bath (2.55 m²), urban apartment.**
Usable area = 2.55 m² → just above the GB 50096-2011 §5.4.1 2.50 m² three-fixture floor (per §5.4.1; cross-ref `codes.md`). Layout: door on the 1.5 m wall, sink + toilet along the long 1.7 m wall, walk-in shower stall **900 × 900 mm** in the far corner. Toilet centerline 460 mm from the side wall (NKBA recommended; per CRD Design Build summary of NKBA #3) and 540 mm front clearance (above the IRC 533 mm floor; per Building Code Geek IRC summary). Shower interior 900 × 900 mm — clears the IRC R307.2 760 × 760 mm floor (per Building Code Geek) and meets the NKBA #18 915 × 915 mm preferred when tile thickness brings finished interior to ~ 880 × 880 mm. Doorway 800 mm clear (GB 50763-2012 §3.5.3 item 3 minimum; per `codes.md`). Vanity sconces at 1600 mm AFF flanking the mirror, 400 lx at the face plane (per Super Bright LEDs IES residential vanity 80 fc range on `lighting.md`). Hero camera at 24 mm height 1.55 m from the doorway, Shift Y +0.10. Note: at this size the GB 50763 1525 mm turning circle does **not** fit — flag the layout as non-accessible.

**2.4 m × 3.0 m master bath (7.2 m²), accessible.**
Usable area = 7.2 m² — above the §5.4.1 floor and supports the GB 50763-2012 §3.5.3 item 4 1525 mm turning circle (per §3.5.3; cross-ref `codes.md`). Layout: 1500 × 1500 mm clear turning circle centered on the doorway approach, accessible toilet on the far short wall (centerline 460 mm from side wall, 760 mm front clearance per NKBA #5), 1525 × 760 mm tub against the 3.0 m wall opposite a 1200 × 600 mm vanity with double-sink centerlines 915 mm apart (per NKBA #11 on CRD Design Build). Roll-in shower as alternative to tub when grab-bars and bench replace tub. Vanity sconces flanking the mirror at 1600 mm AFF, 500 lx at the face plane. Plan view dimensioned with the 1525 mm turning circle as a dashed overlay per `render-output.md`.

## Common mistakes

- **Toilet centerline below the 380 mm IRC floor.** Pushing the toilet flush against the wall to "save space" trips the IRC P2705.1 / R307.1 clearance — the toilet must keep 380 mm centerline-to-wall (per IRC 2021 as summarised on Building Code Geek). Hard-fail in code review.
- **Stacking a bathroom over a bedroom of the unit below.** GB 50096-2011 §5.4.4 is a **mandatory (强制性) provision** — the bathroom may not sit directly above a bedroom / living room / kitchen of the unit below (per GB 50096-2011 §5.4.4; cross-ref `codes.md`). Affects multi-storey townhouse and stacked-flat designs; check vertical alignment before locking the plan.
- **Specifying a residential downlight inside the shower.** Standard IP20 downlights fail the wet-zone IP65 requirement (per IEC 60529 / `lighting.md` fixture-IP cross-ref). Use a sealed wet-rated trim only inside the shower volume.
- **Mirror-task light overhead instead of flanking.** Overhead-only vanity lighting throws shadows into eye sockets and under the chin — fails grooming function even at 800 lx total (per Neufert bathroom-grooming chapter as summarised on Scribd; corroborated by Layak Architect). Use vertical sconces flanking the mirror.
- **Ignoring the 1525 mm turning-circle requirement on accessible jobs.** GB 50763-2012 §3.5.3 item 4 requires a 1.50 m turning circle inside any accessible bathroom door (per `codes.md`). Most sub-3 m² bathrooms cannot host the circle without enlarging the footprint or relocating fixtures — flag early.
- **Skipping the vanity task layer.** Ambient alone delivers 100 lx — below the GB 50034-2013 §5.1 Table 5.1.1 vanity 300 lx target (per Wosen LED summary; cross-ref `lighting.md`). Trips the "Lighting ≥ 2 layers" quality gate (per workflow spec § Quality Gates #2).
