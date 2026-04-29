# Acoustics for Interior Design

> Sources: GB 50118-2010 民用建筑隔声设计规范 (Code for design of sound insulation of civil buildings), ASTM E90 (transmission loss test method), ASTM E413 (Sound Transmission Class), ASTM C423 (sound absorption test), NRC reference tables (Acoustical Surfaces, Commercial Acoustics), Beranek L.L. — *Concert Halls and Opera Houses: Music, Acoustics, and Architecture* (Springer, 2nd ed. 2004), International Building Code 2021 §1206.
> Last updated: 2026-04-29

## Purpose

Acoustics is the silent killer of restaurants, cafes, and open-plan offices. A beautiful space with the wrong hard-surface mix becomes a shouting match by 7pm — patrons leave early, staff lose their voices, and reviews say "great food, too loud." This chapter gives the AI agent the numbers it needs to decide: *do we need fabric panels, soft furniture, a ceiling cloud, or none of the above?*

## Key concepts

### NRC (Noise Reduction Coefficient)

A single number from **0.00 (perfect reflector) to 1.00 (perfect absorber)** — the average of a material's absorption coefficients at 250, 500, 1000, and 2000 Hz, rounded to the nearest 0.05 (per ASTM C423; lab repeatability ±0.05). NRC tells you how much sound a surface absorbs *on contact*; it does NOT tell you how much sound passes through to the next room — that is STC.

Use NRC when the problem is **echo, reverberation, or noise build-up inside one room**.

### STC (Sound Transmission Class)

A single-number rating of how well a partition (wall, floor, door) **blocks airborne sound from passing through**. Determined by curve-fitting transmission-loss values from 125 Hz to 4000 Hz against a reference contour (per ASTM E413; underlying transmission-loss test per ASTM E90). Higher = more isolation. STC 25 = normal speech intelligible through wall; STC 50 = loud speech barely audible; STC 60+ = sensitive use (per ASTM E413, ASTM E90).

China's GB 50118-2010 uses ISO-based **Rw + C** (weighted sound reduction index) rather than STC; the two metrics typically differ by 0–2 dB and are practically interchangeable for design intent (per GB 50118-2010 §2; ASTM E413 corroborates).

### RT60

The time, in seconds, for sound pressure to decay by 60 dB after the source stops. Long RT60 = echoey, fatiguing, unintelligible speech because vowels mask consonants (per Beranek 2004, Ch. 4 *Reverberation Time*). Short RT60 (< 0.3 s) = "dead" room, feels unnatural. RT60 scales with room volume and is reduced by absorptive surfaces and people in the room.

## NRC by material

Values are typical mid-range references; specific products vary with thickness, density, and mounting (per ASTM C423).

| Material | NRC (typical) | Source |
|---|---|---|
| Bare smooth concrete | 0.00–0.05 | (per Acoustical Surfaces / Commercial Acoustics absorption tables) |
| Painted concrete or plaster wall | 0.05 | (per Commercial Acoustics absorption tables) |
| Gypsum drywall (painted) | 0.05–0.10 | (per Commercial Acoustics absorption tables) |
| Glass (window, fixed) | 0.05 | (per Commercial Acoustics absorption tables) |
| Hardwood floor | 0.10–0.15 | (per Commercial Acoustics absorption tables) |
| Ceramic tile | 0.02–0.05 | (per Acoustical Surfaces) |
| Brick (exposed) | 0.03–0.05 | (per Commercial Acoustics absorption tables) |
| Low-pile carpet on slab | 0.15–0.20 | (per Acoustical Surfaces) |
| Carpet on padding/foam | 0.30–0.55 | (per Commercial Acoustics absorption tables) |
| Heavy fabric drape (gathered) | 0.55–0.75 | (per Commercial Acoustics absorption tables) |
| Upholstered seat (occupied) | 0.55–0.80 | (per Beranek 2004, audience absorption tables) |
| 25 mm fabric-wrapped fiberglass panel | 0.75–0.90 | (per Commercial Acoustics; AlphaSorb product data) |
| Mineral-fiber acoustic ceiling tile (standard) | 0.50–0.65 | (per Commercial Acoustics absorption tables) |
| High-NRC ceiling cloud / panel | 0.85–1.00 | (per USG Mars High-NRC, BASWA acoustical plaster product data) |

Rule of thumb: if the room is more than ~70% **NRC ≤ 0.10** surfaces by visible area, expect an acoustic problem.

## STC thresholds by space

| Partition / wall | Min STC | Source |
|---|---|---|
| Residential party wall (between dwelling units) | **STC 50** (lab) / NIC 45 (field) | (per IBC 2021 §1206; ASTM E413; LA Municipal Code §91.1206 corroborates) |
| Residential party floor/ceiling | **STC 50** + IIC 50 (impact) | (per IBC 2021 §1206) |
| China — residential party wall/floor | **Rw + C ≥ 45 dB** (mandatory) | (per GB 50118-2010 §4.2.1, §4.2.2 — mandatory clauses) |
| Hotel guest room partition | **STC 50+** | (per IBC 2021 §1206 — hotels treated as dwelling units) |
| Hotel corridor entry door | **STC 26+** with perimeter seal | (per LA Municipal Code §91.1206; IBC 2021) |
| Office demising wall (general) | STC 35–45 | (per industry practice; ASTM E413 commentary) |
| Office speech-privacy wall (HR, exec) | STC 45–50 | (per industry practice; STC standard contour) |
| Hospital / studio sensitive partition | STC 55+ | (per industry practice; IBC sensitive-use guidance) |

**Caveat (per ASTM E413):** STC is calibrated against speech spectra and does NOT predict isolation from low-frequency sources (subwoofers, HVAC rumble, traffic). For those, specify Rw + Ctr or do a banded analysis.

## RT60 targets by space

| Space | RT60 target (s, occupied) | Source |
|---|---|---|
| Restaurant / cafe (speech intelligibility) | **0.5–0.8 s** | (per WELL Building Standard acoustic comfort; tertiary-sector benchmark ~0.55 s for company restaurants — Phonotech / commercial-acoustics) |
| Cafe / bar with music program | 0.6–1.0 s | (per restaurant acoustic design references; Beranek 2004 speech vs. music trade-off) |
| Open-plan office | 0.4–0.6 s | (per WELL Standard; commercial-acoustics guidance) |
| Private office, meeting room | 0.5–0.7 s | (per Phonotech tertiary-sector benchmark ~0.77 s; WELL) |
| Classroom (speech-critical) | 0.4–0.6 s | (per ANSI S12.60 referenced in Acoustical Society of America guidance) |
| Residential living room | 0.4–0.6 s | (per industry practice; commercial-acoustics) |
| Concert hall (symphonic, occupied) | 1.8–2.2 s @ 500–1000 Hz | (per Beranek 2004, *Concert Halls and Opera Houses* Ch. 4 + appendix data tables) |
| Opera house (occupied) | 1.4–1.8 s | (per Beranek 2004) |
| "Dead" zone — avoid for social spaces | < 0.3 s | (per SVANTEK / NTi room-acoustics guidance) |

For a typical small cafe (60–80 m², ~3 m ceiling, hard tile / SPC floor + plaster ceiling + glass front): expect untreated RT60 of **1.5–2.0 s** — well into "noisy restaurant" territory. Target **0.6 s** occupied.

## Acoustic-fix recipes

Coverage matters as much as panel NRC: an NRC-0.90 panel covering 15% of room surface absorbs *less* total energy than NRC-0.75 covering 35% (per Commercial Acoustics — *Coverage by Application*). Recipes assume mid-volume rooms (60–150 m²).

1. **Ceiling cloud panels** — single best lever for global RT60 reduction; ceiling is the largest uninterrupted surface in most rooms. Use NRC 0.85+ panels (e.g., USG Mars High-NRC at NRC 0.90, fabric-wrapped fiberglass at NRC 0.85–0.95). Target **25–40% ceiling coverage** for cafes/restaurants; **30–50%** for open offices; suspend with 100–300 mm air gap to extend low-frequency absorption (per Commercial Acoustics; AlphaSorb cloud product data).
2. **Fabric wall hangings / panels at first-reflection points** — wrap wall behind diners or workstations. 25 mm fabric-wrapped fiberglass at NRC 0.75–0.90, covering **20–30% of wall area** concentrated at ear-height, gives audible improvement (per Commercial Acoustics — *Open offices NRC 0.70–0.85*).
3. **Soft furniture density** — upholstered banquettes, fabric chairs, heavy drapes contribute meaningfully: an occupied upholstered seat absorbs roughly the same as a 0.5 m² acoustic panel (per Beranek 2004, audience absorption tables). For a dense-seating cafe, this can carry 30–40% of the absorption budget.
4. **Carpet or rug on floor** — drops floor NRC from 0.10 (hardwood) to 0.30–0.55 (carpet on pad). For a hard-floor design (SPC plank, polished concrete, etc.), use **area rugs under banquette zones** — captures most of the acoustic benefit without losing the design intent (per Commercial Acoustics flooring values).
5. **Bookshelves with irregular contents** — diffusion + mid-frequency absorption; cheap and visually consistent with speakeasy aesthetic.
6. **For STC (between rooms), not NRC:** mass + decoupling + sealed perimeter. Double-stud wall with mineral wool + resilient channels reaches STC 55–60; a single layer of 12 mm gypsum on wood studs is only ~STC 33 (per IBC §1206 commentary; ASTM E90 test data).

## Worked examples

**Example 1 — Cafe, 70 m² hard-shell.**
Floor SPC plank (NRC 0.10), painted plaster walls (0.05), exposed concrete ceiling (0.02), large glass storefront (0.05), wood bar top (0.10). Total absorption: very low → estimated RT60 ~ 1.7 s untreated. Add: ceiling cloud panels at NRC 0.85 covering 30% of 70 m² ceiling = 21 m² absorptive ceiling, plus fabric-back banquettes along one wall. Predicted occupied RT60: **~0.6 s** — speech-friendly (per Sabine equation; Beranek 2004 Ch. 4).

**Example 2 — Apartment bedroom shared wall to neighbor.**
Existing: single-layer 12 mm gypsum on 90 mm wood studs, no insulation → STC ~33 (loud TV clearly audible). Required by IBC 2021 §1206 / GB 50118-2010 §4.2.1: STC 50 / Rw+C ≥ 45 dB. Fix: add 50 mm mineral wool in cavity, add resilient channels + second layer 12 mm gypsum, seal perimeter with acoustic sealant → STC ~52–55 (per ASTM E90 test data for similar assemblies).

## Common mistakes

1. **All-hard-surface cafe.** Concrete + glass + tile + metal "industrial chic" with zero absorption. RT60 hits 1.8–2.5 s; patrons shout, staff burn out. Always budget at least 25% ceiling coverage of NRC-0.80+ material.
2. **Open-plan office without NRC ceiling.** Drop ceiling at NRC 0.50 is the floor-level minimum, not the target — target NRC 0.80+ (per Commercial Acoustics — *Open offices*). Speech privacy in open plan also requires sound masking, not just absorption.
3. **Confusing STC with NRC.** Putting fabric panels on a thin wall does NOT make it STC-rated — that requires mass and decoupling. NRC fixes echoes inside a room; STC blocks sound from leaving it.
4. **Chasing NRC 0.95 over coverage area.** A 0.95 panel at 10% coverage loses to a 0.80 panel at 30% coverage (per Commercial Acoustics — *Coverage area matters more than the individual panel NRC*).
5. **Ignoring flanking paths.** A great STC-55 wall with an under-door gap, an unsealed electrical outlet box, or HVAC ducting that bridges both rooms performs at STC ~35 in the field. Field-measured NIC is typically 5+ points below lab STC for this reason (per IBC 2021 §1206 lab-vs-field clause).

## See also

- `materials.md` — material choice impacts NRC; specifies finish products with absorption data.
- `space-types/restaurant.md`, `space-types/office.md`, `space-types/residential.md` — per-space acoustic priorities and targets.
- `codes.md` — full GB 50118-2010 + IBC §1206 cross-reference, including impact-noise (IIC) requirements not covered here.
- `lighting.md` — secondary: hard reflective ceilings affect both light bounce and acoustic reflection; coordinated treatment.
