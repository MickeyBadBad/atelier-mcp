# Interior Design MCP Product Design

## Purpose

Build a generic Interior Design layer for Blender MCP. The layer should let an AI assistant operate Blender with interior-design concepts instead of only low-level mesh, material, camera, and render operations.

This design is product- and workflow-focused. It must remain reusable across residential, retail, hospitality, office, and exhibition interiors. Private client projects may be used as manual validation examples, but no private project names, exact palettes, budgets, site facts, or client-specific zones belong in tool code, default configs, tests, docs examples, or committed fixtures.

## Non-Goals

- Do not build project-specific tools for any one venue, home, shop, or client.
- Do not depend on incomplete site scans for the primary workflow.
- Do not promise fully automatic architectural reconstruction from arbitrary photos or drawings in the first release.
- Do not replace CAD/BIM. The target is fast design blockout, material exploration, lighting studies, rendered views, and handoff assets inside Blender.

## Product Positioning

Interior Design MCP should answer this user need:

> "Given a sketch, measured plan, PDF drawing, or a simple room spec, help me create a measured 3D interior blockout in Blender, apply finishes and lighting, render useful views, audit the scene, and export a contractor/client package."

The product should optimize for:

- Speed from plan/reference to 3D blockout.
- Repeatable design workflow.
- Strict unit and scale handling.
- Material and finish schedules.
- Lighting plans that use interior-design terms.
- Render sets and export packages that match real handoff needs.

## Design Principles

1. Domain primitives first.
   Tools should expose room, zone, wall, floor, ceiling, opening, finish, fixture, lighting layer, view, and deliverable concepts.

2. Data-driven configuration.
   Palettes, zones, design constraints, finish schedules, and lighting targets come from caller-supplied JSON-like specs. Code only validates generic schemas and creates Blender objects from those specs.

3. Non-destructive scenes.
   References, imported drawings, generated shell geometry, finish variants, lights, cameras, and exports live in separate collections. Tools should not overwrite reference inputs unless explicitly told.

4. Measured before pretty.
   Wall height, wall thickness, floor scale, drawing calibration, and object dimensions are first-class. Renders are only useful if the scale is defensible.

5. Auditable output.
   The MCP should expose checks for units, scale, missing texture packing, over-heavy meshes, invalid material metadata, out-of-range light color temperatures, camera clipping, and orphaned objects.

6. Progressive automation.
   P0 supports calibrated drawing references plus explicit line/room specs. Later releases can add computer-vision detection, OCR, vector PDF extraction, and LLM-assisted cleanup.

## Workflow Overview

### P0 Workflow

1. Create an interior design project scaffold.
2. Import a PDF/image floor plan or measured drawing as a calibrated reference plane.
3. Add measured wall linework from a structured spec.
4. Extrude wall linework into walls, floor slabs, ceiling planes, and simple openings.
5. Define rooms/zones as named collections and metadata.
6. Apply finishes using generic finish specs.
7. Create an interior lighting plan.
8. Generate cameras and render view sets.
9. Audit the scene.
10. Export an interior package.

### P1 Workflow

1. Parse vector PDFs when wall vectors are available.
2. Run optional image detection to propose wall lines from raster plans.
3. Support variants for finish and lighting schemes.
4. Estimate surface areas and material quantities.
5. Generate a more complete handoff report.

## Tool Set

### `create_interior_project`

Initializes a scene for interior design.

Inputs:

- `project_name`: display name only; no special behavior.
- `root_collection`: default `Interior_Project`.
- `units`: default `metric`.
- `scale_unit`: default `meters`.
- `create_standard_collections`: default true.
- `output_dirs`: optional render/export/report folder hints.

Behavior:

- Set Blender units to metric meters.
- Create standard collections:
  - `00_REFERENCES`
  - `01_PLAN`
  - `02_SHELL`
  - `03_ZONES`
  - `04_FINISHES`
  - `05_FIXTURES`
  - `06_LIGHTING`
  - `07_CAMERAS`
  - `08_RENDER_OUTPUT`
  - `09_EXPORT`
  - `90_VARIANTS`
- Add scene custom properties for project metadata.
- Return created collections and unit settings.

### `import_plan_reference`

Imports a floor plan, measured drawing, or PDF page as a flat reference plane in Blender.

Inputs:

- `filepath`: absolute path to image or PDF.
- `page`: PDF page index, default 0.
- `name`: optional reference object name.
- `target_plane`: `XY` by default.
- `known_distance`: optional object with two drawing points and real-world distance.
- `real_world_width_m`: optional fallback scale.
- `opacity`: default 0.45.
- `lock_reference`: default true.

Behavior:

- For image inputs, load the image and create a plane with the image as material.
- For PDF inputs, render the requested page to a temporary image before creating the plane.
- If calibration is provided, scale the plane to real-world meters.
- Place the plane in `00_REFERENCES` and `01_PLAN`.
- Store calibration metadata on the object.

P0 implementation may support PDF conversion through a small optional helper dependency or a clear `BAD_INPUT` error when PDF support is unavailable. Image support is required.

### `calibrate_plan_reference`

Updates the scale of an existing plan reference from measured points.

Inputs:

- `reference_object`
- `point_a_px` or `point_a_uv`
- `point_b_px` or `point_b_uv`
- `real_distance_m`
- `axis_hint`: optional `x`, `y`, or `free`

Behavior:

- Compute scale from drawing distance to real-world distance.
- Resize the reference plane while preserving origin.
- Store calibration metadata.
- Return pixels-per-meter or drawing-units-per-meter equivalent.

### `create_floorplan_linework`

Creates editable wall-centerline geometry from a structured spec.

Inputs:

- `name`
- `coordinate_space`: `meters` or `plan_uv`.
- `walls`: list of wall segments with `id`, `start`, `end`, optional `thickness_m`, `height_m`, and `type`.
- `openings`: optional list with `id`, `wall_id`, `offset_m`, `width_m`, `height_m`, `sill_height_m`, and `kind`.
- `rooms`: optional list of room polygons with `id`, `name`, `points`, and `zone`.

Behavior:

- Validate wall segment shape and dimensions.
- Create line/curve objects or metadata-only records for later extrusion.
- Assign consistent names and custom properties.
- Return normalized linework with generated IDs for missing IDs.

### `extrude_floorplan_shell`

Turns linework into simple 3D walls, floors, ceilings, and openings.

Inputs:

- `linework_name`
- `default_wall_height_m`: default 2.8.
- `default_wall_thickness_m`: default 0.12.
- `create_floor`: default true.
- `floor_thickness_m`: default 0.04.
- `create_ceiling`: default false.
- `ceiling_height_m`: optional.
- `boolean_openings`: default true.
- `collection_name`: default `02_SHELL`.

Behavior:

- Build rectangular wall meshes from wall centerlines.
- Build floor polygons from room specs when present.
- Add door/window/opening cutouts when enough opening data is present.
- Add metadata linking generated meshes back to wall/room/opening IDs.
- Return created objects and skipped openings with reasons.

### `create_interior_zones`

Creates named room or design-zone collections and optional visual bounds.

Inputs:

- `zones`: list of `name`, `kind`, optional `bounds`, optional `room_ids`, optional metadata.
- `create_labels`: default true.
- `create_bounds`: default true.

Behavior:

- Create collections under `03_ZONES`.
- Add optional transparent bounding boxes or floor labels.
- Attach generic metadata.

### `apply_finish`

Applies a finish to an object or zone using a generic finish spec.

Inputs:

- `target`: object name, collection name, or zone name.
- `finish`: object with:
  - `name`
  - `category`: paint, wood, stone, tile, metal, fabric, glass, concrete, plaster, custom.
  - `color_hex`: optional.
  - `roughness`: optional.
  - `metallic`: optional.
  - `texture_asset_id`: optional.
  - `texture_library`: optional.
  - `uv_scale`: optional.
  - `manufacturer`: optional.
  - `sku`: optional.
  - `notes`: optional.
- `scope`: `objects`, `collection`, `zone`, or `selected`.

Behavior:

- Route simple color finishes to existing color material helpers.
- Route PBR finishes to existing texture helpers when asset IDs or generic categories are available.
- Store finish metadata on materials and target objects.
- Return material names, target count, and any skipped targets.

### `create_finish_schedule`

Exports material and finish metadata from the scene.

Inputs:

- `filepath`: JSON or CSV output path.
- `scope`: whole scene, collection, or zone.
- `include_area_estimates`: default true.

Behavior:

- Collect target object, zone, material, finish category, color, texture asset, manufacturer, SKU, and notes.
- Estimate mesh surface area when practical.
- Write JSON or CSV.
- Return totals by finish category and output path.

### `setup_interior_lighting_plan`

Creates a layered lighting plan for interior render studies.

Inputs:

- `zones`: optional list of target zones.
- `layers`: list of ambient, accent, task, decorative, daylight.
- Each layer supports `kelvin`, `target_lux`, `fixture_type`, `count`, `mount_height_m`, `spacing_m`, `target_objects`, and `target_points`.
- `remove_existing`: default false.
- `collection_name`: default `06_LIGHTING`.

Behavior:

- Create lights by layer and zone.
- Store layer metadata on lights.
- Use Kelvin values directly.
- Return created lights and estimated lux intent.

### `audit_interior_scene`

Runs quality checks before render or export.

Inputs:

- `checks`: optional list. Default all.
- `strict`: default false.
- `scope`: scene or collection.

Checks:

- Units are metric.
- Wall and room dimensions are plausible.
- Drawing reference is calibrated when plan-derived shell exists.
- Objects are in expected collections.
- Materials have finish metadata when used in a finish schedule.
- Image textures are loaded and packed or export-safe.
- Lights have Kelvin metadata and are within caller-supplied range if provided.
- Cameras are not inside wall meshes and have valid clipping.
- Mesh count and polygon count are within warning thresholds.
- Export paths are under an expected output folder when provided.

Return:

- `status`: pass, warn, or fail.
- `findings`: list with severity, code, object, hint, and detail.

### `create_interior_camera_set`

Creates cameras for common interior-design views.

Inputs:

- `views`: list of `wide`, `corner`, `elevation`, `plan`, `detail`, `hero`, or custom.
- `targets`: objects, zones, or explicit coordinates.
- `lens_mm`: optional.
- `height_m`: optional.
- `orthographic`: optional.
- `avoid_walls`: default true.

Behavior:

- Position cameras from zone or shell bounds.
- Prefer useful interior viewpoints rather than world-origin views.
- Add orthographic plan/elevation cameras when requested.
- Return camera names and view metadata.

### `render_view_set`

Renders a named set of cameras.

Inputs:

- `views`: camera names or view preset names.
- `output_dir`
- `resolution`
- `engine`: Cycles or EEVEE.
- `samples`
- `view_transform`: default should prefer AgX when available, with Filmic fallback.
- `return_previews`: default true.

Behavior:

- Render each view to a stable filename.
- Return file paths and optional preview thumbnails.
- Preserve prior render settings where practical.

### `export_interior_package`

Exports scene geometry and handoff artifacts.

Inputs:

- `output_dir`
- `package_name`
- `formats`: default GLB.
- `include_renders`: default true.
- `include_finish_schedule`: default true.
- `include_audit_report`: default true.
- `pack_textures`: default true.

Behavior:

- Run scene audit first.
- Export geometry with existing quick export behavior.
- Write finish schedule and audit report when requested.
- Return output paths and warnings.

## Floor Plan / Drawing to 3D Strategy

### P0: Calibrated Reference + Explicit Linework

P0 should not attempt full automatic recognition. The robust first version is:

1. Import image/PDF page as a reference plane.
2. Calibrate scale using known distance.
3. Accept wall/room/opening linework as JSON-like input.
4. Extrude shell geometry.

This is immediately useful for measured drawings and AI-assisted manual tracing. It also avoids over-promising on messy scans, low-resolution PDFs, handwritten plans, and perspective photos.

### P1: Vector PDF Extraction

When PDF pages contain vector linework, add a parser that extracts paths, normalizes them, and proposes wall segments. The output must still be reviewed through `create_floorplan_linework`; automatic extraction should create candidates, not silently produce final walls.

### P2: Raster Detection

Optional computer vision can detect dark wall lines from images. This requires dependency and environment decisions. The result should be a proposal with confidence scores and a cleanup path, not a guaranteed model.

## Schema Boundaries

Project-specific values are caller data. Tool code may validate and apply this generic shape:

```json
{
  "project_type": "hospitality | residential | retail | office | exhibition | other",
  "units": "metric",
  "zones": [
    {"name": "public_seating", "kind": "seating"},
    {"name": "service_counter", "kind": "service"}
  ],
  "palette": [
    {"name": "primary_wall", "hex": "#123456", "role": "paint"},
    {"name": "accent_metal", "hex": "#abcdef", "role": "metal"}
  ],
  "lighting_targets": {
    "kelvin": [2200, 3000],
    "ambient_lux": [50, 100],
    "accent_lux": [150, 300]
  }
}
```

The code must not ship defaults that correspond to any private project. Generic examples are allowed if they are neutral and reusable.

## Error Handling

All new MCP tools must return the canonical envelope already used by the fork:

- `{"ok": true, "data": ...}`
- `{"ok": false, "error": {"code": "...", "hint": "...", "detail": "..."}}`

Expected error types:

- `BAD_INPUT`: invalid schema, missing path, invalid dimensions, unsupported file type.
- `STATE_REQUIRED`: project scaffold not created, reference not calibrated, no active camera.
- `NOT_FOUND`: missing object, collection, material, linework, camera, or filepath.
- `NETWORK`: only for external downloads or provider calls.
- `INTERNAL`: unexpected Blender or parser failure.

Errors should teach the next action. Example:

```json
{
  "ok": false,
  "error": {
    "code": "STATE_REQUIRED",
    "hint": "Calibrate the plan reference before extruding measured walls.",
    "detail": "Reference object 'Plan_A' has no calibration metadata."
  }
}
```

## Testing Strategy

Unit tests should cover pure helpers without Blender:

- Schema validation for project specs, finish specs, linework specs, lighting specs.
- Unit conversion and calibration math.
- Wall segment normalization.
- Surface area helpers.
- Audit finding aggregation.
- Phase taxonomy additions.
- Server wrapper command forwarding.

Addon-side tests can use existing Blender stubs:

- Ensure handlers are registered in `_execute_command_internal`.
- Validate simple fake-object behavior where possible.
- Avoid tests that require real Blender rendering unless run manually.

Manual validation should use neutral sample projects:

- Small residential room.
- Small retail shop.
- Small hospitality lounge.

These sample names should remain generic and should not embed private client details.

## Release Slices

### Slice 1: Project + Plan Reference Foundation

Deliver:

- `create_interior_project`
- `import_plan_reference` for images
- `calibrate_plan_reference`
- tool phase taxonomy updates
- tests for schemas and server forwarding

### Slice 2: Plan Linework to Shell

Deliver:

- `create_floorplan_linework`
- `extrude_floorplan_shell`
- simple door/window opening support
- tests for wall mesh math and validation

### Slice 3: Finishes + Schedules

Deliver:

- `apply_finish`
- `create_finish_schedule`
- finish metadata support
- tests for metadata extraction and CSV/JSON output decisions

### Slice 4: Lighting + Cameras + Render Sets

Deliver:

- `setup_interior_lighting_plan`
- `create_interior_camera_set`
- `render_view_set`
- AgX-with-Filmic-fallback color management
- tests for wrapper forwarding and auditable settings

### Slice 5: Audit + Package Export

Deliver:

- `audit_interior_scene`
- `export_interior_package`
- warnings for missing calibration, missing finish metadata, missing packed textures, invalid units, and camera clipping
- tests for finding severity and package manifest output

### Slice 6: Optional PDF Support

Deliver:

- PDF page to image conversion path if a dependency is available.
- Clear `BAD_INPUT` fallback if PDF support is unavailable.
- tests for extension routing and error messages.

## Acceptance Criteria

The feature is acceptable when a generic user can:

1. Start with a blank Blender scene.
2. Create an interior project scaffold.
3. Import a PNG/JPG floor plan as a calibrated reference.
4. Provide a small wall/room/opening linework spec.
5. Generate a scaled 3D shell.
6. Apply at least three finish categories.
7. Generate a finish schedule.
8. Add a layered lighting plan.
9. Generate at least three cameras.
10. Render a view set.
11. Run an audit and see actionable findings.
12. Export a GLB package with textures packed.

No committed code, docs examples, tests, or fixtures should contain private project identifiers or private project-specific palettes, budgets, site facts, or zone names.
