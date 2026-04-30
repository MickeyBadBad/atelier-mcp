# Interior Design Workflow — Slice 3: Quality Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use `- [ ]` syntax.

**Goal:** Add the 9-dimension quality-gate validator on top of Slice 2's project state. Each gate is a pure-Python function returning citation-bearing findings; the new `audit_interior_quality` MCP tool wraps them and returns a single audit report consumable by the `interior-render-direction` skill.

**Architecture:** Pure-Python validators in `_gates.py` operate on scene-info dicts (the existing fork already provides `get_scene_info(full=True)` since Sprint 6). The AI fetches scene info first, then passes it plus the project root + strictness mode to `audit_interior_quality`. No Blender API calls inside gate functions — gates stay unit-testable.

**Tech Stack:** Python stdlib only. Builds on `_handbook.py` (for citation lookup), `_project.py` (for taste-profile reading).

---

## File Structure

| File | Responsibility |
|---|---|
| `src/blender_mcp/_gates.py` | 9 pure validator functions + StrictnessMode + Severity enums |
| `src/blender_mcp/server.py` | New `audit_interior_quality` MCP tool wrapping the validators |
| `tests/test_gates.py` | Unit tests for each gate (mock scene_info inputs) |

---

## Task 1: Failing Tests for `_gates.py`

**Files:** Create `tests/test_gates.py`

- [ ] Step 1: write the test file (see Task 3 for the test code).

## Task 2: Implement `_gates.py`

**Files:** Create `src/blender_mcp/_gates.py`

The module exposes:

- `Severity` (HARD / SOFT / INFO)
- `StrictnessMode` (EXPLORATION / HERO / CONSTRUCTION)
- `Finding` namedtuple (gate, severity, message, citation, suggested_fix)
- 9 gate functions (`check_materials`, `check_lighting_layers`, etc.)
- `run_audit(scene_info, mode, project=None)` — entrypoint

## Task 3: MCP Tool `audit_interior_quality`

**Files:** Modify `src/blender_mcp/server.py`

Wrap `_gates.run_audit`. Accepts scene_info dict + mode + optional project_root. Returns the audit report.

## Task 4: Tests + commit + push

Run full suite, expect 132 + new tests. Push to fork.
