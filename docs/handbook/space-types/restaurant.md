# Space Type: Restaurant (餐厅 / 全服务餐厅)

> Sources: Neufert *Architects' Data* (4th International English ed., Catering / Restaurant chapter on Scribd; 2nd International English ed. UCEB civbook archive PDF); GB 50034-2013 《建筑照明设计标准》Table 5.2.5 旅馆建筑照明标准值 / Table 5.2.4 餐饮 (gongbiaoku / zlglpt reproductions; Code of China English version); IBC 2021 §303 Assembly Group A-2 and Table 1004.5 Occupant Load (ICC Digital Codes; UpCodes Texas IBC 2021); ISO 3382-2:2008 reverberation-time definition (Rational Acoustics technical note); Commercial Acoustics "Target Reverb Times" reference; WELL Building Standard v2 Comfort §80 reverberation-time targets; Toast "Average Restaurant Square Footage 2026" industry-survey aggregation; CetraRuddy / Cini-Little FOH:BOH ratio guidance reproduced in TotalFood "Technical Know-How of Creating a Restaurant Floor Plan"; Layak Architect "Dining Room Dimensions". Last updated: 2026-04-29.

## Purpose

A full-service restaurant is a sit-down, table-service eatery where the dining room and the production kitchen occupy a single building envelope under one occupant load. Its job is to deliver paced multi-course meals with waitstaff service while sustaining conversation across each table — distinct from a quick-service / counter-order venue (different FOH:BOH ratio, different acoustic target) and from a cafe-lounge (different occupant-load factor, different lighting band). This chapter is the source of truth for AI agents scaffolding a 60–250 seat full-service restaurant; quick-service, cafeteria, and bar-only venues are out of scope.

## Typical area range

| Restaurant type | Total floor area (m²) | Source |
|---|---|---|
| Casual full-service, 50–80 seats | 150–250 m² | (per Toast "Average Restaurant Square Footage 2026" survey: casual full-service typically 150–250 m²) |
| Fast-casual (counter order, table seating) | 150–170 m² (1,600–1,800 ft²) | (per Toast "Average Restaurant Square Footage 2026": "fast-casual restaurants are typically between 1,600 and 1,800 square feet") |
| Fine dining, 80–150 seats | 200–500 m² (2,153–5,382 ft²) | (per Toast "Average Restaurant Square Footage 2026": "fine dining restaurants usually occupy 2,153 to 5,382 square feet") |
| Banquet / event-driven | 300 m²+ | (per Neufert 4th ed. Catering chapter on banquet-service typology and per CetraRuddy/Cini-Little ratio guidance reproduced in TotalFood floor-plan article) |

Per-seat floor area: a useful sanity check is **1.4–1.8 m² per dining seat** for the dining room alone (≈ 15 net sq ft / person at IBC 2021 Table 1004.5 = 1.39 m²/person, then loosened slightly for service aisles and host-stand) (per IBC 2021 Table 1004.5 unconcentrated tables-and-chairs row reproduced in Dalkita "Understanding Occupant Load" summary; Neufert 4th ed. Catering corroborates 1.4–1.8 m²/seat).

## FOH : BOH split

The single most important top-level layout decision. Allocates the building between revenue-generating dining and service-supporting kitchen / storage / staff.

| Service style | Front-of-house : Back-of-house | Source |
|---|---|---|
| Full-service casual & fine dining | **60 : 40** | (per CetraRuddy senior interior designer Kana Ahn quoted in TotalFood "Technical Know-How of Creating a Restaurant Floor Plan": "a typical allocation of space for dining and kitchen areas might use a 60:40 ratio; 60% is for the dining area, and 40% is for the kitchen") |
| Quick-service / fast-casual | 75 : 25 to 80 : 20 | (per Cini-Little design director Kip Serfozo quoted in TotalFood: "you might only need to dedicate 20% of the space to the kitchen, and 80% for the dining and other areas") |
| Banquet / fast-volume | up to 75 : 25 | (per TotalFood "Technical Know-How": "fast-service or banquet service establishments can have smaller kitchens... as little as 25% of the total floor space, for a 4 to 1 dining area to kitchen ratio") |

Kitchen sizing rule of thumb: **≈ 5 ft² (0.46 m²) of kitchen per dining seat** for a full-service operation (per BestOfExports "Restaurant Kitchen Size Guide": "approximately 5 square feet of kitchen area should be allocated for each dining seat"). A 100-seat full-service restaurant therefore plans ≈ 46 m² of kitchen, and a 60:40 FOH:BOH split puts the total floor area at ≈ 115 m² (kitchen) + 173 m² (dining) ≈ **288 m²**.

## Required clearances

All values are clear distances between finished furniture / wall faces. Cross-referenced with `spatial.md`.

| Clearance | Range (mm) | Source |
|---|---|---|
| Per-diner table width allocation | 600 (place setting) | (per Neufert 4th ed. Catering: "each place setting is around 60 cm wide and 30–40 cm deep") |
| Dining-table depth, plated service | 700–850 | (per Neufert 4th ed. Catering: "if the food is served on plates, then 70 cm is sufficient... overall width of 80–85 cm is suitable for a dining table") |
| Standard rectangular table sizes | 4-seater 1250 × 800; 6-seater 1870 × 800; 8-seater 2500 × 800 | (per Neufert *Architects' Data*: "4-seater dining table is 1.25 m × 0.8 m... 6-seater dining table is 1.87 m × 0.8 m... 8-seater dining table is 2.5 m × 0.8 m") |
| Dining-chair footprint | 450 × 450 | (per Neufert *Architects' Data*: "the standard size for a chair is 0.45 m × 0.45 m") |
| Dining-table top height | 750 | (per Neufert *Architects' Data*: "the height of a dining table is 0.75 m") |
| Dining-chair seat height | 400–450 | (per Neufert *Architects' Data*: "the height of a dining chair is 0.40–0.45 m") |
| Table edge → wall (chair only, no traffic) | ≥ 750 | (per Neufert 4th ed. Catering: "distance between table and wall ≥ 75 cm, because the chair alone requires a space of 50 cm") |
| Table edge → wall (chair + service traffic) | ≥ 1000 | (per Neufert 4th ed. Catering: "if the space between table and wall is also used for access, the distance should be ≥ 100 cm") |
| Round table around-clearance bonus | + 500 vs rectangular | (per Neufert 4th ed. Catering: "round tables need a little more space, a difference of up to 50 cm") |
| Service aisle between table groups | 900–1200 | (per Neufert 4th ed. Catering on "working aisle widths 0.90–1.20 m"; consistent with the table+chair-zone clearance from the table-to-wall traffic case) |
| Main service / circulation route through dining room | 1500–1800 | (per Neufert 4th ed. Catering "local traffic routes... 1.50–1.80 m") |
| Diagonal table-pack space saving vs orthogonal | up to 35 % | (per Neufert 4th ed. Catering: "diagonal arrangement of the tables generally takes up less space than an aligned pattern, with a space saving of up to 35%") |
| Wait station — small (serves ≤ 20 diners) | 0.6–0.9 m² | (per LoopNet "Six Considerations for Your New Restaurant Floor Plan" reproducing industry-standard wait-station sizing: "one small station should take up 6–10 sq ft, sufficient for 20 diners") |
| Wait station — large (serves ≤ 60 diners) | 2.3–3.7 m² | (per LoopNet reproducing same source: "one large central station should be anywhere from 25–40 sq ft. This would be sufficient for 60 diners") |

## Furniture inventory

### Must-have

- **Dining tables** sized for the target party mix — 2-tops at 700 × 700, 4-tops at 1250 × 800, 6-tops at 1870 × 800 (per Neufert *Architects' Data* dining-table sizes).
- **Dining chairs** at 450 × 450 footprint, 400–450 mm seat height (per Neufert *Architects' Data*).
- **Host stand / podium** at the entry — sized for one staff member + reservation system, ≈ 0.8 × 0.5 m (per Neufert 4th ed. Catering entry-zone diagrams).
- **Wait stations** distributed at one small station per 20 diners or one large central station per 60 diners (per LoopNet floor-plan considerations reproducing industry sizing).
- **Pass-through / kitchen-line interface** — the operational seam between FOH and BOH; design as a hard architectural element, not a furniture item.
- **Bar (in full-service venues with alcohol)** — a separate seat count, typically 8–12 stools, with its own occupant-load contribution per IBC 2021 Table 1004.5.

### Common

- **Banquettes** along one or two long walls — fixed seating sized at 600 mm per diner of backrest length (per IBC 2021 §1004.6 fixed-seating rule: "24 in (610 mm) of backrest length = 1 person").
- **Servers' computer station / POS terminal** — typically integrated into a wait station.
- **Acoustic ceiling cloud** or treated wall panels above the dining zone (see "Acoustic targets" below).
- **Decorative pendant lighting** above each table and a layered ambient field — see "Lighting layer recipe" below.

### Optional

- **Private dining room (PDR)** — separately calculated occupant load, often with its own service door from the kitchen line.
- **Open-kitchen counter seating** as a feature of the BOH/FOH seam (per Neufert 4th ed. Catering on contemporary open-kitchen typology).
- **Outdoor terrace / patio** — separately permitted, with its own fire-code occupant load.

## Acoustic targets

Restaurants are speech-intelligibility venues — patrons must be able to converse across the table without raising voices. Reverberation time is the primary metric.

| Restaurant atmosphere | RT60 target (s) | Source |
|---|---|---|
| Fine dining / intimate | 0.7 s | (per Commercial Acoustics "Target Reverb Times" reference: "fine dining or intimate restaurants often desire 0.7 second reverberation") |
| Casual full-service | 0.8–1.0 s | (per Commercial Acoustics "Target Reverb Times" reference: "restaurants at 0.7–1.1 seconds, ranging from intimate to sports bar") |
| Lively / sports-bar / high-energy | 1.0–1.1 s | (per Commercial Acoustics: "a lively sports bar or up-tempo venue may desire closer to 1.1 seconds. In the latter, a low reverb time may have the undesired effect of making it sound 'dead'") |
| Small enclosed dining room (≤ 280 m³) — well-treated | < 0.6 s | (per WELL Building Standard v2 Comfort feature §80: "spaces less than or equal to 280 m³ (10,000 ft³) at less than 0.6 seconds") |

Definition: RT60 is the time, in seconds, for sound pressure level to decay by 60 dB after the source stops, formally defined in ISO 3382-2:2008 §3.1 — "the duration required for the space-averaged sound energy density in an enclosure to decrease by 60 dB after the source emission has stopped" (per ISO 3382-2:2008 §3.1 reproduced in Rational Acoustics technical note).

Operationalising the acoustic target:
- A bare hard-surface dining room with concrete floor, drywall, and glass will land near RT60 = 1.5–2.0 s — well above the casual-dining ceiling and unworkable for fine dining (per Commercial Acoustics: glass and tile have NRC ≈ 0; hardwood and drywall absorb only ~ 15 % of sound energy).
- Acoustic interventions that move the room into target range: ceiling cloud or full acoustic ceiling, fabric-upholstered booth backs, drapery on at least one wall, and an area rug under the densest table cluster (per Commercial Acoustics: "acoustic wall panels, acoustical stretched fabric wall, plush furniture, carpet or other absorptive materials").
- Quality gate "Acoustics: RT60 within target" should be a render-time check — if the user or AI agent cannot point at absorption surfaces totalling ≥ 30 % of the room's exposed surface area, the room will overshoot the target (per Commercial Acoustics treatment-area guidance).

## Lighting layer recipe

| Layer | Target (lx) | Kelvin | Fixture | Source |
|---|---|---|---|---|
| Ambient — Western restaurant / bar / café atmosphere | 100 lx maintained, 0.75 m horizontal plane, Ra ≥ 80 | 2400–2700 K (warm) | Pendants over tables + perimeter cove or wall sconces | (per GB 50034-2013 Table 5.2.5 row "西餐厅、酒吧间、咖啡厅": 100 lx, 0.75 m horizontal plane, Ra 80) |
| Ambient — Chinese restaurant / banquet | 200 lx maintained, 0.75 m horizontal plane, UGR ≤ 22, Ra ≥ 80 | 2700–3000 K | Pendants + recessed downlights | (per GB 50034-2013 Table 5.2.5 row "中餐厅": 200 lx, 0.75 m horizontal plane, UGR 22, Ra 80) |
| Ambient — fine-dining / intimate atmosphere (designer adjustment) | 50–75 lx (one grade reduced from 西餐厅 baseline) | 2200–2400 K (deep warm) | Per-table pendant only, no general overhead | (per GB 50034-2013 §3.3 grade-adjustment rule allowing one-grade reduction for "very short-duration tasks... when accuracy/speed is unimportant... or when the building grade and functional requirements are lower"; standard illuminance grade 50 lx is in the Table 3.3 grade ladder) |
| Per-table accent | 2–4 × ambient (≈ 200–400 lx on the placemat) | matched to ambient ± 100 K | Table pendant or candle-equivalent | (per GB 50034-2013 §3.3 mixed-lighting `*` notation for task layering above general ambient; per Neufert 4th ed. Catering on per-table luminaire as the canonical fine-dining lighting move) |
| Bar / counter task | 200–300 lx on the bar top, Ra ≥ 80 | 2700 K | Under-shelf or pendant linear over the bar | (per GB 50034-2013 Table 5.2.5 row "酒吧间" 100 lx ambient with a one-grade lift to 200 lx for the bartender's task plane; corroborates Neufert 4th ed. Catering bar-design guidance) |
| Kitchen / BOH line | ≥ 500 lx maintained, Ra ≥ 80 | 4000 K (neutral, food-safe colour read) | Recessed troffers or vapour-tight linear | (per GB 50034-2013 Table 5.2.5 kitchen-row 500 lx; food-safety rationale for higher Kelvin per Neufert 4th ed. Catering kitchen-lighting commentary) |

Operationalising the recipe:
- **Lighting must be ≥ 2 layers in the dining room.** Ambient alone produces a flat fluorescent read; per-table pendants alone leave the perimeter dark and break the host-walking-the-room safety case (per GB 50034-2013 §3.3 mixed-lighting principle; quality gate "Lighting ≥ 2 layers" applies).
- **Kelvin coherence** within a layer to within ± 100 K to avoid the "two-suns" effect (per `lighting.md` Kelvin-coherence rule).
- The fine-dining 50 lx ambient is a **designer adjustment** under GB 50034-2013 §3.3 grade-reduction provision, not an explicit table entry — document the reduction rationale on the lighting plan (per GB 50034-2013 §3.3).

## Camera view set

| View | Lens (full-frame eq.) | Height (m) | Framing intent | Source |
|---|---|---|---|---|
| Hero (entry sightline into dining room) | 24–28 mm | 1.40–1.55 | Two walls + ceiling line + first table cluster; pendant array reads as a rhythm | (per `camera.md` "Hero shot" 21–28 mm sweet spot; Neufert 4th ed. Catering "first impression" entry-sequence principle) |
| Table-top detail (place setting + glassware) | 50–85 mm | object-centroid + 100–200 mm | Tight crop on plate, glass, candle, linen — proves food-photography readiness and styling density | (per `camera.md` "Detail crop" 50–85 mm; Neufert dining-table per-place 600 × 300–400 mm sets the centroid) |
| Bar elevation | 24–35 mm | 1.55 (standing) | Bar back-shelf + bottle wall + two stools in foreground | (per `camera.md` "Elevation" lens band; Neufert 4th ed. Catering bar typology) |
| Banquette long-axis (dining-room atmosphere) | 21–24 mm | 1.20–1.40 | Camera tucked at the banquette end, looking down the row of tables | (per `camera.md` "Corner shot" + Neufert 4th ed. Catering dining-room circulation diagrams) |
| Plan view (top-down, table count + service flow) | orthographic, top view | n/a | Whole-floor plan with seat count, service aisles, and BOH layout for code review and contractor handoff | (per `render-output.md` plan / elevation deliverable rules; IBC 2021 Table 1004.5 occupant-load documentation) |

## Cross-references

- Aisle and service-route widths sit in [`spatial.md`](../spatial.md) — keep the 900–1200 mm service, 1500–1800 mm main, and 750/1000 mm table-to-wall bands synchronised.
- Lighting Kelvin-coherence and per-table-pendant conventions live in [`lighting.md`](../lighting.md).
- IBC §303 Assembly A-2, IBC Table 1004.5 unconcentrated 15 net, IBC §1004.6 fixed-seating 24-in rule, GB 50034-2013 §5.2.5 illuminance, and ISO 3382-2 RT60 definition sit in [`codes.md`](../codes.md).
- Standard table / chair / banquette dimensions sit in [`furniture.md`](../furniture.md).
- Acoustic-treatment surface areas live in [`acoustics.md`](../acoustics.md).
- Output bundle (AgX, plan-view orthographic export, file-naming) lives in [`render-output.md`](../render-output.md).

## Worked examples

**80-seat casual full-service neighbourhood restaurant.**
Per IBC 2021 Table 1004.5, dining + bar at 15 net sq ft / person = 1.39 m²/person; kitchen at 200 gross sq ft / person = 18.6 m²/person. With 80 seats, dining ≈ 111 m². Apply 60 : 40 FOH : BOH (per CetraRuddy / TotalFood) → BOH ≈ 74 m² → kitchen ≈ 5 ft²/seat × 80 = 37 m² (per BestOfExports rule of thumb), the rest is dish, dry storage, walk-in, staff. Total floor area ≈ **185 m²**. Occupant load = 111/1.39 + 74/18.6 ≈ 80 + 4 ≈ **84 occupants** — well above the 50-occupant threshold, so panic hardware required and 2 exits required (per IBC 2021 §1006 / §1010). RT60 target 0.8 s — install ceiling cloud over dining + fabric banquette backs + one drapery wall + rug under the densest cluster (per Commercial Acoustics target reverb times). Ambient 100 lx, 2400 K (per GB 50034-2013 Table 5.2.5 西餐厅) + per-table pendants at 250 lx on the placemat (mixed-lighting under GB 50034-2013 §3.3).

**40-seat fine-dining tasting-menu venue.**
Dining ≈ 56 m² + bar / lounge 20 m² = 76 m² FOH; kitchen ≈ 5 ft²/seat × 40 = 19 m²; FOH:BOH at 60:40 wants BOH ≈ 50 m² so add prep, walk-in, dish, staff for ≈ 31 m² beyond the cooking line. Total ≈ **126 m²**. Occupant load = 76/1.39 + 50/18.6 ≈ 55 + 3 ≈ **58 occupants** — still above the 50-occupant threshold, panic hardware + 2 exits (per IBC 2021 §1006). RT60 target 0.7 s, room volume ≤ 280 m³ → push toward < 0.6 s for the WELL-aligned premium tier (per WELL v2 Comfort §80). Ambient designer-adjusted to ~ 50 lx, 2200–2400 K (per GB 50034-2013 §3.3 grade reduction documented on the lighting plan) + per-table pendants at 200 lx on the place setting.

## Common mistakes

- **Hard-surface dining room without acoustic budget.** A drywall + glass + concrete-floor dining room lands at RT60 ≈ 1.5–2.0 s, two to three times the target — patrons leave because they cannot converse, not because of the food (per Commercial Acoustics absorption-coefficient table; ISO 3382-2 RT60 definition).
- **Single ambient lighting layer, no per-table pendant.** Reads as cafeteria; fine-dining venues must use the §3.3 mixed-lighting layering (per GB 50034-2013 §3.3 mixed-lighting principle).
- **Tables jammed at 500 mm table-to-wall.** The chair alone needs 500 mm, leaving zero clearance for entry / exit; Neufert sets the floor at 750 mm chair-only and 1000 mm with service traffic (per Neufert 4th ed. Catering wall-clearance rule).
- **Kitchen sized below 5 ft² / seat in a full-service operation.** Producers stack tickets, plates miss windows, ticket times balloon — the dining room turns into a complaint queue (per BestOfExports kitchen-sizing rule of thumb; CetraRuddy / TotalFood 60:40 rationale).
- **Failing to count the bar separately in the occupant load.** The IBC 2021 Table 1004.5 row that applies to bar standing area is 5 net sq ft / person — much denser than the 15 net dining row. Skipping the separate calc under-counts egress requirements (per IBC 2021 Table 1004.5 standing-space row).
- **Treating fixed banquettes as movable seating.** IBC 2021 §1004.6 counts banquette by 24 in (610 mm) of backrest length per occupant — a 3 m banquette = 5 occupants, not "as many as fit" (per IBC 2021 §1004.6 fixed-seating rule).
