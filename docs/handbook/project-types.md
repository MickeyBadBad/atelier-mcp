# Project Types and Multi-Space Organization

> Sources: Neufert Architects' Data, 4th ed. (Wiley-Blackwell) chapters Restaurants (pp. 187-189), Administration & Offices, Retail, Hotels & Catering; Time-Saver Standards for Building Types, 3rd ed. (De Chiara & Callender); Time-Saver Standards for Housing and Residential Development (De Chiara, Panero & Zelnik); GB 50352-2019 民用建筑设计统一标准; IBC 2021 Chapter 3 (Use and Occupancy Classification, §303 / §304 / §309 / §310); IBC 2021 Chapter 10 §1004.5 (Occupant Load Factors); Webstaurant Store, Patriquin Architects, RBNH Solutions on FOH/BOH adjacency.
> Last updated: 2026-04-29

## Purpose

This chapter answers the question "what spaces does a project of type X need, in what relative arrangement, at what total square-meter range?". It is the canonical lookup used by the Discovery questionnaire (`discovery.md`) and by the project-skeleton scaffolder. Each project type is bound to a canonical taxonomy slug that downstream tools branch on. Numeric ranges, occupant-load densities, and FOH/BOH ratios are all sourced from named publications, not inferred from training memory.

## Project type taxonomy

The questionnaire and scaffolder accept exactly these slugs:

- `residential_apartment` — multi-unit dwelling, single floor, shared building envelope (IBC R-2; GB 50096-2011 住宅).
- `residential_house` — single-family detached or townhouse, owns its envelope (IBC R-3 outside the strict scope of Chapter 3 above; GB 50096-2011 住宅).
- `cafe_lounge` — small assembly space focused on beverage service with light food (IBC A-2 below the 50-occupant threshold may revert to Group B; verify with AHJ).
- `restaurant_full_service` — table-service food and drink (IBC A-2 §303).
- `retail_boutique` — small mercantile space for display + sale of merchandise (IBC M §309).
- `office_small` — single-tenant workplace, ≤ ~25 workstations (IBC B §304).

Anything outside these six (hotel, school, hospital, factory) is out of scope for v1 and the questionnaire will refuse it.

## Per-type space programs

### residential_apartment

- **Required spaces** (per Time-Saver Standards for Housing and Residential Development, "Residential Program" sections — Living, Dining, Kitchen, Bedrooms, Bathrooms, Closets/Storage, Laundry):
  - entry / foyer (transition zone)
  - living room (social zone)
  - dining area (often combined with living or kitchen — Time-Saver explicitly lists "Combined Living-Dining" and "Combined Dining Area-Kitchen" as accepted programs)
  - kitchen
  - bedroom(s) (≥ 1)
  - bathroom(s) (≥ 1)
  - storage / closets
  - laundry (in-unit or shared per local code)
- **Adjacency:** kitchen ↔ dining adjacent; bedrooms clustered with bathroom(s) on the private side; entry-foyer mediates between corridor and living room (no direct sofa-from-corridor sightline).
- **Floor area range:** studio 25-37 m²; 1-bedroom 37-50 m²; 2-bedroom 61-77 m² (per UK Nationally Described Space Standard, "Technical Requirements", 2015 — 1B/2P shower 37 m², 1B/2P bath 39 m²; 2B/4P single-storey 70 m²; London Plan best-practice adds 10-14% on top). Catalan Decree 141/2012 sets a 20 m² minimum net for a studio (per "Housing Spaces in Nine European Countries", PMC8073340).
- **Typical occupant load:** N/A (residential — IBC 2021 §1004.5 lists residential at 200 gross sf/person but life-safety planning for multi-family uses dwelling-unit count, not load factor).

### residential_house

- **Required spaces** (per Time-Saver Standards for Housing and Residential Development, "Detached Single-Family" section, beginning ~p. 460):
  - entry / foyer
  - living room
  - dining room (often separate from kitchen in detached programs)
  - kitchen (frequently with eat-in nook — Time-Saver: "Most families want to eat some meals in the kitchen, so provision should be made for this even if a separate dining room is also provided")
  - bedrooms (typical program: 6 rooms / 3 bathrooms per ResearchGate "Floor plan of a typical single-family detached house" study, fig. 1)
  - bathrooms
  - laundry / utility
  - garage and/or workshop (per Time-Saver "Garages, Closets and Storage" section)
  - optional: home office, recreation room, outdoor living area
- **Adjacency:** Time-Saver three-zone model — Living/Social, Kitchen/Eating, and Sleeping/Private. "Nonworking areas should be segregated from working areas" (Time-Saver, "Kitchen / Eating Zone"). Combined rooms must share an opening of ≥ 8 ft (≈2.4 m) clear (per Time-Saver, "Living/Social Zone"). General traffic-lane minimum 3 ft 4 in (≈1.0 m) (per Time-Saver, "Circulation").
- **Floor area range:** No single canonical figure across regions. The ResearchGate Spain/Andalusia statistical study cites a typical 6-room / 3-bathroom detached house as the median (per ResearchGate fig. 259995970, Table 2). The UK Nationally Described Space Standard implies ≥ 84 m² for a 3-bedroom / 5-person dwelling and ≥ 95 m² for a 4-bedroom / 6-person dwelling (per assets.publishing.service.gov.uk space-standard PDF, 2015 update).
- **Typical occupant load:** N/A — same caveat as apartments.

### cafe_lounge

- **Required spaces** (per Neufert Architects' Data, 4th ed. "Restaurants" pp. 187-189; corroborated by Patriquin Architects "Restaurant Design: Space Flow"):
  - entry vestibule (climate / acoustic buffer)
  - host or order counter
  - seating area (mix of tables, banquettes, bar stools)
  - bar / beverage station
  - restroom(s) (per GB 50352-2019 §6.6 and IBC §2902 — count by occupant load)
  - back-of-house: prep kitchen, storage, staff
- **Adjacency:** counter ↔ seating ↔ restroom forms the patron loop; bar ↔ BOH prep is the shortest staff path; restrooms must NOT open directly into the dining floor without a vestibule (per GB 50352-2019 §6.6.4).
- **Floor area range:** No fixed Neufert range for "café" specifically; Neufert lists café dining-area allowance of less than restaurant ("apart from fast-food outlets, the least space required is in cafés" per Neufert 4th ed., "Restaurants"). Practical band 50-200 m² for a single-room neighborhood café.
- **Typical occupant load:** 15 net sq ft per person (≈1.4 m²/person) for "Assembly without fixed seats — unconcentrated (tables and chairs)" (per IBC 2021 §1004.5 Table). Standing-only zones: 5 net sq ft (≈0.46 m²/person).
- **FOH:BOH ratio:** Neufert kitchen-to-place ratios for café-class operations sit around 0.3-0.4 m² kitchen per 1.4-1.6 m² dining seat — i.e. BOH ≈ 20-25% of FOH (per Neufert 4th ed., pp. 187-189 dining-room / kitchen tables). Neufert dining allowance of 1.4-1.6 m²/place applies (standard 1.5).

### restaurant_full_service

- **Required spaces** (per Neufert 4th ed. "Restaurants" pp. 187-189; IBC §303 A-2 occupancy):
  - entry vestibule + waiting/host area
  - dining room (Neufert: "the main room of a restaurant is the customers' dining room")
  - bar (optional but common)
  - service stations (water, POS) within FOH
  - restrooms (separate M/F per code; accessible per ADA / GB 50763-2012)
  - BOH: receiving / loading dock, dry storage, refrigerated storage (walk-ins), prep kitchen, hot line, cold line, plating / pass, dish pit / warewashing, staff lockers, office, trash / recycling
- **Adjacency** (per Webstaurant Store "6 Principles for Layout & Flow" + Patriquin Architects + RBNH Solutions):
  - One-way flow: receiving → storage → prep → cook → plate → pass → dining; dirty dishes return via separate path to dish pit.
  - Pass / expo is the critical FOH-BOH bridge — locate it where servers can hand off and turn around without crossing the hot line.
  - Dish return must be near the dining-room entrance so servers don't cut through the hot line.
  - Two distinct FOH circulation paths: patron flow (entry → host → table → restroom → exit) and waitstaff flow (kitchen → tables → service stations → kitchen). Cross only at controlled handoff points.
  - Raw-protein prep separated from salad / plating (raw vs. cooked separation, per Webstaurant Store).
- **Floor area range:** Neufert dining allowance 1.4-1.6 m²/seat (standard 1.5); typical 40-80-seat full-service room → 60-130 m² FOH alone, plus BOH per ratio below. Neufert ceiling height: ≤ 50 m² → 2.50 m, > 50 m² → 2.75 m, > 100 m² → 3.00 m (Neufert 4th ed., "Restaurants").
- **Typical occupant load:** 15 net sq ft per person (≈1.4 m²/person) — Assembly tables-and-chairs; standing bar 5 net sq ft (≈0.46 m²/person); kitchen counted at the BOH side as Business 150 gross sq ft per person (per IBC 2021 §1004.5 Table; per IBC 2018 Code & Commentary commercial kitchens not associated with a dining room ≤ 2,500 sq ft can be classified Group B).
- **FOH:BOH ratio:** Neufert restaurant-class kitchen 0.4-0.5 m²/place vs. dining 1.4-1.6 m²/place → BOH ≈ 25-35% of FOH (per Neufert 4th ed., pp. 187-189). Hotel-restaurant FOH/BOH cross-check from Neufert "Hotels": total FOH 7.8-8.2 m² per guest room, BOH kitchen + store 6.3-5.4 m² per guest room (similar order of magnitude — corroborates).

### retail_boutique

- **Required spaces** (per Neufert 4th ed. "Retail" chapter; IBC §309 M occupancy):
  - entry / shopfront display window
  - sales floor (display fixtures, circulation)
  - fitting room(s) — for apparel
  - cash-wrap / point-of-sale counter
  - back-of-house: stockroom, receiving, staff break, restroom (staff and/or customer per code)
- **Adjacency:** entry ↔ sales floor ↔ cash-wrap forms the customer loop, with cash-wrap typically near the exit and sightline-dominant; stockroom directly behind cash-wrap so staff can fetch without leaving the floor; fitting rooms on the sales floor but visually screened.
- **Floor area range:** No single Neufert global range — Neufert "Retail" classifies typologies (specialized shops, retail chains, supermarkets, department stores). Working band for "boutique" 30-200 m². Anything ≥ ~500 m² migrates into shopping-arcade typology (per Neufert 4th ed., "Retail").
- **Typical occupant load:** 30 gross sq ft per person (≈2.8 m²/person) for basement and grade-floor mercantile; 60 gross sq ft per person (≈5.6 m²/person) for upper floors; 300 gross sq ft per person (≈27.9 m²/person) for storage/stock/shipping (per IBC 2021 §1004.5 Table; concise summary in usmadesupply.com IBC Chapter 10 reference).
- **FOH:BOH ratio:** No canonical Neufert ratio for boutique-scale retail in the surfaced tables; industry rule-of-thumb (per Spacefile "Retail back of house") is 70-80% sales floor / 20-30% BOH (stockroom + back areas) for fashion boutiques. Treat this as guidance, not code.

### office_small

- **Required spaces** (per Neufert 4th ed. "Administration & Offices" chapter; IBC §304 B occupancy):
  - reception / entry
  - workstations (cellular and/or open-plan)
  - meeting room(s) — at least one for ≥ 6 people
  - phone / focus room (1-person enclosed)
  - shared kitchenette / pantry
  - restroom(s)
  - copy / print / supply
  - server / IT closet (small)
  - storage / archive
- **Adjacency:** reception is the public face — visitors should not pass through workstations to reach a meeting room; place meeting rooms near reception so visitor traffic is contained. Workstation cluster forms the private-side; restrooms and print rooms accessible from the workstation cluster but not from reception alone.
- **Floor area range:** Neufert per-workstation allocation 11-15 m² (typical 13 m²) plus consulting / storage 1.5-4.2 m² (typical 2.5 m²) plus support spaces (sanitary 0.6-0.8, conference 0.3-1.0, archive 0.4-1.0, stores 0.4-1.5, canteen 0.6-1.6, entrance 0.2-0.7) per workstation (per Neufert 4th ed., "Administration & Offices"). For a 10-workstation office: ~150-200 m² total. Open-plan workstation: 12-15 m² per seat (per modern guidance, Flexopus office space guidelines, corroborating Neufert range).
- **Typical occupant load:** 150 gross sq ft per person (≈13.9 m²/person) for ordinary business areas; 50 net sq ft per person (≈4.65 m²/person) for "concentrated business use" (call centers, trading floors, data centers) per IBC 2021 §1004.8 (per IBC 2021 §1004.5 Table; usmadesupply.com summary).
- **FOH:BOH ratio:** Not a meaningful framing for offices — instead use Neufert workstation:support ratio. Workstation area ≈ 60-65% of net floor; support (meeting, archive, kitchenette, circulation, sanitary) ≈ 35-40% (derived from Neufert per-workstation allocation table).

## Cross-cutting adjacency principles

- **Kitchen ↔ Dining (residential):** adjacent, with a clear ≥ 8 ft / 2.4 m opening if combined, but no through-traffic — a dining room is not a corridor (per Time-Saver Housing, "Living/Social Zone").
- **Kitchen ↔ Dining (commercial):** kitchen is the BOH terminus, dining the FOH. Bridge them via a single pass / expo zone; never let patron circulation pass through prep. Dish return uses a separate path to avoid crossing the hot line (per Webstaurant Store, "6 Principles for Layout & Flow"; Patriquin Architects).
- **Entry ↔ Public rooms:** all project types need a transition zone (vestibule, foyer, entry threshold). Time-Saver: "There should be easy access to front and back doors". For commercial spaces in cold climates an air-lock vestibule reduces HVAC load (per ASHRAE 90.1 §5.4.3.3, referenced via codes.md).
- **Sleeping ↔ Bath (private cluster):** bedrooms and bathrooms should be on a single private circulation, screened from public rooms. The master bath should be directly accessible from the master bedroom without traversing public space.
- **Service vs. front-of-house separation (commercial):** staff, deliveries, and waste should have a path that never crosses the customer experience. In restaurants this is non-negotiable; in retail, deliveries route through the stockroom door, not the shopfront; in offices, the IT closet and copy room sit off the workstation cluster, not off reception.

## Blender collection layout

Every project, regardless of type, uses the same top-level Blender collection structure (per `docs/dev/specs/2026-04-29-interior-design-workflow-design.md`):

```
00_REFERENCES/    01_PLAN/        02_SHELL/       03_ZONES/
04_FINISHES/      05_FIXTURES/    06_LIGHTING/    07_CAMERAS/
08_RENDER_OUT/    09_EXPORT/      90_VARIANTS/
```

For multi-space projects, `03_ZONES/` is split into per-space sub-collections named after the space-type slugs from the questionnaire:

```
03_ZONES/
  Living/        (residential_apartment, residential_house)
  Dining/
  Kitchen/
  Bedroom_Master/
  Bedroom_2/
  Bath_Master/
  ...
03_ZONES/
  Entry/         (cafe_lounge, restaurant_full_service)
  Dining/
  Bar/
  BOH_Kitchen/
  BOH_Storage/
  Restroom/
```

Cross-reference: `discovery.md` defines the canonical space-type slugs; the scaffolder creates an empty sub-collection per space the user selects in the questionnaire.

## Worked examples

**Example 1 — Small speakeasy / shisha lounge:** A 6-zone speakeasy lounge, total floor area ≈ 90 m². Project type: `cafe_lounge`. Required spaces from this chapter: entry, counter, seating, restroom, BOH (when an existing back kitchen is preserved, BOH is "skinned" rather than rebuilt). FOH:BOH per Neufert ≈ 80:20, which typically matches existing footprints. Occupant load at IBC 15 net sq ft / person → ~50 m² FOH ÷ 1.4 m²/person ≈ 35 occupants — below the 50-occupant A-2 threshold so the local AHJ may permit Group B classification (verify on site).

**Example 2 — 2-bedroom apartment, 70 m²:** Project type: `residential_apartment`. Per UK NDSS, 2B/4P single-storey minimum 70 m². Spaces from this chapter: entry, combined living-dining, kitchen (open or galley), 2 bedrooms, 1 bathroom, in-unit storage. Apply the Time-Saver three-zone layout: living/dining + kitchen on the public side, two bedrooms + bath on the private side, separated by the entry transition.

## Common mistakes

- **Kitchen as a corridor.** Designing a residential kitchen so it sits on the through-path between living room and bedrooms forces all household traffic through the cooking zone. Time-Saver explicitly calls out that work areas should be segregated from non-working areas (per Time-Saver, "Kitchen/Eating Zone").
- **No transition zone at the entry.** Front door opening directly onto the sofa or directly into the dining room sacrifices acoustic/visual privacy and HVAC efficiency. Always include a foyer / vestibule, even a 1.5 m² niche.
- **FOH:BOH ratio inverted.** Treating the kitchen as a "leftover" space after the dining room is sized produces unworkable restaurants. Size BOH to match the seat count using Neufert's m²/place table, not by what's left over.
- **Occupant load undercounted in commercial.** Designers often count only seated patrons and forget standing zones (bar areas) at the much denser 5 net sq ft/person factor (per IBC 2021 §1004.5). This breaks egress calculations.

## See also

- [`codes.md`](codes.md) — egress widths, accessibility, and fire-area thresholds keyed to the IBC occupancy group cited above.
- [`spatial.md`](spatial.md) — clearance rules that apply within each space type's program.
- [`discovery.md`](discovery.md) — questionnaire that maps user input to a project-type slug from this chapter.
- `space-types/*.md` — per-space-type chapters (living room, kitchen, bedroom, dining, bar, etc.) referenced in the program lists above.
- `docs/dev/specs/2026-04-29-interior-design-workflow-design.md` — full Blender collection convention and citation policy.
