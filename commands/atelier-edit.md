---
description: Modify the current Blender scene using plain language. Routes "move that sofa to the window", "make it warmer", "swap the lamp for a brass one", etc. into MCP tool calls. Classifies edit cost (L1-L4 loops) and snapshots before expensive operations.
---

You are translating a plain-language edit request into MCP tool calls on the live Blender scene.

## Required state

The user has a Blender scene open (addon connected) and an Atelier project on disk with `taste-profile.json` containing the locked style.

## Process

1. **Parse intent** — what verb (move/swap/change/add/remove)? what target (object name, zone, or descriptor)? what attribute (position / material / color / size / count)?
2. **Load the relevant handbook chapter** based on intent:
   - Geometry / placement → `read_design_handbook(chapter="spatial")`
   - Material / color → `read_design_handbook(chapter="materials")`
   - Lighting → `read_design_handbook(chapter="lighting")`
   - Composition / styling → `read_design_handbook(chapter="styling")`
3. **Classify the edit cost** (per the workflow spec § Loop Architecture):
   - **L1** (within Stage 5 render-tweak): silent execute
   - **L2** (back to materials/lighting): silent execute
   - **L3** (back to layout / Stage 3-4): execute + auto-snapshot prior state + record version-log entry
   - **L4** (style change / back to Stage 2.5): **STOP** and prompt the user with branch / overwrite / cancel
4. **Route to MCP tools**:
   - "move X to Y" → `get_object_info(name=X)` → compute new transform → translate
   - "swap X for Y" → `delete_objects(name=X)` + asset search/place
   - "make it warmer" → identify lights → reduce Kelvin per `lighting.md` range
   - "more X" / "less X" → `scatter_on_surface` + count delta
   - "remove that" → `delete_objects(name=last_referenced_object)`
   - "add a Y" → search asset providers in priority order: Sketchfab → PolyHaven → AmbientCG → AI generation. Use `asset_query_help` first if unsure how to query. For style-aware furniture, use `place_furniture_from_style`.
5. **After every render-affecting edit**, run `audit_interior_quality_native(mode="exploration")`. Surface only HARD findings during iteration.

## Cite when explaining

If the user asks "why" you did something, cite the handbook chapter that drove the choice. Example:

> "I dropped the Kelvin from 4000K to 2700K because lighting.md §2 (citing GB 50034-2013 §5.1 Table) places residential evening lighting in the 2700-3000K band, and you said 'warmer'."
