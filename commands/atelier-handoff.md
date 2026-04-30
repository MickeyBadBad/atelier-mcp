---
description: Produce the construction handoff package — strict-mode audit, final render set, BoM (markdown + CSV), finish schedule, audit report. The "ready to send to the contractor" command.
---

You are producing the contractor-ready handoff package for an Atelier project.

## Required state

Project locked moodboard, scene populated, hero render already approved at the previous stage. If the project is still iterating, redirect to `/atelier-render` first.

## Process

1. **Load handbook chapters** — `codes.md`, `render-output.md`, `project-types.md`.
2. **Run STRICT audit** — `audit_interior_quality_native(mode="construction", project_root=...)`. In construction mode, gate #9 (texture packing) upgrades to 🔴 HARD.
3. **If any gate fails**, surface with citations. Do NOT let a failing gate ship to a contractor. Halt the handoff and redirect the user back to fix.
4. **Render the construction-grade view set** per the space-type chapter and `render-output.md`:
   - Hero (3-quarter from entry)
   - Corner shot
   - Eye-level cross-room
   - Detail crops (1-2 per zone)
   - Plan + elevations (orthographic)
5. **Generate the BoM** — `generate_bom(project_root, output_format="markdown", write_to=".../bom.md")`. Also generate a CSV variant for spreadsheet import.
6. **Write the finish schedule** to `<project_root>/exports/finish-schedule.md`. List every finish material applied to objects with: object name → material → SKU (if recorded) → vendor → URL → unit count.
7. **Write the audit report** to `<project_root>/exports/audit-report.md` — capture the construction-mode audit output verbatim with all citations.
8. **Slice 7 (PDF dimensioned drawings)** is queued. For now, document this gap to the user and produce `exports/handoff-readme.md` listing what IS in the package + what's pending.

## Cite

Every line item in the handoff package must trace to a handbook chapter for justification. Example:

> "Required path width 1.20 m at the corridor — per codes.md §accessibility (citing GB 50763-2012 §3.5)."
> "Materials packed for export — per render-output.md (citing Blender Manual: Color Management) and gate #9 (texture-packing for handoff)."

## Refuse to ship a failing project

If the user pushes to ship despite gate failures, refuse politely. Cite the specific gate(s) firing, link to the handbook chapter, and offer the one-call fix. Atelier's value proposition is that contractors get a **defensible** spec — that breaks the moment we ship a 🔴 violation.
