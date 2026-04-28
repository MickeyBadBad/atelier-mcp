# Building Codes for Interior Design

> Sources: GB 50096-2011 住宅设计规范, GB 50352-2019 民用建筑设计统一标准, GB 50763-2012 无障碍设计规范, GB 50016-2014 (2018 ed.) 建筑设计防火规范, ADA 2010 Standards for Accessible Design
> Last updated: 2026-04-29

## Purpose

This chapter is the regulatory backbone for the Interior Design Workflow MCP. It collects the minimum dimensional, accessibility, and fire-egress rules that an interior designer cannot legally violate, with one inline citation per number so a downstream skill (`validate_dimensions`, `validate_accessibility`, `validate_egress`) can quote the source. Numbers below are floors, not targets — `spatial.md` covers comfort-driven clearances above the code minimum.

## Scope and applicability

The Chinese GB codes cited here apply to projects built on the mainland: GB 50096-2011 governs **residential** dwelling units (套内), GB 50352-2019 is the **civil-building unified standard** (covers all民用建筑 except industrial / agricultural / military), GB 50763-2012 is the **accessibility** code that applies to all newly built / renovated public buildings and residential developments nationwide, and GB 50016-2014 (2018 amendment) is the **fire-protection design** code that governs both residential and public-building egress. Where a project is mixed-use (e.g. cafe + apartment above), each function is checked against its own scope.

ADA 2010 is included as a **secondary corroboration** for accessible-route widths and door clearances. It is the legal standard in the US only — but Chinese projects often borrow ADA's wheelchair turning radius (1525 mm) when GB 50763 is silent (it is not silent on most points).

## Rules

### Minimum room dimensions (residential)

- Living-room (起居室/厅) usable area minimum: **10 m²** (per GB 50096-2011 §5.2.2; soujianzhu.cn / jianbiaoku.com publication of the standard).
- Double bedroom (双人卧室) usable area minimum: **9 m²** (per GB 50096-2011 §5.2.1 item 1).
- Single bedroom (单人卧室) usable area minimum: **5 m²** (per GB 50096-2011 §5.2.1 item 2).
- Bedroom that doubles as living space (兼起居的卧室) minimum: **12 m²** (per GB 50096-2011 §5.2.1 item 3).
- Kitchen (厨房) usable area minimum: **4.0 m²** in a full bedroom + living + kitchen + bath unit; **3.5 m²** in the smallest combined unit (per GB 50096-2011 §5.3.1).
- Kitchen single-row equipment clear width: **≥1.50 m**; double-row clear distance between rows: **≥0.90 m** (per GB 50096-2011 §5.3.5).
- Bathroom (卫生间) with three fixtures (toilet + bathing + washbasin) usable area minimum: **2.50 m²** (per GB 50096-2011 §5.4.1).
- Bathroom with toilet + washbasin only: **≥1.80 m²**; toilet + bath: **≥2.00 m²**; toilet only: **≥1.10 m²** (per GB 50096-2011 §5.4.2).
- Bedroom / living-room interior net height: **≥2.40 m** (local low areas ≥2.10 m, low area ≤1/3 of usable area) (per GB 50096-2011 §5.5.2).
- Kitchen / bathroom interior net height: **≥2.20 m** (per GB 50096-2011 §5.5.4).
- Whole-unit usable area: **≥30 m²** (full layout) or **≥22 m²** (smallest combined-bedroom layout) (per GB 50096-2011 §5.1.2).

Note: §5.4.4 (bathroom may not sit directly above bedroom/living/kitchen of the unit below) is one of the **mandatory (强制性) provisions** of GB 50096-2011 — others on this list are recommended.

### Corridor / circulation widths

- Civil-building corridor minimum net height (where people normally pass): **≥2.0 m** (per GB 50352-2019 §6.3.3).
- Building connector (with traffic function) net width: **≥3.0 m** above ground, **≥4.0 m** underground, **≤9.0 m** maximum (per GB 50352-2019 §4.4.4).
- Note: GB 50352-2019 is a **unified general standard** and defers specific corridor widths per building type to the specialized standard (residential → GB 50096; commercial → GB 50016 egress widths). Do not cite GB 50352 for a specific residential corridor width — it does not publish one.
- Wheelchair-accessible indoor corridor: **≥1.20 m** (large public buildings with high pedestrian flow: ≥1.80 m) (per GB 50763-2012 §3.5.1 item 1).
- Wheelchair-accessible outdoor passage: **≥1.50 m** (per GB 50763-2012 §3.5.1 item 2).
- Wheelchair lane at ticket / checkout: **≥900 mm** (per GB 50763-2012 §3.5.1 item 3).
- ADA accessible-route walking-surface clear width: **915 mm (36 in)** continuously, narrowing to **815 mm (32 in)** only at point obstructions (per ADA 2010 §403.5 — corroborated via Access-Board Chapter 4 publication and corada.com/up.codes mirror; ADA 1991 §4.2.1 used the same numbers).
- Wheelchair turning space (T-shaped or circular): **1525 mm (60 in) diameter circle** or 60-in square with 36-in arms (per ADA 2010 §304.3.1 / §304.3.2 — Access-Board Chapter 3; GB 50763-2012 §3.5.3 item 4 corroborates with **直径不小于1.50 m** of turning space inside doors).

### Doors and openings

- GB 50352-2019 entry-vestibule rule: when both interior+exterior doors are open, the gap between them shall be **≥0.8 m**; if accessibility applies, defer to GB 50763 (per GB 50352-2019 §6.11 item 8).
- Accessible automatic door clear passing width: **≥1.00 m** (per GB 50763-2012 §3.5.3 item 2).
- Accessible swing / sliding / folding door clear passing width: **≥800 mm** (preferred ≥900 mm where conditions permit) (per GB 50763-2012 §3.5.3 item 3).
- Accessible door must have a **≥400 mm clear wall** on the latch side (per GB 50763-2012 §3.5.3 item 5).
- Accessible threshold / level change: **≤15 mm** (per GB 50763-2012 §3.5.3 item 7).
- ADA door clear width: **815 mm (32 in) minimum**, measured between the face of the door and the stop with the door open 90° (per ADA 2010 §404.2.3 — Access-Board / corada.com / up.codes mirrors).
- ADA door clear width for openings >610 mm (24 in) deep: **915 mm (36 in)** (per ADA 2010 §404.2.3, deep-opening clause).
- ADA door projections at 865-2030 mm (34-80 in) AFF: **≤100 mm (4 in)** into the clear opening (per ADA 2010 §404.2.3).
- Door maneuvering clearances (push/pull side, latch/hinge approach) governed by ADA 2010 §404.2.4 and Table 404.2.4.1 — the table specifies different clearance depths for front, hinge, and latch approaches; consult the source table directly when validating, as the values vary by approach direction (per ADA 2010 §404.2.4 / §404.2.4.1; cf. Access-Board Chapter 4).

### Fire egress

- Public-building room evacuation door to nearest safety exit, located **between two safety exits**, single/multi-story Class I/II fire resistance — generic "other" public buildings: **40 m maximum**; located on a dead-end (袋形走道) corridor: **22 m maximum** (per GB 50016-2014 §5.5.17 Table 5.5.17, "其他建筑" row, single/multi-story 一、二级耐火等级 columns; tpy119.com / jianbiaoku.com mirrors of the standard).
- Public-building hotel-specific values: high-rise hotel **30 m** between exits / **15 m** dead-end; single/multi-story hotel **40 m / 22 m** (Class I/II); the 25 % sprinklered uplift below applies (per GB 50016-2014 Table 5.5.17, hotel row).
- Sprinkler uplift: when the entire building has automatic sprinklers, the §5.5.17 distances increase by **25 %** (per GB 50016-2014 §5.5.17 Note 3; this is a strong-provision (mandatory) note).
- Open-air external corridor uplift: rooms opening onto an open exterior corridor add **+5 m** to the table value (per GB 50016-2014 §5.5.17 Note 1).
- Travel within room → room evacuation door: shall not exceed the dead-end-corridor value in Table 5.5.17 (per GB 50016-2014 §5.5.17 item 3).
- Large-room special rule (Class I/II fire resistance, ≥2 exits, theater / exhibition / restaurant / sales hall): any-point-to-nearest-exit straight-line distance **≤30 m**; sprinklered → +25 % (per GB 50016-2014 §5.5.17 item 4).
- Residential travel distance, high-rise (一、二级耐火等级 高层) — unit door to nearest safety exit, between two exits: **40 m max**; on a dead-end corridor: **20 m max** (per GB 50016-2014 §5.5.29 Table 5.5.29, high-rise row; full-building sprinklered → 50 m / 25 m via the §5.5.29 Note 3 25 % uplift).
- Residential single/multi-story (一、二级耐火等级): **40 m / 22 m** between exits / dead-end (per GB 50016-2014 Table 5.5.29).
- Residential straight-flight stair (跃层式) inside a duplex unit: stair distance counted as **1.5× horizontal projected length** (per GB 50016-2014 §5.5.29 Note, mirrored in §5.5.17 commentary).
- §5.5.29 is a **mandatory (强制性) provision** of GB 50016-2014 — the table values cannot be exceeded under any planning argument; only the documented Notes (sprinklers, exterior corridor) raise them.
- Number of safety exits: a single safety exit is allowed for a small room only when (a) area <50 m² with evacuation door net width ≥0.90 m, or (b) any-point-to-evacuation-door distance ≤15 m, area ≤200 m², and door net width ≥1.40 m; otherwise ≥2 exits (per GB 50016-2014 §5.5.15 — mandatory).

## Worked examples

**Example 1 — A 4 m × 6 m residential living room (24 m²).**
24 m² ≥ 10 m² minimum (per GB 50096-2011 §5.2.2). Pass. Note that §5.2.3 also asks for a continuous straight wall **>3 m** for furniture placement — a 6 m wall easily clears that.

**Example 2 — Small-commercial space (cafe / lounge / boutique), ground-floor, sprinklers absent.**
A single-story public building with presumed Class II fire resistance ("其他建筑" row of GB 50016-2014 Table 5.5.17). Without sprinklers, any seat must be ≤22 m straight-line from the nearest exit if reached via a dead-end (single-direction) path, or ≤40 m if it sits between two exits. With a fire sprinkler upgrade, both numbers grow by 25 % to 27.5 m / 50 m respectively (per §5.5.17 Note 3). Layout decisions must therefore not push any occupant more than 22 m down a single-direction corridor toward the rear exit.

**Example 3 — Accessible bathroom door retrofit, GB + ADA cross-check.**
GB 50763-2012 §3.5.3 item 3 requires **≥800 mm** clear passing width on a swing door; ADA 2010 §404.2.3 requires **≥815 mm (32 in)**. Specifying an 850 mm clear opening satisfies both. GB 50763-2012 §3.5.3 item 4 additionally requires a **1.50 m turning circle** inside the door — the same as ADA 2010 §304.3.1 (1525 mm). One number, two citations.

## Common mistakes

- **Citing GB 50352 for a residential corridor width.** GB 50352-2019 only sets a 2.0 m corridor net-height floor (§6.3.3); it explicitly defers specific widths to building-type standards. Cite GB 50096 or GB 50016 instead.
- **Forgetting the §5.5.17 / §5.5.29 sprinkler uplift.** A "violating" 25 m dead-end corridor becomes compliant the moment the building is fully sprinklered (per GB 50016-2014 §5.5.17 Note 3 / §5.5.29 Note 3 — +25 %). Always check sprinkler status before calling a layout non-compliant.
- **Conflating nominal door size with clear width.** ADA 2010 §404.2.3 measures clear width with the door **open 90°, between the door face and the stop** — a 32-in (815 mm) nominal door does **not** give 32 in clear because of door thickness and hinge geometry. Specify a 36-in (915 mm) leaf to be safe.
- **Treating ADA as authoritative on a Chinese site.** ADA only governs in the US. On a Chinese project, GB 50763 is the binding accessibility code; ADA is a corroborating reference, not a substitute.
- **Pushing bedroom area below 9 m².** GB 50096-2011 §5.2.1 reduced double-bedroom minimum from 10 m² (1999 version) to 9 m² in the 2011 edition, but Beijing's local DB standard kept 10 m². Check the local DB before assuming the national floor.

## See also

- `spatial.md` — non-code clearances (sofa-to-coffee-table, dining-chair pull-out, kitchen aisle comfort) that sit **above** the code minimum
- `lighting.md` — illuminance values that are also code-defined (GB 50034)
- `furniture.md` — door swing zones and furniture-clear zones at door arcs
- `space-types/` — per-space-type chapters reference these section numbers when validating dimensions
