# Slice 8 — Native Addon Commands + End-to-End Smoke Test

> **For agentic workers:** Use superpowers:executing-plans.

**Goal:** Move the audit + project-scaffold work from caller-driven (AI fetches scene_state, passes to audit) to addon-driven (AI says "audit zone X" and the addon does it directly). Plus an end-to-end smoke test that runs the full workflow against a sample project.

**Architecture:** The Blender addon already exposes a socket protocol with `_execute_command_internal(command_type, params)`. We add 4 new command handlers that invoke our existing pure-Python `_gates`, `_project`, `_snapshots` modules from inside the addon process, returning structured results to the MCP client without round-tripping scene state.

---

## File Structure

| File | Responsibility |
|---|---|
| `addon.py` | 4 new socket commands |
| `src/blender_mcp/server.py` | Refactor 4 existing MCP tools to optionally use native commands |
| `tests/test_e2e_workflow.py` | End-to-end smoke test (no Blender required — uses fixtures) |

---

## Task 1: Native `audit_interior_quality_native` Addon Command

Currently `audit_interior_quality(scene_info, ...)` requires the caller to first call `get_scene_info(full=True)` and pass the result. Native version eliminates the round-trip:

```python
def audit_interior_quality_native(self, params):
    """
    Run the 9-dimension audit directly inside Blender.

    Params:
        strictness: "exploration" | "hero" | "construction"
        project_root: optional path to project for handbook citation lookups
        scope: optional collection name (defaults to whole scene)

    Returns: same shape as MCP-side audit_interior_quality
             ({summary, gates: [...], status})
    """
    # 1. Walk bpy.data.objects to build scene_info dict
    # 2. Build lights_info from bpy.data.lights
    # 3. Build cameras_info from bpy.data.cameras
    # 4. Read render settings from bpy.context.scene
    # 5. Call _gates.run_audit(...) (pure-Python, copied/imported into addon)
    # 6. Return result
```

The complication: the addon runs in Blender's embedded Python, which doesn't have access to our `src/blender_mcp/` modules by default. Two options:

- **A.** Vendor the gate logic into addon.py (simple, duplicates code)
- **B.** Add `src/blender_mcp/` to addon's sys.path on register (cleaner, fragile)

**Decision:** Go with A — copy the gate-evaluation function into addon.py with a `# DUPLICATED FROM src/blender_mcp/_gates.py` header. The gate logic is small (~150 lines). Tests on the MCP side still cover the canonical version.

## Task 2: Native `create_interior_project_native` Command

Same pattern: scaffolds the project's Blender collections directly inside Blender, instead of MCP returning a list of names that the caller writes via `execute_blender_code`.

```python
def create_interior_project_native(self, params):
    """
    Params:
        project_name: str
        project_type: 'residential_apartment' | 'cafe_lounge' | etc.
        spaces: list[str]  # ['Living', 'Bedroom', 'Kitchen', ...]

    Behavior:
        1. Sets scene unit system to metric meters
        2. Creates the 11 standard collections
        3. Creates one sub-collection per space under 03_ZONES
        4. Sets scene custom properties for project metadata
        5. Returns created collection names + scene metadata
    """
```

## Task 3: Native `version_snapshot_native`

Saves the current `.blend` file via `bpy.ops.wm.save_as_mainfile` to the snapshots dir, copies sidecar JSONs, generates a thumbnail render via the active camera. Replaces the caller-driven snapshot pattern.

## Task 4: Native `place_furniture_from_style_native`

The compound version of Slice 6's `place_furniture_from_style`: a single addon command that runs Sketchfab search → download → import → place_on_ground inside one transaction, returning the placed object name.

## Task 5: End-to-End Smoke Test

`tests/test_e2e_workflow.py` exercises the full workflow without requiring a live Blender connection. Uses fixtures and the `mock_blender_connection` pattern already used in `tests/test_v22_features.py`.

```python
def test_full_workflow_smoke(tmp_path):
    """
    Simulates the full workflow:
    1. Create a discovery questionnaire session
    2. Submit canned answers to all 25 questions
    3. Verify taste-profile.json contains expected style_match
    4. Create a project from the recommended style
    5. Verify project structure (11 collections + per-space sub-collections)
    6. Lock a moodboard
    7. Record 3 SKUs
    8. Generate BoM
    9. Run audit in 'exploration' mode (mock scene state)
    10. Verify audit report has citations to handbook chapters
    11. Generate a snapshot
    12. Restore the snapshot
    """
```

Each step asserts the artifact exists / has the expected shape. No real Blender, no real image-gen.

## Task 6: Documentation update

- Update README.md with a "Quick start: Interior Design Workflow" section walking through the smoke-test sequence
- Update AGENTS.md with the addon-native vs MCP-side decision matrix
- Update INSTALL_AI.md with `register_addon_commands` step

## Task 7: Commit + push + tag

- Commit `feat: Slice 8 — native addon commands + E2E smoke test`
- Push to `develop`
- Tag `v2.4.0+fork.1`

## Acceptance

After Slice 8:
- AI can run audit / create_project / snapshot without first fetching scene state — single tool call.
- `pytest tests/test_e2e_workflow.py` passes: full workflow simulated end-to-end with fixtures.
- README documents the workflow visibly enough for a new user to start their first project in under 30 minutes.

## Out of scope

- Real Blender integration tests (would require headless Blender CI) — manual verification only
- Performance profiling — none of these are hot-path
