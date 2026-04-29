# Space Type: Small Office (小型办公室)

> Sources: Neufert *Architects' Data* (4th International English ed., Administration & Offices chapter on Scribd; 2nd International English ed. UCEB civbook archive PDF); ANSI/BIFMA G1-2013 Ergonomics Guideline for Furniture (Eureka Ergonomic interpretive summary; Uplift Desk reproduction of the height-range envelope); GB 50034-2013 《建筑照明设计标准》Table 5.2.1 办公建筑照明标准值 (gongbiaoku / zlglpt reproductions; Code of China English version); ANSI/ASHRAE Standard 55-2020 *Thermal Environmental Conditions for Human Occupancy* (Wikipedia summary of the PMV comfort zone; SimScale "What is ASHRAE 55"); IBC 2021 §304 Business Group B and Table 1004.5 Occupant Load (UpCodes Texas IBC 2021; Bellevue Office Use Occupant Load Calculation; Dalkita "Understanding Occupant Load"); *Time-Saver Standards for Building Types* (3rd ed., Commercial / Office section on Scribd); Knoll "Office Ergonomic Standards" white paper. Last updated: 2026-04-29.

## Purpose

A small office is a single-tenant or single-team workspace of roughly 50–500 m² serving 4–40 people, typically a mix of cellular private offices, an open-plan workstation pool, one or two meeting rooms, and shared support (pantry, copy, restrooms). Its job is to deliver heads-down work + scheduled collaboration + occasional client reception under one occupant load. Out of scope: large corporate floor plates with floor-by-floor zoning, coworking with 100+ desks, and call centres / trading floors (which IBC classifies separately as "concentrated business use" per IBC 2021 §1004.8). This chapter is the source of truth for AI agents scaffolding small-office scenes.

## Typical area range

| Office configuration | Sales / usable floor area (m²) | Source |
|---|---|---|
| 4–8 person team, all open-plan + 1 phone room | 50–100 m² | (per Neufert 4th ed. Administration & Offices "single-room offices" typology and grid-module guidance: 1.50 m grid × 12.50 m building depth = economical single-office form) |
| 12–25 person team, mixed cellular + open-plan + 1–2 meeting | 150–300 m² | (per Neufert 4th ed. Administration & Offices "combi-office" principle; per-person 4.5 m² (employee) → 6.7 m² (secretary) → 8.3 m² (manager) ladder) |
| Up to ~ 40 person small-office tenant slot | 300–500 m² | (per Neufert 4th ed. Administration & Offices and IBC 2021 Table 1004.5 business-occupancy 150 gross sq ft / person → 14 m²/person at the IBC density floor sets the upper envelope) |

Density check: per IBC 2021 Table 1004.5, business-area occupant-load factor is **150 gross sq ft / person** (≈ 13.94 m²/person) (per IBC 2021 Table 1004.5 reproduced in Dalkita "Understanding Occupant Load" and on UpCodes Texas IBC 2021). Conference rooms with tables and chairs use the unconcentrated assembly factor of **15 net sq ft / person** (≈ 1.39 m²/person) — substantially denser, calculated by function-of-space rather than occupancy classification (per IBC 2021 Table 1004.5 unconcentrated row; building-code-forum interpretive guidance reproduced in Dalkita).

Neufert per-person ladder (American study cited in Neufert 4th ed.): office employee 4.5 m² · secretary 6.7 m² · departmental manager 8.3 m² · director 13.4 m² · vice president 28.0 m² (per Neufert *Architects' Data* 4th ed. Administration & Offices "personal floor area" reproduction).

## Required clearances

All values are clear distances between finished furniture / wall faces. Cross-referenced with `spatial.md`.

| Clearance | Range (mm) | Source |
|---|---|---|
| Workstation zone depth (desk + chair pull-back + shelf) | 2200 | (per Neufert 4th ed. Administration & Offices: "the workstation zone depth is 2.20 m (80 cm desk, 1 m movement area, 40 cm shelf behind)") |
| Resulting clear room depth, two-back-to-back workstations | 4400 | (per Neufert 4th ed. Administration & Offices: "with 10 cm wall thickness, this gives 4.40 m clear room space") |
| Building depth, central-corridor offices | 12000–13000 | (per Neufert 4th ed. Administration & Offices: "the usual depth of buildings with central corridors is 12–13 m") |
| Daylight-penetration rule of thumb | D = 1.5 × H (window head height) | (per Neufert 4th ed. Administration & Offices: "rule of thumb: D = 1.5H, where D is the depth of light penetration and H is the height of the window head") |
| Workstation circulation aisle (one person) | ≥ 900 | (per Arcedior "Open Office Layout: Standard Distances & Clearances 2025" reproducing planning-standard circulation: "circulation between desks should be a minimum of 90 cm / 35.5"") |
| Two-person passing aisle | ≥ 1500 | (per Arcedior open-office reproduction of the same planning standard: "up to a spacious 150 cm / 59.1" which allows for two") |
| Main internal corridor | 1500–1800 | (per Time-Saver Standards 3rd ed. Commercial / Office "main streets" 150–240 cm; consistent with Neufert's 1.50–1.80 m local-traffic band) |
| Desk height — fixed | 720–740 | (per BIFMA G1-2013 reproduction in Eureka Ergonomic "BIFMA Workstation Ergonomics" summary: "fixed-height desks are usually around 29 inches / 73 cm") |
| Desk height — sit-stand adjustable | 559–1181 (22–46.5 in) | (per ANSI/BIFMA G1-2013 reproduced in Uplift Desk's commercial-height-range PDF: "minimum height of 22″ to a maximum height of 46.5″... accommodates 90% of the US population... 5th percentile of women to the 95th percentile of men") |
| Monitor viewing distance | 500–1000 (≈ 20–40 in) | (per OSHA Computer Workstations eTool reproduced in Eureka Ergonomic BIFMA summary: "your monitor should be placed at a viewing distance between 20 and 40 inches (50 to 100 cm) from your eyes") |
| Desk depth — minimum for 24-in viewing distance + workspace | ≥ 760 (30 in) | (per Knoll "Office Ergonomic Standards": "facility managers often rely on a '60/40 rule' for desk specification: for a monitor to be a healthy 24 inches away, you need a desk depth of at least 30 inches") |
| Conference room — per-occupant area | 1.4–1.8 m² | (per IBC 2021 Table 1004.5 unconcentrated tables-and-chairs row 15 net sq ft / person = 1.39 m²/person; Neufert 4th ed. corroborates 1.5–1.8 m²/seat in conference layouts) |
| ADA accessible workstation knee clearance | ≥ 685 (27 in) high × 760 (30 in) wide × 480 (19 in) deep | (per ADA 2010 Standards §902 reproduced in Knoll "Office Ergonomic Standards" white paper) |

## Furniture inventory

### Must-have

- **Workstation** = adjustable-height desk + ergonomic task chair + monitor arm. Desk fits the 22–46.5 in BIFMA height envelope; depth ≥ 760 mm to land monitor at 500–1000 mm from the eye (per ANSI/BIFMA G1-2013 height envelope; Knoll "60/40 rule" desk depth; OSHA viewing-distance reproduction).
- **Task chair** with adjustable seat height, lumbar support, armrests in the BIFMA-G1 ergonomic envelope (per ANSI/BIFMA G1-2013 reproduced in Eureka Ergonomic / Knoll office-ergonomic reference).
- **Conference / meeting table** for ≥ 1 room, sized to the team's typical meeting headcount + 2 (per Neufert 4th ed. Administration & Offices conference-room sizing).
- **Reception or arrival point** — even if just a small console + 1 chair, the entry zone is required for visitors and deliveries (per Neufert 4th ed. Administration & Offices entry-sequence guidance; IBC 2021 §1006 egress means).
- **Storage cabinet / personal locker** at ≥ 1 unit per workstation — paper, jacket, personal effects (per Neufert 4th ed. workstation 0.40 m shelf-behind allocation).

### Common

- **Phone room / focus pod** — 1 small enclosed room per ≈ 12 open-plan desks for calls and concentration work (per Neufert 4th ed. Administration & Offices combi-office typology; daylight-penetration rule pushes deep workstations into artificially-lit zones that are best converted into meeting / focus rooms).
- **Pantry / coffee point** with a counter, sink, and small refrigerator — drives the social diaphragm of the floor (per Neufert 4th ed. ancillary-space provisions).
- **Print / copy zone** centralised to one location, acoustically separated from the open-plan pool (per Neufert 4th ed. equipment-zone guidance).
- **Whiteboard or pinup wall** in or adjacent to the open-plan zone (per Time-Saver Standards 3rd ed. Office collaboration-space typology).

### Optional

- **Cellular private offices** for senior staff — Neufert's 2-grid-module 2.30 m wide is "too narrow for a senior staff member with seating for 3 visitors. Deeper workstations with video display units and other special equipment require the next largest room (2.70 m)" (per Neufert 4th ed. Administration & Offices office-grid commentary).
- **Library / archive room** for paper-heavy tenants.
- **Wellness / mother's room** — required by some jurisdictions for offices over a threshold size; verify locally.

## Lighting layer recipe

| Layer | Target (lx) | Kelvin | Fixture | Source |
|---|---|---|---|---|
| Ambient — ordinary office workstation | 300 lx maintained, 0.75 m horizontal plane, UGR ≤ 19, Ra ≥ 80 | 3500–4000 K (neutral, daylight-aligned) | Recessed direct/indirect linear fixtures or troffers | (per GB 50034-2013 Table 5.2.1 row "普通办公室": 300 lx, 0.75 m horizontal plane, UGR 19, Ra 80) |
| Ambient — high-spec / executive office | 500 lx maintained, 0.75 m horizontal plane, UGR ≤ 19, Ra ≥ 80 | 3500–4000 K | Higher-density linear or pendant array | (per GB 50034-2013 Table 5.2.1 row "高档办公室": 500 lx, 0.75 m horizontal plane, UGR 19, Ra 80) |
| Conference / meeting room | 300 lx maintained, dimmable to ≤ 50 lx for projection, UGR ≤ 19, Ra ≥ 80 | 3500–4000 K | Dimmable downlights or linear with separate AV-mode scene | (per GB 50034-2013 Table 5.2.1 row "会议室": 300 lx, 0.75 m horizontal plane, UGR 19, Ra 80) |
| Reception / front-of-house | 300 lx ambient, 200 lx accent on logo wall | 3000–3500 K | Wall-wash + downlights | (per GB 50034-2013 Table 5.2.1 reception row 200–300 lx; CIE-aligned office-lighting practice cited in lighting-standard compilations) |
| Task — desk-mounted | 500 lx maintained on the keyboard/document, Ra ≥ 80 | matched to ambient ± 200 K | Adjustable desk lamp | (per CIE office-lighting recommendation reproduced in office-lighting-standard summaries: 500 lx for the focused-work plane; GB 50034-2013 §3.3 mixed-lighting principle) |
| Corridor / lobby | 100–150 lx, Ra ≥ 60 | 3500–4000 K | Recessed downlights | (per GB 50034-2013 Table 5.2.1 corridor / general circulation row 100 lx) |

Operationalising the recipe:
- **UGR ≤ 19 is non-negotiable for desk-bound work.** Glare ratings above 19 cause veiling reflections on screens and reading material — GB 50034-2013 sets this as a hard ceiling for office and conference rooms (per GB 50034-2013 Table 5.2.1 UGR column).
- **Daylight is the primary ambient layer when available.** Workstations within 4.5 m of a window head 3.0 m high meet the daylight-penetration rule of thumb D = 1.5H and may reach the 300 lx ambient target on daylight alone for much of the working day; deeper workstations require artificial light (per Neufert 4th ed. Administration & Offices daylight rule; GB 50034-2013 Table 5.2.1 maintained 300 lx target).
- **Conference rooms are dual-mode.** Default 300 lx for face-to-face working sessions, with an AV scene that drops the ambient ≤ 50 lx in the projection-screen zone while keeping perimeter at ≥ 100 lx for note-taking (per GB 50034-2013 Table 5.2.1 conference-room target; CIE projection-room guidance in office-lighting compilations).
- **Kelvin coherence** within a layer to within ± 200 K to avoid the patchwork-tile read across a grid of recessed fixtures (per `lighting.md` Kelvin-coherence rule).

## Thermal comfort target

ASHRAE 55 sets the comfort envelope for sedentary office work.

| Variable | Target | Source |
|---|---|---|
| Operative temperature, summer (light clothing 0.5 clo) | 23–26 °C | (per ANSI/ASHRAE Standard 55-2020 PMV-PPD method summarised in Wikipedia "ASHRAE 55" and SimScale "What is ASHRAE 55": comfort zone for "lightly clothed person (clothing insulation 0.5–0.7 clo) engaged in near sedentary physical activity (1.0–1.3 met)"; "upper limit of 26 °C assumes a relative humidity of 50%") |
| Operative temperature, winter (clo ≈ 1.0) | 20–23.5 °C | (per ANSI/ASHRAE Standard 55-2020 winter PMV envelope reproduced in Wikipedia "ASHRAE 55") |
| Relative humidity | 30–60 % typical; humidity ratio ≤ 0.012 kg H₂O / kg dry air | (per ANSI/ASHRAE Standard 55-2020 §5.2.1.1 graphic comfort-zone humidity-ratio cap reproduced in SimScale "What is ASHRAE 55") |
| PMV (Predicted Mean Vote) | −0.5 ≤ PMV ≤ +0.5 | (per ANSI/ASHRAE Standard 55-2020: "compliance is achieved if the conditions provide thermal neutrality, measured as falling between -0.5 and +0.5 on the PMV scale") |
| Air speed | ≤ 0.20 m/s for the basic PMV method | (per ANSI/ASHRAE Standard 55-2020: "use of the PMV model in this standard is limited to air speeds below 0.20 m/s") |
| Metabolic rate (sedentary office work) | 1.0–1.3 met | (per ANSI/ASHRAE Standard 55-2020 reproduced in SimScale "What is ASHRAE 55") |
| Clothing insulation | 0.5–1.0 clo | (per ANSI/ASHRAE Standard 55-2020 light-office-clothing assumption) |

## Camera view set

| View | Lens (full-frame eq.) | Height (m) | Framing intent | Source |
|---|---|---|---|---|
| Hero (open-plan from entry) | 24–28 mm | 1.40–1.55 | Two walls + ceiling line + workstation pool; daylight axis along the long edge | (per `camera.md` "Hero shot" 21–28 mm sweet spot; Neufert 4th ed. daylight-axis principle) |
| Workstation detail (single desk, ergonomic read) | 35–50 mm | 1.20–1.40 (seated eye-level) | Monitor + desk + chair + lamp — reads ergonomic compliance, not just aesthetics | (per `camera.md` "Detail crop" 35–50 mm; ANSI/BIFMA G1-2013 ergonomic-envelope visualisation) |
| Conference-room hero | 24–28 mm | 1.40–1.55 | Table + chairs + AV wall on a thirds intersection; reads as ready-to-meet | (per `camera.md` "Hero shot" + GB 50034-2013 conference-room ambient + AV-mode scene) |
| Reception axial | 28–35 mm | 1.55 | Symmetric framing onto the reception desk + brand wall | (per `camera.md` "Eye-level cross-room" framing) |
| Plan view (top-down, layout reference) | orthographic, top view | n/a | Whole-floor plan with workstation grid, meeting rooms, exits, and accessible-route overlay | (per `render-output.md` plan / elevation deliverable rules) |

## Cross-references

- Aisle and accessible-route widths sit in [`spatial.md`](../spatial.md) — keep the 900 mm one-person, 1500 mm two-person, and 4.4 m back-to-back-workstation room-depth bands synchronised.
- Lighting Kelvin-coherence and UGR conventions live in [`lighting.md`](../lighting.md).
- IBC §304 Business Group B, IBC Table 1004.5 business 150 gross + concentrated-business 50 gross + unconcentrated-conference 15 net rows, GB 50034-2013 §5.2.1 illuminance, ANSI/BIFMA G1-2013 ergonomic envelope, and ANSI/ASHRAE Standard 55-2020 thermal-comfort PMV sit in [`codes.md`](../codes.md).
- Standard desk / chair / conference-table dimensions sit in [`furniture.md`](../furniture.md).
- Output bundle (AgX, plan-view orthographic export, file-naming) lives in [`render-output.md`](../render-output.md).

## Worked examples

**12-person mixed cellular + open-plan startup, 200 m² floor.**
Workstation pool 8 desks × 4.5 m² = 36 m² (per Neufert 4th ed. employee-area allocation); 2 cellular offices × 13.4 m² = 26.8 m² (per Neufert director allocation); 1 conference room 12 m² (8-seat × 1.5 m²/seat); pantry 8 m²; reception 6 m²; circulation + restrooms ≈ 50 m²; balance is storage / IT. Occupant load: 200 m²(gross) ÷ 13.94 m²/person = **14 occupants** under IBC 2021 Table 1004.5 business 150 gross row — below the 50-occupant panic-hardware threshold, single exit acceptable per IBC 2021 §1006 (verify with AHJ on the second-exit travel-distance rules). Conference room is calculated separately at 8 seats / 1.39 m²/seat = 5.7 → **6 occupants** by function-of-space (per IBC 2021 Table 1004.5 unconcentrated row; building-code-forum guidance). Ambient lighting 300 lx, UGR 19, 4000 K (per GB 50034-2013 Table 5.2.1 普通办公室). Sit-stand desks at the BIFMA 22–46.5 in envelope (per ANSI/BIFMA G1-2013); monitors 600 mm from the eye on 760 mm-deep tops (per OSHA / Knoll). Thermal setpoint 24 °C summer / 22 °C winter, 30–60 % RH (per ANSI/ASHRAE Standard 55-2020).

**6-person legal practice, 80 m² floor, all cellular.**
3 cellular offices × 8.3 m² (managers) + 1 corner office × 13.4 m² + 1 small conference + reception + storage = ~ 80 m². Occupant load = 80 / 13.94 ≈ **6 occupants** — single exit, no panic hardware (per IBC 2021 Table 1004.5; §1006). Ambient 500 lx in client-facing offices (per GB 50034-2013 Table 5.2.1 高档办公室) and 300 lx in the workroom; conference room dimmable to AV mode.

## Common mistakes

- **UGR > 19 from over-bright ceiling fixtures or undimmed daylight glare onto screens.** Fails GB 50034-2013 Table 5.2.1 office UGR ceiling and produces measurable productivity loss (per GB 50034-2013 Table 5.2.1 UGR column).
- **Fixed-height 720 mm desk with no monitor arm.** Forces taller users (≥ 95th-percentile male, ~ 188 cm) into a hunched posture; ANSI/BIFMA G1-2013 expects the desk + monitor system to fit the 5th-percentile-female to 95th-percentile-male band (per ANSI/BIFMA G1-2013 height envelope reproduction).
- **Workstations placed deeper than 4.5 m from a 3 m-head window.** Beyond the daylight-penetration rule (D = 1.5H), so they require full-time artificial light — better repurposed as meeting / focus rooms (per Neufert 4th ed. Administration & Offices D = 1.5H rule).
- **Conference room calculated at the office 150 gross factor.** IBC 2021 Table 1004.5 explicitly applies 15 net for tables-and-chairs assembly use within an office building — a 12 m² conference room counts ≈ 9 occupants by function, not 1 occupant by occupancy class (per IBC 2021 Table 1004.5 unconcentrated row; Dalkita "Understanding Occupant Load" interpretive guidance).
- **Single-mode conference lighting with no AV scene.** 300 lx ambient is correct for face-to-face but washes out projected content; design a second scene that drops the screen-zone illuminance ≤ 50 lx while keeping note-taking perimeter ≥ 100 lx (per GB 50034-2013 §3.3 mixed-lighting principle; CIE office-lighting projection guidance).
- **No humidity control plan.** Below 30 % RH, occupants report dry eyes / static / mucus-membrane irritation; above 60 % RH, mould risk and the PMV envelope shifts. ANSI/ASHRAE Standard 55 caps humidity ratio at 0.012 kg H₂O / kg dry air — ignore at the spec stage and you cannot retrofit it cheaply (per ANSI/ASHRAE Standard 55-2020 §5.2.1.1).
