# Space Type: Cafe / Lounge (咖啡馆 / 休闲餐饮)

> Sources: Neufert *Architects' Data* (4th International English ed., Internet Archive PDF, restaurants / catering chapter, pp. 187–189; ResearchGate "Restaurant space requirements" reproduction); Time-Saver Standards for Building Types (McGraw-Hill, restaurant / cafe / kitchen sections pp. 755–768, archived on arc213.files.wordpress.com); GB 50034-2013 《建筑照明设计标准》§5.3 / Table 5.x for 餐饮建筑 (Wosen LED / Recolux / Casyoo summaries; cross-ref `lighting.md`); GB 50016-2014 (2018 amendment) 《建筑设计防火规范》§5.5.17 (egress for "其他建筑" public-building rows; cross-ref `codes.md`); GB 50763-2012 《无障碍设计规范》§3.5 / §3.7 (cross-ref `codes.md`); ADA 2010 Standards for Accessible Design §403 / §902 (Access-Board publication); ISO 3382-2:2008 §3.1 (RT60 definition; summarised on commercial-acoustics.com and ddsacoustical.com); Rindel "Suggested acoustical requirements for restaurants, canteens, and cafeterias" (BNAM 2018, paper C142 on odeon.dk); Acoustic Bulletin "The Lombard effect in hospitality"; WELL Building Standard "Reverberation Time" feature; Toast POS "Average Restaurant Square Footage" (per-seat sizing); Hospitality.Institute "Back of House Food Production Planning Guide" (FOH/BOH ratios); Dimensions.com "Dining Room Clearances".
> Last updated: 2026-04-29

## Purpose

The cafe / lounge envelope is a small public-building hospitality space — coffee shop, tea house, casual bar, hotel lounge — whose job is to host short to medium dwell-time seated socialising plus over-the-counter beverage and light-food service. This chapter is the source of truth for AI agents scaffolding any cafe-style space, **regardless of size, location, or stylistic palette**: it pins the area envelope (per-seat sizing + FOH/BOH split), the table / bar clearances, the lighting recipe (which sits below the residential dining floor on purpose), the acoustic target, and the camera view set. Downstream consumers are the `interior-discovery-intake` and `interior-plain-language-edit` skills plus the 9-dimension quality gates.

## Typical area range

Cafe sizing is driven by **seat count × per-seat allocation**, then split FOH (front of house, customer-facing) and BOH (back of house, prep + storage + staff). The headline ratios:

| Region / context | Range | Source |
|---|---|---|
| Per-seat FOH allocation, casual cafe / coffee-shop | ≈ 1.4 m² (15 ft²) per seat | (per Toast POS "Average Restaurant Square Footage" sizing guide: "Most restaurants and coffee shops with a general menu allocate about 15 sq ft per person"; corroborates Time-Saver Standards 12–15 sq ft per person band on arc213 PDF) |
| Per-seat FOH allocation, cafeteria-style close seating | ≈ 1.1 m² (12 ft²) per seat | (per Toast POS sizing guide: "12 sq ft per person for cafeteria or restaurant style seating"; corroborates Time-Saver Standards p. 759 restaurant-seating-density figures) |
| Per-seat FOH allocation, fine-dining / spacious | ≈ 1.7–1.9 m² (18–20 ft²) per seat | (per Toast POS: "for fine dining, the range is 18–20 sq ft per person") |
| FOH:BOH split, full-service cafe | ≈ 60 / 40 | (per Toast POS "Average Restaurant Square Footage": "the dining area should take up 60 % of space, with the remaining 40 % allocated to the kitchen, storage, and other back-of-house functions"; Hospitality.Institute corroborates 30–40 % FOH for production-heavy ops, 60–70 % BOH for the same) |
| FOH:BOH split, quick-service / counter-only | ≈ 45 / 55 | (per Toast POS: "QSRs often reverse the standard allocation. In these production-driven environments, only 45 % of space may go to seating, while 55 % is devoted to kitchen and storage") |
| Per-seat BOH (kitchen) sizing rule of thumb | ≈ 0.46 m² (5 ft²) of kitchen per FOH seat | (per Toast POS "Average Restaurant Square Footage": "allocate 5 sq ft of kitchen space for every seat in your FOH") |
| Neufert *Architects' Data* dining-room sizing caveat | "number of heads = m²" formulas not applicable to rooms < 100 m² | (per Neufert *Architects' Data* restaurant chapter as reproduced on ResearchGate "Restaurant space requirements": "the design of dining rooms based on 'number of heads = m²' formulas is to be avoided, as they are not applicable to rooms under 100 m² and can lead to false results"; Neufert insists on furniture-layout-driven sizing for small cafes) |

A 24-seat casual cafe therefore wants ≈ 24 × 1.4 = **34 m² FOH** plus ≈ 24 × 0.46 = **11 m² BOH** plus restroom + storage = total **≈ 50–60 m² gross**. Below 30 m² the Neufert per-seat rule loses validity (per Neufert restaurant chapter) — switch to a furniture-layout-driven plan and let table count fall out of the layout.

GB 50016-2014 §5.5.17 also caps **any-point-to-nearest-exit travel distance** for restaurant/cafe spaces (Class I/II fire resistance, ≥ 2 exits) at **30 m straight-line** (per GB 50016-2014 §5.5.17 item 4 large-room special rule; +25 % uplift if sprinklered per Note 3; cross-ref `codes.md`).

## Required clearances

All values are clear distances between finished furniture / wall faces. Cross-referenced with `spatial.md` and `codes.md` — keep in sync when editing.

### FOH — table + chair clearances

| Clearance | Range (mm) | Source |
|---|---|---|
| Per-person table-edge width (rectangular) | 600 (24 in) absolute, 660–760 (26–30 in) preferred | (per Neufert *Architects' Data* restaurant chapter on ResearchGate: "individual place setting around 60 cm wide and 30–40 cm deep"; corroborated by Dimensions.com "Dining Room Clearances": "chairs spaced 24–30 in apart") |
| Table depth (cafe / plate service) | 700 | (per Neufert *Architects' Data* restaurant chapter: "if the food is served on plates, then 70 cm is sufficient, and for fast food 60 cm table depth"; ResearchGate reproduction) |
| Table → wall (chair pulled out, no traffic behind) | ≥ 750 | (per Neufert *Architects' Data* restaurant chapter: "distance between table and wall should be ≥ 75 cm, because the chair alone requires a space of 50 cm") |
| Table → wall (chair pulled out + walking behind) | ≥ 1000 | (per Neufert *Architects' Data* restaurant chapter: "if the space between table and wall is also used for access, the distance should be ≥ 100 cm") |
| Round-table → wall additional allowance | + 500 | (per Neufert *Architects' Data*: "round tables need a little more space, a difference of up to 50 cm") |
| Table → table (back-to-back chair clearance) | ≥ 1200 (≈ 2 × 600 mm pulled chairs) | (per Time-Saver Standards for Building Types restaurant section pp. 759–761 as archived on arc213 PDF; corroborates Dimensions.com "Dining Room Clearances" total clearance band 36–60 in) |
| Diagonal vs. aligned table arrangement | up to 35 % space saving for diagonal | (per Neufert *Architects' Data*: "Diagonal arrangement of the tables generally takes up less space than an aligned pattern, with a space saving of up to 35 %") |
| Alcove / banquette seating | wall-side clearance not required | (per Neufert *Architects' Data*: "Alcoves are beneficial for use of space because the distance between seats and wall is no longer required") |
| Booth depth (per side, including seat back) | 600–650 | (per Time-Saver Standards for Building Types booth-detail figures p. 759, archived on arc213; corroborated by Dimensions.com booth dimensions) |
| Bar / counter, customer side stool spacing | ≥ 600 (24 in) on-centre | (per Time-Saver Standards for Building Types liquor-bar section p. 765, archived on arc213; corroborates Neufert bar-stool figures) |
| Bar / counter height (customer top) | 1050–1150 (42–45 in) | (per Time-Saver Standards bar-detail p. 765; corroborated by Layak Architect bar-counter convention) |
| Bar stool seat height (matched to 1100 mm bar) | 760 (30 in) | (per Time-Saver Standards bar-detail p. 765 stool-detail figures) |
| Counter aisle behind bar (single staff) | ≥ 900 | (per Neufert *Architects' Data* bar / counter section p. 188; corroborates NKBA Kitchen Planning Guidelines work-aisle parallel) |
| Counter aisle behind bar (multi-staff) | ≥ 1200 | (per Neufert *Architects' Data* bar / counter section p. 188; corroborates NKBA work-aisle multi-cook 1219 mm) |
| Accessible route through seating area | ≥ 915 (36 in) clear | (per ADA 2010 §403.5 / GB 50763-2012 §3.5.1: "≥ 1.20 m" indoor accessible passage; cross-ref `codes.md`) |
| Accessible turning circle, where required | 1525 (60 in) ø | (per ADA 2010 §304.3.1; GB 50763-2012 §3.5.3 item 4; cross-ref `codes.md`) |
| Counter-service accessible counter section | ≥ 915 mm wide at ≤ 865 mm height | (per ADA 2010 §904.4 sales-and-service-counter clauses; corroborated by GB 50763-2012 §3.5.1 item 3 wheelchair-counter ≥ 900 mm) |
| Travel distance any-seat → nearest exit (large public room) | ≤ 30 m straight-line (Class I/II, ≥ 2 exits) | (per GB 50016-2014 §5.5.17 item 4; +25 % if sprinklered per Note 3; cross-ref `codes.md`) |

Standard cafe-table footprints used for clearance arithmetic: **2-seat 700 × 700 mm**; **2-seat round Ø 700 mm**; **4-seat 1200 × 700 mm**; **4-seat round Ø 1100 mm**; **6-seat 1800 × 800 mm**; **bar / high-top 4-seat 1500 × 700 mm at 1100 mm height** (per Time-Saver Standards restaurant-seating p. 759 and Neufert restaurant chapter p. 187; corroborated by Civil Tutorials dining tables summary).

## Furniture inventory

### Must-have

- **Seated FOH tables** sized 2-seat / 4-seat with the per-person 600 mm and table-depth 700 mm bands (per Neufert restaurant chapter); per-seat allocation 1.4 m² (15 ft²) FOH (per Toast POS).
- **Service counter / bar** delivering customer order + payment + (optionally) seated bar service. Customer-side stool spacing 600 mm, counter top 1050–1150 mm AFF (per Time-Saver Standards bar p. 765). Behind-bar staff aisle ≥ 900 mm single-staff (per Neufert p. 188).
- **At least one accessible seated table** with the ADA §902 accessible-table clearance and 1525 mm turning circle reachable from the entry route (per ADA 2010 §902 / GB 50763-2012; cross-ref `codes.md`).
- **Two egress exits** for any cafe whose layout pushes a seat past the 30 m straight-line travel distance to a single exit (per GB 50016-2014 §5.5.17; cross-ref `codes.md`).
- **BOH prep counter + sink + cold storage** sized to ≥ 5 ft² (0.46 m²) per FOH seat (per Toast POS / Time-Saver Standards kitchen p. 768).

### Common

- **Banquette / alcove seating** along one wall — saves 750 mm wall-side clearance per Neufert alcove rule (per Neufert restaurant chapter); useful in narrow cafe footprints below 4.0 m wide.
- **High-top / bar-height communal table** for solo seating + laptop work (1100 mm height, 760 mm stool seat) (per Time-Saver Standards bar p. 765; common cafe convention).
- **Pastry / display refrigerator** at the counter — sized into the BOH allocation (per Time-Saver Standards food-bar section p. 763).
- **Coat / bag hooks** at booth ends or under bar overhang — Neufert restaurant fitting convention; not regulated by code.

### Optional

- **Dedicated reading / lounge zone** with sofa + low table (cafe-lounge hybrid) — sized using `space-types/living-room.md` sofa-cluster clearances (per Layak Architect / Castlery layout rules cross-referenced in living-room chapter). Drops table count by 2–3 in exchange for dwell time.
- **Outdoor terrace / sidewalk seating** — per local AHJ patio rules; GB / IBC do not directly regulate but the FOH:BOH ratio and §5.5.17 travel distances still apply when outdoor seats count toward occupancy.
- **Live-music / DJ corner** — adds an acoustic load that must be reconciled with the RT60 target below (per Acoustic Bulletin "The Lombard effect in hospitality"; Rindel BNAM 2018 paper §3 restaurant classification on odeon.dk).
- **Retail merchandise display** (beans, mugs) — reads as wayside fixture; sized per Time-Saver Standards retail counter p. 765.

## Lighting layer recipe

| Layer | Target (lx) | Kelvin | Fixture | Source |
|---|---|---|---|---|
| Ambient (general FOH) | 100–200 lx maintained on a 0.75 m horizontal plane | 2700–3500 K | Suspended pendants, recessed downlights, or cove uplighting | (per GB 50034-2013 §5.3 餐饮建筑 row "咖啡厅 / 西餐厅" 100–150 lx, 0.75 m horizontal plane, Ra ≥ 80, as summarised on Wosen LED standard-lux summary and Recolux Lighting GB-50034 commentary; corroborated by Archtoolbox citing IESNA Handbook lounge 10–30 fc ≈ 100–300 lux; cross-ref `lighting.md`) |
| Accent (focal walls / artwork / display) | 3–5× the ambient on the focal object | 2700–3500 K (match ambient ± 100 K) | Adjustable track or recessed adjustable downlights | (per ERCO Lighting Knowledge "Arranging luminaires" accent-contrast rule of thumb; cross-ref `lighting.md` four-layer model) |
| Per-table task | 150 lx maintained at the table top | 2700–3000 K (warmer than ambient for intimacy) | Pendant centred over table, 800–900 mm above table top, dimmable | (per GB 50034-2013 §5.3 餐饮建筑 row "餐厅" 150 lx as summarised on Wosen LED / Recolux Lighting; corroborated by XAL "Lighting for the dining hall and cafeteria" 200 lx EN 12464-1 reference; cross-ref `lighting.md`) |
| Decorative pools | not metered | 2200–2700 K | Wall sconces, picture lights, candle-equivalent low-output points | (per `lighting.md` decorative-layer cross-ref; warmer than ambient/task for atmosphere) |
| Counter / bar task | 300 lx at the counter top | 3000–4000 K (color judgement for drink prep) | Linear LED under upper shelf or recessed down-spot over bar | (per GB 50034-2013 餐饮建筑 commentary on counter-task surfaces summarised on Wosen LED; corroborated by `space-types/kitchen-dining.md` counter-task 500–750 lx residential floor — cafe bar sits below the home-kitchen number because cafes are not full-prep) |

Operationalising the recipe:
- The ambient + per-table task layers must satisfy the GB 50034-2013 floor — a single ambient layer at 75 lx fails both the 100 lx ambient and the 150 lx table-task target (per Wosen LED summary). Trips the "Lighting ≥ 2 layers" quality gate (per workflow spec § Quality Gates #2).
- Cafes typically run **dimmer and warmer** than residential dining — Archtoolbox / IESNA Handbook lounge 10–30 fc band sits below the residential dining 30 fc target (per Archtoolbox lounge row in `lighting.md`). The Kelvin target follows hospitality convention 2700–3500 K (per Lumens "Kelvin Color Temperature Chart"; cross-ref `lighting.md` Hospitality row).
- Per-table pendants should hang **800–900 mm above table top** so the bottom of the shade sits below seated eye level — keeps the 150 lx task target tight on the table rather than spilling onto adjacent tables.

## Acoustic target (cafe-specific)

| Metric | Target | Source |
|---|---|---|
| RT60 (reverberation time, occupied or unoccupied) | 0.4–0.6 s | (per Rindel "Suggested acoustical requirements for restaurants, canteens, and cafeterias" BNAM 2018 paper C142 on odeon.dk: cafes / restaurants target 0.4–0.6 s as summarised on Acoustic Bulletin "The Lombard effect in hospitality"; corroborated by commercial-acoustics.com hospitality RT60 row; ISO 3382-2:2008 §3.1 defines RT60 as "the duration required for the space-averaged sound energy density in an enclosure to decrease by 60 dB after the source emission has stopped") |
| Volume per person | ≥ 10 m³ | (per Rindel BNAM 2018: "if the reverberation time is more than 1.5 s and the volume per person is less than 10 m³, the ambient noise level may exceed acceptable limits"; pushing the parameter above 10 m³ at RT60 < 0.6 s keeps noise below the Lombard-effect threshold) |
| Average room absorption coefficient (ᾱ) | 0.7–1.0 | (per Acoustic Bulletin "The Lombard effect in hospitality": "for restaurant and hospitality spaces aim for average room absorption coefficient of 0.7–1.0"; achieves comfortable 1.5 m table-spacing speech distance vs. 3 m at ᾱ ≈ 0.2) |
| WELL Building Standard reverberation feature | RT60 ≤ 0.6 s for spaces ≤ 500 m³ | (per WELL Building Standard "Reverberation Time" feature requirement summarised on standard.wellcertified.com; corroborates the cafe target band) |

For cafes with hard floor + glass + dense seating, this target is achievable only with **acoustic ceiling treatment** (mineral fiber tiles, baffles, or 50 mm rockwool with fabric scrim), upholstered seating, and one absorptive wall section ≥ 30 % of the wall area (per `acoustics.md` material-NRC cross-ref; corroborates Acoustic Bulletin restaurant-treatment guidance).

## Camera view set

Default render bundle for a cafe / lounge hero deliverable. Lens / height bands cite `camera.md`.

| View | Lens (full-frame eq.) | Height (m) | Framing intent | Source |
|---|---|---|---|---|
| Hero (3-quarter from entry) | 24–28 mm | 1.40–1.55 | Two walls + ceiling line + bar + sample of table cluster on a thirds composition; Shift Y +0.10–0.15 to lift ceiling | (per `camera.md` "Standard framings · Hero shot") |
| Bar / counter axial | 28–35 mm | 1.30–1.45 | Camera on the customer side facing the bar — reads the full bar product display + counter top + bartender pass | (per `camera.md` "Eye-level cross-room"; Time-Saver Standards bar p. 765 view convention) |
| Banquette / booth read | 21–24 mm | 1.20–1.30 (seated eye level) | Tucked into a non-cluster corner facing the diagonal; reads booth + table + window line | (per `camera.md` "Corner shot" ultra-wide caution; Hi-Rise Camera lower 1.2–1.4 m band) |
| Table-top detail (styling proof) | 50–85 mm | table top ± 100 mm | Tight crop on cup + saucer + table material — proves task-light coverage and styling density | (per `camera.md` "Detail crop" 50–85 mm; `styling.md` cross-ref) |
| Plan view (top-down, layout reference) | orthographic, top view | n/a | Whole-cafe plan with table footprints + clearances + egress travel distances overlaid | (per `render-output.md` plan / elevation deliverable rules; GB 50016-2014 §5.5.17 travel distances visualised; Blender orthographic camera per `camera.md`) |

## Cross-references

- Public-building egress rules (GB 50016-2014 §5.5.17 large-room special) and accessibility (GB 50763-2012 §3.5 / §3.7) live in [`codes.md`](../codes.md).
- Table-to-wall, table-to-table, and bar-aisle clearances also live in [`spatial.md`](../spatial.md).
- Hospitality Kelvin (2700–3500 K) and lux ranges (lounge 100–300 lx, restaurant ambient 50–100 lx) live in [`lighting.md`](../lighting.md).
- Standard cafe-table, chair, bar-stool, banquette dimensions live in [`furniture.md`](../furniture.md).
- RT60 target, NRC material values, and absorption-coefficient calculation live in [`acoustics.md`](../acoustics.md).
- Hero / counter / detail vignette construction lives in [`styling.md`](../styling.md).
- Lens / sensor / Shift-Y mechanics for every view above live in [`camera.md`](../camera.md).
- Output bundle (AgX view transform, plan-view orthographic export) lives in [`render-output.md`](../render-output.md).

## Worked examples

**60 m² gross casual cafe, 24 FOH seats, single counter.**
FOH = 60 × 0.60 = 36 m² → ≈ 24 × 1.4 = 34 m² seat area + 2 m² circulation slack — tracks the Toast POS 60/40 ratio (per Toast POS "Average Restaurant Square Footage"). BOH = 24 m² with 24 × 0.46 = 11 m² of kitchen/prep + 13 m² of restroom/storage/staff. Tables: 8 × 4-seat (1200 × 700 mm) at 1.5 m centres along the long axis, plus 2 × bar high-tops. Table-to-wall both sides 1000 mm (walking-behind, per Neufert restaurant chapter); table-to-table back-to-back 1200 mm (per Time-Saver Standards p. 759). Travel distance from worst seat to either of two exits: ≈ 14 m straight-line — well within the GB 50016-2014 §5.5.17 30 m large-room cap (per `codes.md`). Ambient 150 lx at 2900 K (per GB 50034-2013 餐饮建筑 row 咖啡厅 on Wosen LED summary); per-table pendants 150 lx at 2700 K, 850 mm above table top. RT60 target 0.5 s — requires mineral-fiber ceiling tiles + fabric-faced absorber on one long wall to lift ᾱ to ~ 0.7 (per Acoustic Bulletin restaurant-treatment guidance; cross-ref `acoustics.md`). Hero camera at 24 mm height 1.55 m from the entry corner, Shift Y +0.12.

**32 m² gross compact lounge cafe, 14 FOH seats, banquette + bar.**
Below the Neufert 100 m² per-seat-formula validity threshold (per Neufert restaurant chapter) — switch to furniture-layout-driven sizing. FOH ≈ 32 × 0.55 = 18 m² (slightly QSR-leaning split since BOH is counter-only): 4 × 2-seat banquette (700 × 700 mm) along one wall using Neufert's alcove-clearance saving, plus 1 × 4-seat bar high-top, plus 2 stools at the counter bar. Table-to-table back-to-back 1100 mm; bar-stool spacing 600 mm. Travel distance ≈ 8 m to the single front entrance — under the §5.5.17 30 m cap, but a single-exit cafe is only legal under §5.5.15 if total FOH ≤ 200 m² and travel ≤ 15 m (per GB 50016-2014; cross-ref `codes.md`); this layout passes. RT60 needs 0.5 s — banquette upholstery + acoustic baffles overhead carry most of the absorption budget. Plan-view deliverable annotates the single egress per `render-output.md`.

## Common mistakes

- **Sizing a cafe with a "heads × m²" formula below 100 m².** Neufert's restaurant chapter explicitly invalidates this approach for small rooms (per Neufert *Architects' Data* on ResearchGate: "the design of dining rooms based on 'number of heads = m²' formulas is to be avoided, as they are not applicable to rooms under 100 m²"). Use furniture-layout-driven sizing and let seat count fall out of the layout.
- **Forgetting the GB 50016-2014 §5.5.17 30 m travel cap.** The large-room special rule applies to any cafe / restaurant Class I/II fire-resistance public room — any-point-to-nearest-exit straight-line distance must be ≤ 30 m (per GB 50016-2014 §5.5.17 item 4; cross-ref `codes.md`). Cafes deeper than ~ 20 m almost always need a second egress.
- **Single accessible route blocked by a chair-back.** ADA 2010 §403.5 requires a continuous 915 mm clear accessible route (per `codes.md`); a chair pulled out into the route trips it. Either widen the route to ≥ 1100 mm to absorb chair-back protrusion or fix the chair position with floor-mounted bases.
- **Cool-white (≥ 4000 K) ambient.** Pushes the cafe out of the hospitality 2700–3500 K band into the office band (per `lighting.md` Kelvin-by-space-type table) — kills the lounge-warmth read and reduces dwell time. Lock to 2700–3500 K.
- **Hard surfaces everywhere, no acoustic treatment.** Concrete floor + glass front + bare ceiling + hard tables produces RT60 well above 1.0 s — triggers the Lombard effect (per Acoustic Bulletin "The Lombard effect in hospitality": "spaces with RT60 < 0.7 s perform significantly better"). Always specify ceiling absorption + one absorptive wall + upholstered seating to land in the 0.4–0.6 s RT60 band (per Rindel BNAM 2018; cross-ref `acoustics.md`).
- **Per-table pendant too high.** Above 900 mm over the table the lux drops below the GB 50034-2013 餐厅 150 lx target (per Wosen LED summary) and the shade reads as ceiling clutter. Lock to 800–900 mm above table top.
- **Skipping per-table task layer.** Ambient alone at 100–150 lx is on the line — a per-table layer is what differentiates a cafe-lounge read from a cafeteria. Trips the "Lighting ≥ 2 layers" quality gate (per workflow spec § Quality Gates #2).
