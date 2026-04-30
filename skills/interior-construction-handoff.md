---
name: interior-construction-handoff
description: Use when the user wants to produce construction-grade deliverables — "施工图", "construction docs", "BoM", "ready to ship", "give me the spec for the contractor", "交底文件", or signals the project is moving from design to build.
---

# interior-construction-handoff

Produce the final handoff package: dimensioned plans, elevations, sections, BoM (Bill of Materials), finish schedule, audit report.

## Required reading

1. `read_design_handbook(chapter="codes")` — validate against accessibility / fire / structural before handoff.
2. `read_design_handbook(chapter="render-output")` — final render set conventions.
3. `read_design_handbook(chapter="project-types")` — project-type-specific deliverables.

## Process

1. **Run a STRICT-mode `audit_interior_scene`** (all 🔴 + 🟡 + 🔵, gate #9 upgraded to 🔴).
2. **If any gate fails**, surface with citations. Do not let a failing gate ship to a contractor.
3. **Render the construction-grade view set** (hero + corner + detail + plan + elevation per the applicable space-type chapter and `render-output.md`).
4. **Generate dimensioned 2D outputs** (plan, key elevations) via `export_construction_docs` (lands in Slice 4 — for now, document this step as "pending Slice 4" and produce manual approximations).
5. **Produce the BoM** from `procurement.json` (when the SKU-tracking tools land in Slice 4) + the locked materials in `taste-profile.json`.
6. **Final audit-report** writes alongside renders.

## Note for Slice 1

Most `export_construction_docs` machinery lands in Slice 4. In Slice 1, this skill should:

- Guide the user through manual export of renders + a markdown BoM stub.
- Cite `codes.md` when explaining what a contractor will need (fire-rating tags, accessibility clearances).
- Set the user's expectation that machine-generated dimensioned drawings ship in Slice 4.
- Refuse to declare a project "ready to ship" when STRICT-mode audit gates fail.

## Cite

Every line item in the handoff package must trace to a handbook chapter for justification. Example:

> "Required path width 1.20 m at the corridor — per codes.md §accessibility (citing GB 50763-2012 §3.5)."
> "Materials packed for export — per render-output.md (citing Blender Manual: Color Management) and gate #9 (texture-packing for handoff)."
