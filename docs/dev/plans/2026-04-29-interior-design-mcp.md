# Interior Design MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a generic Interior Design layer for Blender MCP, including image/PDF plan reference import, calibrated floor-plan-to-3D blockout, finishes, lighting, cameras, audits, render sets, and export packages.

**Architecture:** Add a pure Python helper module for schemas, validation, calibration, linework normalization, audit findings, and package manifests. Add MCP server wrappers that forward commands through the existing socket bridge and addon-side Blender methods that create scene objects. Keep all project-specific values caller-supplied; no private client data appears in code, tests, fixtures, or docs examples.

**Tech Stack:** Python 3.10+, Blender Python API, FastMCP, existing `tool_envelope`, existing socket command pattern, pytest, Pillow for image handling. PDF support is optional in the first pass and must fail with a clear `BAD_INPUT` error if no PDF conversion backend is available.

---

## File Structure

- Create: `src/blender_mcp/interior_design.py`
  - Pure helpers: generic schema validation, unit/calibration math, wall linework normalization, finish schedule rows, audit finding objects, render/export manifest helpers.
- Create: `tests/test_interior_design.py`
  - Unit tests for pure helpers without Blender.
- Create: `tests/test_interior_mcp_tools.py`
  - MCP wrapper forwarding tests using `mock_blender_connection`.
- Modify: `src/blender_mcp/server.py`
  - Add new MCP tools that forward interior-design commands to the addon and return canonical envelopes.
- Modify: `src/blender_mcp/_phases.py`
  - Add interior workflow phase tags.
- Modify: `addon.py`
  - Register command handlers and implement Blender-side project, plan reference, linework, shell, finish, lighting, camera, render, audit, and package methods.
- Modify: `tests/test_phases.py`
  - Add phase taxonomy assertions for the new tools.
- Modify: `tests/test_naming.py`
  - Keep legacy-name checks passing if new names are added.
- Optional later modification: `pyproject.toml`
  - Only add a PDF conversion dependency after deciding it is stable across Blender Python and normal Python test environments.

## Task 1: Add Pure Interior Design Helper Module

**Files:**
- Create: `src/blender_mcp/interior_design.py`
- Test: `tests/test_interior_design.py`

- [ ] **Step 1: Write failing tests for project collections, calibration, linework, and audit findings**

Create `tests/test_interior_design.py`:

```python
import math
import pytest

from blender_mcp.interior_design import (
    STANDARD_INTERIOR_COLLECTIONS,
    InteriorValidationError,
    calibration_scale_from_points,
    normalize_project_spec,
    normalize_wall_linework,
    validate_finish_spec,
    audit_finding,
    package_manifest,
)


def test_standard_collections_are_generic():
    assert "00_REFERENCES" in STANDARD_INTERIOR_COLLECTIONS
    assert "02_SHELL" in STANDARD_INTERIOR_COLLECTIONS
    joined = " ".join(STANDARD_INTERIOR_COLLECTIONS).lower()
    assert "clientcodename" not in joined
    assert "privatepalette" not in joined
    assert "privatelocation" not in joined


def test_normalize_project_spec_defaults_to_metric():
    spec = normalize_project_spec({"project_name": "Small Retail Study"})
    assert spec["project_name"] == "Small Retail Study"
    assert spec["units"] == "metric"
    assert spec["scale_unit"] == "meters"
    assert spec["collections"] == STANDARD_INTERIOR_COLLECTIONS


def test_calibration_scale_from_points():
    scale = calibration_scale_from_points([0, 0], [200, 0], 4.0)
    assert math.isclose(scale["pixels_per_meter"], 50.0)
    assert math.isclose(scale["meters_per_pixel"], 0.02)


def test_calibration_rejects_zero_length_points():
    with pytest.raises(InteriorValidationError) as exc:
        calibration_scale_from_points([10, 10], [10, 10], 1.0)
    assert "Calibration points must be different" in str(exc.value)


def test_normalize_wall_linework_adds_defaults():
    out = normalize_wall_linework({
        "name": "Ground Floor",
        "coordinate_space": "meters",
        "walls": [
            {"start": [0, 0], "end": [4, 0]},
            {"id": "w2", "start": [4, 0], "end": [4, 3], "height_m": 3.2},
        ],
        "rooms": [
            {"name": "sales", "points": [[0, 0], [4, 0], [4, 3], [0, 3]]}
        ],
    })
    assert out["walls"][0]["id"] == "wall_001"
    assert out["walls"][0]["thickness_m"] == 0.12
    assert out["walls"][0]["height_m"] == 2.8
    assert out["walls"][1]["id"] == "w2"
    assert out["rooms"][0]["id"] == "room_001"


def test_normalize_wall_linework_rejects_bad_wall():
    with pytest.raises(InteriorValidationError) as exc:
        normalize_wall_linework({
            "name": "Bad",
            "walls": [{"start": [0, 0], "end": [0, 0]}],
        })
    assert "Wall wall_001 start and end must differ" in str(exc.value)


def test_validate_finish_spec_accepts_generic_finish():
    finish = validate_finish_spec({
        "name": "dark paint",
        "category": "paint",
        "color_hex": "#123456",
        "roughness": 0.82,
        "manufacturer": "Generic",
        "sku": "PAINT-001",
    })
    assert finish["category"] == "paint"
    assert finish["color_hex"] == "#123456"


def test_validate_finish_spec_rejects_bad_hex():
    with pytest.raises(InteriorValidationError) as exc:
        validate_finish_spec({
            "name": "bad paint",
            "category": "paint",
            "color_hex": "123456",
        })
    assert "color_hex must be #RRGGBB" in str(exc.value)


def test_audit_finding_shape():
    finding = audit_finding(
        severity="warn",
        code="UNCALIBRATED_PLAN",
        hint="Calibrate the plan before extrusion.",
        detail="Plan_A has no pixels_per_meter metadata.",
        obj="Plan_A",
    )
    assert finding == {
        "severity": "warn",
        "code": "UNCALIBRATED_PLAN",
        "hint": "Calibrate the plan before extrusion.",
        "detail": "Plan_A has no pixels_per_meter metadata.",
        "object": "Plan_A",
    }


def test_package_manifest_is_generic():
    manifest = package_manifest(
        package_name="retail_study_v1",
        geometry_exports=["/tmp/retail_study_v1.glb"],
        renders=["/tmp/hero.png"],
        reports=["/tmp/audit.json"],
        warnings=["One material lacks SKU metadata."],
    )
    assert manifest["package_name"] == "retail_study_v1"
    assert manifest["geometry_exports"] == ["/tmp/retail_study_v1.glb"]
    assert "private" not in str(manifest).lower()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
uv run pytest tests/test_interior_design.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'blender_mcp.interior_design'
```

- [ ] **Step 3: Implement the helper module**

Create `src/blender_mcp/interior_design.py`:

```python
"""Generic interior-design helpers for Blender MCP.

This module must stay project-neutral. It validates and normalizes generic
interior-design data, but it must not contain private client names, palettes,
budgets, site facts, or project-specific zone names.
"""
from __future__ import annotations

from copy import deepcopy
import math
import re
from typing import Any


STANDARD_INTERIOR_COLLECTIONS = [
    "00_REFERENCES",
    "01_PLAN",
    "02_SHELL",
    "03_ZONES",
    "04_FINISHES",
    "05_FIXTURES",
    "06_LIGHTING",
    "07_CAMERAS",
    "08_RENDER_OUTPUT",
    "09_EXPORT",
    "90_VARIANTS",
]

FINISH_CATEGORIES = {
    "paint",
    "wood",
    "stone",
    "tile",
    "metal",
    "fabric",
    "glass",
    "concrete",
    "plaster",
    "custom",
}

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class InteriorValidationError(ValueError):
    """Raised when an interior-design spec is invalid."""


def _ensure_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InteriorValidationError(f"{field} must be a number")
    return float(value)


def _ensure_point2(value: Any, field: str) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise InteriorValidationError(f"{field} must be [x, y]")
    return [_ensure_number(value[0], f"{field}[0]"), _ensure_number(value[1], f"{field}[1]")]


def _distance2(a: list[float], b: list[float]) -> float:
    return math.hypot(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))


def normalize_project_spec(spec: dict[str, Any] | None) -> dict[str, Any]:
    spec = deepcopy(spec or {})
    project_name = str(spec.get("project_name") or "Interior Design Project")
    units = str(spec.get("units") or "metric")
    scale_unit = str(spec.get("scale_unit") or "meters")
    if units != "metric":
        raise InteriorValidationError("units must be 'metric'")
    if scale_unit != "meters":
        raise InteriorValidationError("scale_unit must be 'meters'")
    collections = list(spec.get("collections") or STANDARD_INTERIOR_COLLECTIONS)
    if not collections:
        raise InteriorValidationError("collections must not be empty")
    return {
        "project_name": project_name,
        "units": units,
        "scale_unit": scale_unit,
        "collections": collections,
        "metadata": dict(spec.get("metadata") or {}),
    }


def calibration_scale_from_points(
    point_a: list[float],
    point_b: list[float],
    real_distance_m: float,
) -> dict[str, float]:
    a = _ensure_point2(point_a, "point_a")
    b = _ensure_point2(point_b, "point_b")
    real = _ensure_number(real_distance_m, "real_distance_m")
    if real <= 0:
        raise InteriorValidationError("real_distance_m must be > 0")
    pixel_dist = _distance2(a, b)
    if pixel_dist <= 0:
        raise InteriorValidationError("Calibration points must be different")
    pixels_per_meter = pixel_dist / real
    return {
        "drawing_distance": pixel_dist,
        "real_distance_m": real,
        "pixels_per_meter": pixels_per_meter,
        "meters_per_pixel": 1.0 / pixels_per_meter,
    }


def normalize_wall_linework(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise InteriorValidationError("linework spec must be an object")
    name = str(spec.get("name") or "Floorplan Linework")
    coordinate_space = str(spec.get("coordinate_space") or "meters")
    if coordinate_space not in {"meters", "plan_uv"}:
        raise InteriorValidationError("coordinate_space must be 'meters' or 'plan_uv'")
    raw_walls = spec.get("walls")
    if not isinstance(raw_walls, list) or not raw_walls:
        raise InteriorValidationError("walls must be a non-empty list")

    walls = []
    for idx, wall in enumerate(raw_walls, start=1):
        if not isinstance(wall, dict):
            raise InteriorValidationError(f"wall_{idx:03d} must be an object")
        wall_id = str(wall.get("id") or f"wall_{idx:03d}")
        start = _ensure_point2(wall.get("start"), f"{wall_id}.start")
        end = _ensure_point2(wall.get("end"), f"{wall_id}.end")
        if _distance2(start, end) <= 0:
            raise InteriorValidationError(f"Wall {wall_id} start and end must differ")
        thickness = _ensure_number(wall.get("thickness_m", 0.12), f"{wall_id}.thickness_m")
        height = _ensure_number(wall.get("height_m", 2.8), f"{wall_id}.height_m")
        if thickness <= 0:
            raise InteriorValidationError(f"{wall_id}.thickness_m must be > 0")
        if height <= 0:
            raise InteriorValidationError(f"{wall_id}.height_m must be > 0")
        walls.append({
            "id": wall_id,
            "start": start,
            "end": end,
            "thickness_m": thickness,
            "height_m": height,
            "type": str(wall.get("type") or "partition"),
        })

    openings = []
    for idx, opening in enumerate(spec.get("openings") or [], start=1):
        if not isinstance(opening, dict):
            raise InteriorValidationError(f"opening_{idx:03d} must be an object")
        opening_id = str(opening.get("id") or f"opening_{idx:03d}")
        wall_id = opening.get("wall_id")
        if not wall_id:
            raise InteriorValidationError(f"{opening_id}.wall_id is required")
        openings.append({
            "id": opening_id,
            "wall_id": str(wall_id),
            "offset_m": _ensure_number(opening.get("offset_m", 0), f"{opening_id}.offset_m"),
            "width_m": _ensure_number(opening.get("width_m", 0.8), f"{opening_id}.width_m"),
            "height_m": _ensure_number(opening.get("height_m", 2.1), f"{opening_id}.height_m"),
            "sill_height_m": _ensure_number(opening.get("sill_height_m", 0), f"{opening_id}.sill_height_m"),
            "kind": str(opening.get("kind") or "opening"),
        })

    rooms = []
    for idx, room in enumerate(spec.get("rooms") or [], start=1):
        if not isinstance(room, dict):
            raise InteriorValidationError(f"room_{idx:03d} must be an object")
        room_id = str(room.get("id") or f"room_{idx:03d}")
        points = [_ensure_point2(p, f"{room_id}.points[]") for p in room.get("points") or []]
        if len(points) < 3:
            raise InteriorValidationError(f"{room_id}.points must include at least 3 points")
        rooms.append({
            "id": room_id,
            "name": str(room.get("name") or room_id),
            "points": points,
            "zone": str(room.get("zone") or room.get("name") or room_id),
        })

    return {
        "name": name,
        "coordinate_space": coordinate_space,
        "walls": walls,
        "openings": openings,
        "rooms": rooms,
    }


def validate_finish_spec(finish: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(finish, dict):
        raise InteriorValidationError("finish must be an object")
    name = str(finish.get("name") or "").strip()
    if not name:
        raise InteriorValidationError("finish.name is required")
    category = str(finish.get("category") or "custom")
    if category not in FINISH_CATEGORIES:
        raise InteriorValidationError(f"finish.category must be one of {sorted(FINISH_CATEGORIES)}")
    color_hex = finish.get("color_hex")
    if color_hex is not None:
        color_hex = str(color_hex)
        if not HEX_RE.match(color_hex):
            raise InteriorValidationError("color_hex must be #RRGGBB")
    out = deepcopy(finish)
    out["name"] = name
    out["category"] = category
    if color_hex is not None:
        out["color_hex"] = color_hex
    return out


def audit_finding(
    *,
    severity: str,
    code: str,
    hint: str,
    detail: str,
    obj: str | None = None,
) -> dict[str, str]:
    if severity not in {"info", "warn", "fail"}:
        raise InteriorValidationError("severity must be info, warn, or fail")
    finding = {
        "severity": severity,
        "code": str(code),
        "hint": str(hint),
        "detail": str(detail),
    }
    if obj is not None:
        finding["object"] = str(obj)
    return finding


def package_manifest(
    *,
    package_name: str,
    geometry_exports: list[str],
    renders: list[str],
    reports: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "package_name": str(package_name),
        "geometry_exports": list(geometry_exports),
        "renders": list(renders),
        "reports": list(reports),
        "warnings": list(warnings),
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
uv run pytest tests/test_interior_design.py -v
```

Expected:

```text
10 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/blender_mcp/interior_design.py tests/test_interior_design.py
git commit -m "feat: add generic interior design helpers"
```

## Task 2: Add MCP Tool Wrappers and Phase Taxonomy

**Files:**
- Modify: `src/blender_mcp/server.py`
- Modify: `src/blender_mcp/_phases.py`
- Modify: `tests/test_phases.py`
- Create: `tests/test_interior_mcp_tools.py`

- [ ] **Step 1: Write failing wrapper tests**

Create `tests/test_interior_mcp_tools.py`:

```python
import json

from blender_mcp import server


def _parsed(tool_result):
    return json.loads(tool_result)


def test_create_interior_project_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"collections": ["00_REFERENCES"]}
    out = _parsed(server.create_interior_project(None, project_name="Small Retail Study"))
    assert out["ok"] is True
    mock_blender_connection.send_command.assert_called_once()
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "create_interior_project"
    assert params["project_name"] == "Small Retail Study"


def test_import_plan_reference_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"object_name": "Plan_Reference"}
    out = _parsed(server.import_plan_reference(
        None,
        filepath="/tmp/plan.png",
        known_distance={"point_a": [0, 0], "point_b": [100, 0], "real_distance_m": 2.0},
    ))
    assert out["ok"] is True
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "import_plan_reference"
    assert params["filepath"] == "/tmp/plan.png"
    assert params["known_distance"]["real_distance_m"] == 2.0


def test_create_floorplan_linework_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"linework_name": "Ground Floor"}
    spec = {"name": "Ground Floor", "walls": [{"start": [0, 0], "end": [4, 0]}]}
    out = _parsed(server.create_floorplan_linework(None, linework=spec))
    assert out["ok"] is True
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "create_floorplan_linework"
    assert params["linework"] == spec


def test_extrude_floorplan_shell_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"created_objects": ["Wall_wall_001"]}
    out = _parsed(server.extrude_floorplan_shell(None, linework_name="Ground Floor"))
    assert out["ok"] is True
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "extrude_floorplan_shell"
    assert params["linework_name"] == "Ground Floor"


def test_apply_finish_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"material": "Paint_dark"}
    out = _parsed(server.apply_finish(
        None,
        target="Wall_wall_001",
        finish={"name": "dark paint", "category": "paint", "color_hex": "#123456"},
    ))
    assert out["ok"] is True
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "apply_finish"
    assert params["target"] == "Wall_wall_001"


def test_audit_interior_scene_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"status": "pass", "findings": []}
    out = _parsed(server.audit_interior_scene(None))
    assert out["ok"] is True
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "audit_interior_scene"
    assert params["checks"] is None
```

- [ ] **Step 2: Extend phase tests**

Modify `tests/test_phases.py` expected phase set and known tool assertions:

```python
def test_phase_keys_match_curated_list():
    expected = {
        "discovery", "diagnostics", "asset_search",
        "asset_download", "asset_generation",
        "interior_project", "interior_plan", "interior_finish",
        "interior_audit", "material", "geometry", "camera", "lighting",
        "render", "export", "scene_management", "config",
    }
    assert set(PHASES.keys()) == expected
```

Add assertions inside `test_phase_for_known_tools`:

```python
    assert phase_for_tool("create_interior_project") == "interior_project"
    assert phase_for_tool("import_plan_reference") == "interior_plan"
    assert phase_for_tool("create_floorplan_linework") == "interior_plan"
    assert phase_for_tool("extrude_floorplan_shell") == "interior_plan"
    assert phase_for_tool("apply_finish") == "interior_finish"
    assert phase_for_tool("audit_interior_scene") == "interior_audit"
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
uv run pytest tests/test_interior_mcp_tools.py tests/test_phases.py -v
```

Expected:

```text
AttributeError: module 'blender_mcp.server' has no attribute 'create_interior_project'
```

- [ ] **Step 4: Add phase taxonomy**

Modify `src/blender_mcp/_phases.py` by adding these keys after `asset_generation`:

```python
    "interior_project": [
        "create_interior_project",
        "create_interior_zones",
    ],
    "interior_plan": [
        "import_plan_reference",
        "calibrate_plan_reference",
        "create_floorplan_linework",
        "extrude_floorplan_shell",
    ],
    "interior_finish": [
        "apply_finish",
        "create_finish_schedule",
    ],
    "interior_audit": [
        "audit_interior_scene",
        "export_interior_package",
    ],
```

- [ ] **Step 5: Add MCP wrappers in `server.py`**

Add these functions near the existing design-workflow wrappers, before `execute_blender_code`:

```python
@mcp.tool()
@tool_envelope
def create_interior_project(
    ctx: Context,
    project_name: str = "Interior Design Project",
    root_collection: str = "Interior_Project",
    units: str = "metric",
    scale_unit: str = "meters",
    create_standard_collections: bool = True,
    output_dirs: Dict[str, str] = None,
) -> str:
    """Initialize a generic interior-design Blender scene.

    Creates metric units, standard collections, and project metadata. This
    tool is project-neutral: all palettes, zones, budgets, and client facts
    must be supplied by callers through later generic specs.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("create_interior_project", {
        "project_name": project_name,
        "root_collection": root_collection,
        "units": units,
        "scale_unit": scale_unit,
        "create_standard_collections": create_standard_collections,
        "output_dirs": output_dirs,
    }))
    return result


@mcp.tool()
@tool_envelope
def import_plan_reference(
    ctx: Context,
    filepath: str,
    page: int = 0,
    name: str = None,
    target_plane: str = "XY",
    known_distance: Dict[str, Any] = None,
    real_world_width_m: float = None,
    opacity: float = 0.45,
    lock_reference: bool = True,
) -> str:
    """Import an image or PDF plan as a calibrated reference plane.

    Use this when the source is a floor plan, measured drawing, or scanned
    sketch. P0 image import is required; PDF conversion may return BAD_INPUT
    when the runtime has no PDF backend.
    """
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("import_plan_reference", {
        "filepath": filepath,
        "page": page,
        "name": name,
        "target_plane": target_plane,
        "known_distance": known_distance,
        "real_world_width_m": real_world_width_m,
        "opacity": opacity,
        "lock_reference": lock_reference,
    }))
    return result


@mcp.tool()
@tool_envelope
def calibrate_plan_reference(
    ctx: Context,
    reference_object: str,
    point_a: List[float],
    point_b: List[float],
    real_distance_m: float,
    axis_hint: str = "free",
) -> str:
    """Calibrate an existing plan reference from two measured drawing points."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("calibrate_plan_reference", {
        "reference_object": reference_object,
        "point_a": point_a,
        "point_b": point_b,
        "real_distance_m": real_distance_m,
        "axis_hint": axis_hint,
    }))
    return result


@mcp.tool()
@tool_envelope
def create_floorplan_linework(ctx: Context, linework: Dict[str, Any]) -> str:
    """Create normalized wall/room/opening linework from a generic spec."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("create_floorplan_linework", {
        "linework": linework,
    }))
    return result


@mcp.tool()
@tool_envelope
def extrude_floorplan_shell(
    ctx: Context,
    linework_name: str,
    default_wall_height_m: float = 2.8,
    default_wall_thickness_m: float = 0.12,
    create_floor: bool = True,
    floor_thickness_m: float = 0.04,
    create_ceiling: bool = False,
    ceiling_height_m: float = None,
    boolean_openings: bool = True,
    collection_name: str = "02_SHELL",
) -> str:
    """Extrude measured 2D linework into simple 3D interior shell geometry."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("extrude_floorplan_shell", {
        "linework_name": linework_name,
        "default_wall_height_m": default_wall_height_m,
        "default_wall_thickness_m": default_wall_thickness_m,
        "create_floor": create_floor,
        "floor_thickness_m": floor_thickness_m,
        "create_ceiling": create_ceiling,
        "ceiling_height_m": ceiling_height_m,
        "boolean_openings": boolean_openings,
        "collection_name": collection_name,
    }))
    return result


@mcp.tool()
@tool_envelope
def create_interior_zones(
    ctx: Context,
    zones: List[Dict[str, Any]],
    create_labels: bool = True,
    create_bounds: bool = True,
) -> str:
    """Create generic interior zones as collections and optional bounds."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("create_interior_zones", {
        "zones": zones,
        "create_labels": create_labels,
        "create_bounds": create_bounds,
    }))
    return result


@mcp.tool()
@tool_envelope
def apply_finish(
    ctx: Context,
    target: str,
    finish: Dict[str, Any],
    scope: str = "object",
) -> str:
    """Apply a generic interior finish and attach schedule metadata."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("apply_finish", {
        "target": target,
        "finish": finish,
        "scope": scope,
    }))
    return result


@mcp.tool()
@tool_envelope
def create_finish_schedule(
    ctx: Context,
    filepath: str,
    scope: str = "scene",
    include_area_estimates: bool = True,
) -> str:
    """Export finish metadata from the scene to JSON or CSV."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("create_finish_schedule", {
        "filepath": filepath,
        "scope": scope,
        "include_area_estimates": include_area_estimates,
    }))
    return result


@mcp.tool()
@tool_envelope
def setup_interior_lighting_plan(
    ctx: Context,
    zones: List[str] = None,
    layers: List[Dict[str, Any]] = None,
    remove_existing: bool = False,
    collection_name: str = "06_LIGHTING",
) -> str:
    """Create layered interior lighting by ambient/accent/task/decorative intent."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("setup_interior_lighting_plan", {
        "zones": zones,
        "layers": layers,
        "remove_existing": remove_existing,
        "collection_name": collection_name,
    }))
    return result


@mcp.tool()
@tool_envelope
def create_interior_camera_set(
    ctx: Context,
    views: List[Dict[str, Any]],
    targets: List[str] = None,
    avoid_walls: bool = True,
) -> str:
    """Create cameras for common interior views such as wide, corner, plan, and detail."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("create_interior_camera_set", {
        "views": views,
        "targets": targets,
        "avoid_walls": avoid_walls,
    }))
    return result


@mcp.tool()
@tool_envelope
def render_view_set(
    ctx: Context,
    views: List[str],
    output_dir: str,
    resolution: List[int] = None,
    engine: str = "CYCLES",
    samples: int = 64,
    view_transform: str = "AgX",
    return_previews: bool = True,
) -> str:
    """Batch render a set of named cameras to stable interior-design filenames."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("render_view_set", {
        "views": views,
        "output_dir": output_dir,
        "resolution": resolution,
        "engine": engine,
        "samples": samples,
        "view_transform": view_transform,
        "return_previews": return_previews,
    }))
    return result


@mcp.tool()
@tool_envelope
def audit_interior_scene(
    ctx: Context,
    checks: List[str] = None,
    strict: bool = False,
    scope: str = "scene",
) -> str:
    """Audit generic interior-design scene quality before render or export."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("audit_interior_scene", {
        "checks": checks,
        "strict": strict,
        "scope": scope,
    }))
    return result


@mcp.tool()
@tool_envelope
def export_interior_package(
    ctx: Context,
    output_dir: str,
    package_name: str,
    formats: List[str] = None,
    include_renders: bool = True,
    include_finish_schedule: bool = True,
    include_audit_report: bool = True,
    pack_textures: bool = True,
) -> str:
    """Export geometry plus optional renders, finish schedule, and audit report."""
    blender = get_blender_connection()
    result = _check_addon_result(blender.send_command("export_interior_package", {
        "output_dir": output_dir,
        "package_name": package_name,
        "formats": formats,
        "include_renders": include_renders,
        "include_finish_schedule": include_finish_schedule,
        "include_audit_report": include_audit_report,
        "pack_textures": pack_textures,
    }))
    return result
```

- [ ] **Step 6: Run tests to verify pass**

Run:

```bash
uv run pytest tests/test_interior_mcp_tools.py tests/test_phases.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 7: Commit**

```bash
git add src/blender_mcp/server.py src/blender_mcp/_phases.py tests/test_phases.py tests/test_interior_mcp_tools.py
git commit -m "feat: expose generic interior design mcp tools"
```

## Task 3: Add Addon Command Registration and Project Scaffold

**Files:**
- Modify: `addon.py`
- Test: `tests/test_interior_design.py`

- [ ] **Step 1: Write a lightweight handler-registration test**

Append to `tests/test_interior_design.py`:

```python
def test_interior_tool_names_are_project_neutral():
    tool_names = [
        "create_interior_project",
        "import_plan_reference",
        "calibrate_plan_reference",
        "create_floorplan_linework",
        "extrude_floorplan_shell",
        "create_interior_zones",
        "apply_finish",
        "create_finish_schedule",
        "setup_interior_lighting_plan",
        "create_interior_camera_set",
        "render_view_set",
        "audit_interior_scene",
        "export_interior_package",
    ]
    joined = " ".join(tool_names).lower()
    assert "clientcodename" not in joined
    assert "privatepalette" not in joined
    assert "privatelocation" not in joined
```

- [ ] **Step 2: Run test to verify helper tests still pass**

Run:

```bash
uv run pytest tests/test_interior_design.py -v
```

Expected:

```text
11 passed
```

- [ ] **Step 3: Register addon handlers**

In `addon.py`, import pure helpers near existing imports:

```python
from blender_mcp.interior_design import (
    STANDARD_INTERIOR_COLLECTIONS,
    InteriorValidationError,
    calibration_scale_from_points,
    normalize_project_spec,
    normalize_wall_linework,
    validate_finish_spec,
    audit_finding,
    package_manifest,
)
```

Add handlers inside `_execute_command_internal`'s `handlers` dict:

```python
            "create_interior_project": self.create_interior_project,
            "import_plan_reference": self.import_plan_reference,
            "calibrate_plan_reference": self.calibrate_plan_reference,
            "create_floorplan_linework": self.create_floorplan_linework,
            "extrude_floorplan_shell": self.extrude_floorplan_shell,
            "create_interior_zones": self.create_interior_zones,
            "apply_finish": self.apply_finish,
            "create_finish_schedule": self.create_finish_schedule,
            "setup_interior_lighting_plan": self.setup_interior_lighting_plan,
            "create_interior_camera_set": self.create_interior_camera_set,
            "render_view_set": self.render_view_set,
            "audit_interior_scene": self.audit_interior_scene,
            "export_interior_package": self.export_interior_package,
```

- [ ] **Step 4: Add project scaffold methods**

Add these methods to `BlenderMCPServer` near the existing design-workflow helper section:

```python
    def _get_or_create_collection(self, name, parent=None):
        collection = bpy.data.collections.get(name)
        if collection is None:
            collection = bpy.data.collections.new(name)
        if parent is None:
            if collection.name not in bpy.context.scene.collection.children:
                try:
                    bpy.context.scene.collection.children.link(collection)
                except RuntimeError:
                    pass
        else:
            if collection.name not in parent.children:
                try:
                    parent.children.link(collection)
                except RuntimeError:
                    pass
        return collection

    def _link_object_to_collection(self, obj, collection_name):
        collection = self._get_or_create_collection(collection_name)
        if obj.name not in collection.objects:
            collection.objects.link(obj)
        return collection

    def create_interior_project(self, project_name="Interior Design Project",
                                root_collection="Interior_Project",
                                units="metric", scale_unit="meters",
                                create_standard_collections=True,
                                output_dirs=None):
        try:
            spec = normalize_project_spec({
                "project_name": project_name,
                "units": units,
                "scale_unit": scale_unit,
                "collections": STANDARD_INTERIOR_COLLECTIONS if create_standard_collections else [root_collection],
                "metadata": {"output_dirs": output_dirs or {}},
            })
        except InteriorValidationError as e:
            return {"error": str(e)}

        scene = bpy.context.scene
        scene.unit_settings.system = "METRIC"
        scene.unit_settings.scale_length = 1.0
        scene["interior_project_name"] = spec["project_name"]
        scene["interior_project_units"] = spec["units"]
        scene["interior_project_scale_unit"] = spec["scale_unit"]

        root = self._get_or_create_collection(root_collection)
        created = [root.name]
        if create_standard_collections:
            for child_name in spec["collections"]:
                child = self._get_or_create_collection(child_name, parent=root)
                created.append(child.name)

        return {
            "project_name": spec["project_name"],
            "root_collection": root.name,
            "collections": created,
            "units": {
                "system": scene.unit_settings.system,
                "scale_length": scene.unit_settings.scale_length,
            },
            "output_dirs": output_dirs or {},
        }
```

- [ ] **Step 5: Run full unit test suite**

Run:

```bash
uv run pytest -v
```

Expected:

```text
all tests pass
```

- [ ] **Step 6: Commit**

```bash
git add addon.py tests/test_interior_design.py
git commit -m "feat: add interior project scaffold handler"
```

## Task 4: Implement Image Plan Reference Import and Calibration

**Files:**
- Modify: `addon.py`
- Test: `tests/test_interior_design.py`

- [ ] **Step 1: Add pure extension routing tests**

Append to `tests/test_interior_design.py`:

```python
from blender_mcp.interior_design import classify_plan_reference_path


def test_classify_plan_reference_path():
    assert classify_plan_reference_path("/tmp/plan.png") == "image"
    assert classify_plan_reference_path("/tmp/plan.jpg") == "image"
    assert classify_plan_reference_path("/tmp/plan.jpeg") == "image"
    assert classify_plan_reference_path("/tmp/plan.webp") == "image"
    assert classify_plan_reference_path("/tmp/plan.pdf") == "pdf"


def test_classify_plan_reference_path_rejects_unknown():
    with pytest.raises(InteriorValidationError) as exc:
        classify_plan_reference_path("/tmp/plan.txt")
    assert "Unsupported plan reference file type" in str(exc.value)
```

- [ ] **Step 2: Implement extension helper**

Add to `src/blender_mcp/interior_design.py`:

```python
def classify_plan_reference_path(filepath: str) -> str:
    suffix = str(filepath).lower().rsplit(".", 1)[-1] if "." in str(filepath) else ""
    if suffix in {"png", "jpg", "jpeg", "webp", "tif", "tiff"}:
        return "image"
    if suffix == "pdf":
        return "pdf"
    raise InteriorValidationError(
        "Unsupported plan reference file type. Use PNG, JPG, WEBP, TIFF, or PDF."
    )
```

Add it to the `addon.py` import list.

- [ ] **Step 3: Run tests**

Run:

```bash
uv run pytest tests/test_interior_design.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 4: Implement image import and calibration methods**

Add methods to `BlenderMCPServer`:

```python
    def _plan_material_from_image(self, image_path, name, opacity):
        image = bpy.data.images.load(image_path)
        mat = bpy.data.materials.new(f"{name}_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = image
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Alpha"].default_value = float(opacity)
        mat.blend_method = "BLEND"
        mat.use_screen_refraction = True
        return mat, image

    def import_plan_reference(self, filepath, page=0, name=None,
                              target_plane="XY", known_distance=None,
                              real_world_width_m=None, opacity=0.45,
                              lock_reference=True):
        try:
            kind = classify_plan_reference_path(filepath)
        except InteriorValidationError as e:
            return {"error": str(e)}
        if not os.path.exists(filepath):
            return {"error": f"Plan reference file not found: {filepath}"}
        if target_plane != "XY":
            return {"error": "Only target_plane='XY' is supported in this release"}
        if kind == "pdf":
            return {
                "error": "PDF plan import requires a PDF conversion backend. Export this page to PNG/JPG first, or install PDF support in a later release."
            }

        ref_name = name or os.path.splitext(os.path.basename(filepath))[0] or "Plan_Reference"
        mat, image = self._plan_material_from_image(filepath, ref_name, opacity)
        width_px, height_px = image.size
        width_m = float(real_world_width_m) if real_world_width_m else 1.0
        height_m = width_m * (float(height_px) / float(width_px)) if width_px else width_m

        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
        obj = bpy.context.object
        obj.name = ref_name
        obj.dimensions = (width_m, height_m, 0)
        obj.data.materials.append(mat)
        obj.show_transparent = True
        obj.display_type = "TEXTURED"
        obj["interior_reference_type"] = kind
        obj["interior_reference_path"] = os.path.abspath(filepath)
        obj["interior_reference_width_px"] = int(width_px)
        obj["interior_reference_height_px"] = int(height_px)

        if known_distance:
            try:
                scale = calibration_scale_from_points(
                    known_distance["point_a"],
                    known_distance["point_b"],
                    known_distance["real_distance_m"],
                )
                real_width = scale["meters_per_pixel"] * float(width_px)
                real_height = scale["meters_per_pixel"] * float(height_px)
                obj.dimensions = (real_width, real_height, 0)
                obj["interior_pixels_per_meter"] = scale["pixels_per_meter"]
                obj["interior_meters_per_pixel"] = scale["meters_per_pixel"]
            except (InteriorValidationError, KeyError) as e:
                return {"error": f"Invalid known_distance: {e}"}

        if lock_reference:
            obj.lock_location = (True, True, True)
            obj.lock_rotation = (True, True, True)
            obj.lock_scale = (True, True, True)

        self._link_object_to_collection(obj, "00_REFERENCES")
        self._link_object_to_collection(obj, "01_PLAN")
        return {
            "object_name": obj.name,
            "kind": kind,
            "filepath": os.path.abspath(filepath),
            "size_px": [int(width_px), int(height_px)],
            "dimensions_m": [float(obj.dimensions.x), float(obj.dimensions.y)],
            "calibrated": "interior_pixels_per_meter" in obj,
        }

    def calibrate_plan_reference(self, reference_object, point_a, point_b,
                                 real_distance_m, axis_hint="free"):
        obj = bpy.data.objects.get(reference_object)
        if obj is None:
            return {"error": f"Reference object not found: {reference_object}"}
        try:
            scale = calibration_scale_from_points(point_a, point_b, real_distance_m)
        except InteriorValidationError as e:
            return {"error": str(e)}
        width_px = float(obj.get("interior_reference_width_px", 0))
        height_px = float(obj.get("interior_reference_height_px", 0))
        if width_px <= 0 or height_px <= 0:
            return {"error": f"Reference object '{reference_object}' is missing image dimension metadata"}
        obj.lock_scale = (False, False, False)
        obj.dimensions = (
            scale["meters_per_pixel"] * width_px,
            scale["meters_per_pixel"] * height_px,
            0,
        )
        obj["interior_pixels_per_meter"] = scale["pixels_per_meter"]
        obj["interior_meters_per_pixel"] = scale["meters_per_pixel"]
        obj["interior_calibration_axis_hint"] = axis_hint
        obj.lock_scale = (True, True, True)
        return {
            "object_name": obj.name,
            "pixels_per_meter": scale["pixels_per_meter"],
            "meters_per_pixel": scale["meters_per_pixel"],
            "dimensions_m": [float(obj.dimensions.x), float(obj.dimensions.y)],
        }
```

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/test_interior_design.py tests/test_interior_mcp_tools.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 6: Commit**

```bash
git add addon.py src/blender_mcp/interior_design.py tests/test_interior_design.py
git commit -m "feat: import calibrated interior plan references"
```

## Task 5: Implement Floorplan Linework and Shell Extrusion

**Files:**
- Modify: `addon.py`
- Modify: `src/blender_mcp/interior_design.py`
- Test: `tests/test_interior_design.py`

- [ ] **Step 1: Add wall mesh math tests**

Append to `tests/test_interior_design.py`:

```python
from blender_mcp.interior_design import wall_rect_from_centerline


def test_wall_rect_from_centerline_horizontal():
    rect = wall_rect_from_centerline([0, 0], [4, 0], 0.2)
    assert rect == [[0.0, -0.1], [4.0, -0.1], [4.0, 0.1], [0.0, 0.1]]


def test_wall_rect_from_centerline_vertical():
    rect = wall_rect_from_centerline([2, 1], [2, 5], 0.2)
    assert rect == [[2.1, 1.0], [2.1, 5.0], [1.9, 5.0], [1.9, 1.0]]
```

- [ ] **Step 2: Implement wall rectangle helper**

Add to `src/blender_mcp/interior_design.py`:

```python
def wall_rect_from_centerline(start: list[float], end: list[float], thickness_m: float) -> list[list[float]]:
    s = _ensure_point2(start, "start")
    e = _ensure_point2(end, "end")
    thickness = _ensure_number(thickness_m, "thickness_m")
    if thickness <= 0:
        raise InteriorValidationError("thickness_m must be > 0")
    dx = e[0] - s[0]
    dy = e[1] - s[1]
    length = math.hypot(dx, dy)
    if length <= 0:
        raise InteriorValidationError("start and end must differ")
    nx = -dy / length
    ny = dx / length
    half = thickness / 2.0
    pts = [
        [s[0] + nx * half, s[1] + ny * half],
        [e[0] + nx * half, e[1] + ny * half],
        [e[0] - nx * half, e[1] - ny * half],
        [s[0] - nx * half, s[1] - ny * half],
    ]
    return [[round(x, 10), round(y, 10)] for x, y in pts]
```

- [ ] **Step 3: Run tests**

Run:

```bash
uv run pytest tests/test_interior_design.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 4: Implement linework storage and wall extrusion**

Update `addon.py` import list to include `wall_rect_from_centerline`.

Add methods:

```python
    def create_floorplan_linework(self, linework):
        try:
            normalized = normalize_wall_linework(linework)
        except InteriorValidationError as e:
            return {"error": str(e)}
        scene = bpy.context.scene
        store = json.loads(scene.get("interior_lineworks_json", "{}"))
        store[normalized["name"]] = normalized
        scene["interior_lineworks_json"] = json.dumps(store)
        return {
            "linework_name": normalized["name"],
            "wall_count": len(normalized["walls"]),
            "opening_count": len(normalized["openings"]),
            "room_count": len(normalized["rooms"]),
            "linework": normalized,
        }

    def _create_wall_mesh(self, wall, collection_name):
        rect = wall_rect_from_centerline(wall["start"], wall["end"], wall["thickness_m"])
        h = float(wall["height_m"])
        verts = [
            (rect[0][0], rect[0][1], 0),
            (rect[1][0], rect[1][1], 0),
            (rect[2][0], rect[2][1], 0),
            (rect[3][0], rect[3][1], 0),
            (rect[0][0], rect[0][1], h),
            (rect[1][0], rect[1][1], h),
            (rect[2][0], rect[2][1], h),
            (rect[3][0], rect[3][1], h),
        ]
        faces = [
            (0, 1, 2, 3),
            (4, 7, 6, 5),
            (0, 4, 5, 1),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (3, 7, 4, 0),
        ]
        mesh = bpy.data.meshes.new(f"WallMesh_{wall['id']}")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(f"Wall_{wall['id']}", mesh)
        obj["interior_kind"] = "wall"
        obj["interior_wall_id"] = wall["id"]
        obj["interior_wall_type"] = wall["type"]
        bpy.context.scene.collection.objects.link(obj)
        self._link_object_to_collection(obj, collection_name)
        return obj

    def _create_room_floor_mesh(self, room, thickness, collection_name):
        verts_bottom = [(p[0], p[1], -float(thickness)) for p in room["points"]]
        verts_top = [(p[0], p[1], 0) for p in room["points"]]
        n = len(room["points"])
        verts = verts_bottom + verts_top
        faces = [tuple(range(n)), tuple(range(n, n * 2))]
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, j + n, i + n))
        mesh = bpy.data.meshes.new(f"FloorMesh_{room['id']}")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(f"Floor_{room['id']}", mesh)
        obj["interior_kind"] = "floor"
        obj["interior_room_id"] = room["id"]
        obj["interior_zone"] = room["zone"]
        bpy.context.scene.collection.objects.link(obj)
        self._link_object_to_collection(obj, collection_name)
        return obj

    def extrude_floorplan_shell(self, linework_name,
                                default_wall_height_m=2.8,
                                default_wall_thickness_m=0.12,
                                create_floor=True,
                                floor_thickness_m=0.04,
                                create_ceiling=False,
                                ceiling_height_m=None,
                                boolean_openings=True,
                                collection_name="02_SHELL"):
        store = json.loads(bpy.context.scene.get("interior_lineworks_json", "{}"))
        linework = store.get(linework_name)
        if linework is None:
            return {"error": f"Linework not found: {linework_name}"}

        created = []
        for wall in linework["walls"]:
            wall = dict(wall)
            wall["height_m"] = wall.get("height_m") or default_wall_height_m
            wall["thickness_m"] = wall.get("thickness_m") or default_wall_thickness_m
            obj = self._create_wall_mesh(wall, collection_name)
            created.append(obj.name)

        if create_floor:
            for room in linework.get("rooms", []):
                obj = self._create_room_floor_mesh(room, floor_thickness_m, collection_name)
                created.append(obj.name)

        skipped_openings = []
        if boolean_openings and linework.get("openings"):
            for opening in linework["openings"]:
                skipped_openings.append({
                    "opening_id": opening["id"],
                    "reason": "Opening boolean generation is scheduled for the next implementation slice.",
                })

        return {
            "linework_name": linework_name,
            "created_objects": created,
            "skipped_openings": skipped_openings,
            "create_ceiling": bool(create_ceiling),
            "ceiling_height_m": ceiling_height_m,
        }
```

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/test_interior_design.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 6: Commit**

```bash
git add addon.py src/blender_mcp/interior_design.py tests/test_interior_design.py
git commit -m "feat: extrude interior floorplan linework"
```

## Task 6: Implement Finishes and Finish Schedule

**Files:**
- Modify: `addon.py`
- Modify: `src/blender_mcp/interior_design.py`
- Test: `tests/test_interior_design.py`

- [ ] **Step 1: Add schedule row helper test**

Append to `tests/test_interior_design.py`:

```python
from blender_mcp.interior_design import finish_schedule_row


def test_finish_schedule_row_shape():
    row = finish_schedule_row(
        zone="public_area",
        object_name="Wall_wall_001",
        material_name="Paint_dark",
        finish={"name": "dark paint", "category": "paint", "color_hex": "#123456", "sku": "P-001"},
        area_m2=12.3456,
    )
    assert row["zone"] == "public_area"
    assert row["object_name"] == "Wall_wall_001"
    assert row["area_m2"] == 12.35
    assert row["sku"] == "P-001"
```

- [ ] **Step 2: Implement schedule row helper**

Add to `src/blender_mcp/interior_design.py`:

```python
def finish_schedule_row(
    *,
    zone: str,
    object_name: str,
    material_name: str,
    finish: dict[str, Any],
    area_m2: float | None,
) -> dict[str, Any]:
    validated = validate_finish_spec(finish)
    return {
        "zone": str(zone or ""),
        "object_name": str(object_name),
        "material_name": str(material_name),
        "finish_name": validated["name"],
        "category": validated["category"],
        "color_hex": validated.get("color_hex"),
        "texture_asset_id": validated.get("texture_asset_id"),
        "texture_library": validated.get("texture_library"),
        "manufacturer": validated.get("manufacturer"),
        "sku": validated.get("sku"),
        "notes": validated.get("notes"),
        "area_m2": round(float(area_m2), 2) if area_m2 is not None else None,
    }
```

- [ ] **Step 3: Implement `apply_finish` and `create_finish_schedule`**

Update import list to include `finish_schedule_row`.

Add methods:

```python
    def _objects_for_finish_scope(self, target, scope):
        if scope in ("object", "objects"):
            obj = bpy.data.objects.get(target)
            return [obj] if obj else []
        if scope in ("collection", "zone"):
            coll = bpy.data.collections.get(target)
            return [o for o in coll.objects if getattr(o, "type", None) == "MESH"] if coll else []
        if scope == "selected":
            return [o for o in bpy.context.selected_objects if getattr(o, "type", None) == "MESH"]
        return []

    def apply_finish(self, target, finish, scope="object"):
        try:
            spec = validate_finish_spec(finish)
        except InteriorValidationError as e:
            return {"error": str(e)}
        objects = self._objects_for_finish_scope(target, scope)
        if not objects:
            return {"error": f"No mesh objects found for target '{target}' with scope '{scope}'"}

        material_names = []
        for obj in objects:
            if spec.get("texture_asset_id"):
                applied = self._apply_polyhaven_texture(
                    obj.name,
                    spec["texture_asset_id"],
                    resolution=spec.get("resolution", "2k"),
                    uv_scale=spec.get("uv_scale"),
                )
                if isinstance(applied, dict) and applied.get("error"):
                    return applied
                mat_name = applied.get("set_texture_result", {}).get("material") or applied.get("material")
            elif spec.get("color_hex"):
                applied = self.apply_material_color(
                    obj.name,
                    spec["color_hex"],
                    roughness=float(spec.get("roughness", 0.7)),
                    metallic=float(spec.get("metallic", 0.0)),
                    material_name=spec.get("material_name"),
                )
                if isinstance(applied, dict) and applied.get("error"):
                    return applied
                mat_name = applied.get("material_name")
            else:
                return {"error": "finish requires either color_hex or texture_asset_id"}

            mat = bpy.data.materials.get(mat_name) if mat_name else None
            if mat:
                mat["interior_finish_json"] = json.dumps(spec)
                material_names.append(mat.name)
            obj["interior_finish_name"] = spec["name"]
            obj["interior_finish_category"] = spec["category"]

        return {
            "target": target,
            "scope": scope,
            "object_count": len(objects),
            "materials": material_names,
            "finish": spec,
        }

    def _mesh_area_m2(self, obj):
        if getattr(obj, "type", None) != "MESH":
            return None
        area = 0.0
        for poly in obj.data.polygons:
            area += float(poly.area)
        scale = obj.scale
        return area * abs(float(scale.x) * float(scale.y))

    def create_finish_schedule(self, filepath, scope="scene", include_area_estimates=True):
        targets = []
        if scope == "scene":
            targets = [o for o in bpy.context.scene.objects if getattr(o, "type", None) == "MESH"]
        else:
            coll = bpy.data.collections.get(scope)
            if coll:
                targets = [o for o in coll.objects if getattr(o, "type", None) == "MESH"]
        rows = []
        for obj in targets:
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or "interior_finish_json" not in mat:
                    continue
                finish = json.loads(mat["interior_finish_json"])
                rows.append(finish_schedule_row(
                    zone=obj.get("interior_zone", ""),
                    object_name=obj.name,
                    material_name=mat.name,
                    finish=finish,
                    area_m2=self._mesh_area_m2(obj) if include_area_estimates else None,
                ))

        os.makedirs(os.path.dirname(os.path.abspath(filepath)) or ".", exist_ok=True)
        if filepath.lower().endswith(".csv"):
            import csv
            fieldnames = [
                "zone", "object_name", "material_name", "finish_name",
                "category", "color_hex", "texture_asset_id", "texture_library",
                "manufacturer", "sku", "notes", "area_m2",
            ]
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({"rows": rows}, f, indent=2)
        return {"filepath": os.path.abspath(filepath), "row_count": len(rows), "rows": rows}
```

- [ ] **Step 4: Run tests**

Run:

```bash
uv run pytest tests/test_interior_design.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 5: Commit**

```bash
git add addon.py src/blender_mcp/interior_design.py tests/test_interior_design.py
git commit -m "feat: add interior finishes and schedules"
```

## Task 7: Implement Zones, Lighting, Cameras, and Render Sets

**Files:**
- Modify: `addon.py`
- Test: `tests/test_interior_mcp_tools.py`

- [ ] **Step 1: Add forwarding tests for remaining wrappers**

Append to `tests/test_interior_mcp_tools.py`:

```python
def test_setup_interior_lighting_plan_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"created_lights": ["Ambient_01"]}
    layers = [{"kind": "ambient", "kelvin": 2700, "target_lux": 80}]
    out = _parsed(server.setup_interior_lighting_plan(None, layers=layers))
    assert out["ok"] is True
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "setup_interior_lighting_plan"
    assert params["layers"] == layers


def test_create_interior_camera_set_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"created_cameras": ["Camera_Wide"]}
    views = [{"name": "wide", "kind": "wide"}]
    out = _parsed(server.create_interior_camera_set(None, views=views))
    assert out["ok"] is True
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "create_interior_camera_set"
    assert params["views"] == views


def test_render_view_set_forwards(mock_blender_connection):
    mock_blender_connection.send_command.return_value = {"renders": ["/tmp/wide.png"]}
    out = _parsed(server.render_view_set(None, views=["Camera_Wide"], output_dir="/tmp/renders"))
    assert out["ok"] is True
    cmd, params = mock_blender_connection.send_command.call_args.args
    assert cmd == "render_view_set"
    assert params["output_dir"] == "/tmp/renders"
```

- [ ] **Step 2: Run tests**

Run:

```bash
uv run pytest tests/test_interior_mcp_tools.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 3: Implement zones, lighting, camera, render methods**

Add methods to `BlenderMCPServer`:

```python
    def create_interior_zones(self, zones, create_labels=True, create_bounds=True):
        if not isinstance(zones, list):
            return {"error": "zones must be a list"}
        created = []
        for zone in zones:
            name = str(zone.get("name") or "").strip()
            if not name:
                return {"error": "Each zone requires a name"}
            coll = self._get_or_create_collection(name, parent=self._get_or_create_collection("03_ZONES"))
            coll["interior_zone_kind"] = str(zone.get("kind") or "zone")
            created.append(coll.name)
        return {"zones": created, "create_labels": bool(create_labels), "create_bounds": bool(create_bounds)}

    def setup_interior_lighting_plan(self, zones=None, layers=None,
                                     remove_existing=False,
                                     collection_name="06_LIGHTING"):
        if remove_existing:
            for obj in list(bpy.context.scene.objects):
                if obj.type == "LIGHT" and obj.name.startswith("Interior_"):
                    bpy.data.objects.remove(obj, do_unlink=True)
        layers = layers or [{"kind": "ambient", "kelvin": 2700, "target_lux": 80}]
        created = []
        for idx, layer in enumerate(layers, start=1):
            kind = str(layer.get("kind") or "ambient")
            kelvin = float(layer.get("kelvin", 2700))
            target_lux = float(layer.get("target_lux", 80))
            mount_height = float(layer.get("mount_height_m", 2.7))
            x = float(layer.get("x", idx * 1.5))
            y = float(layer.get("y", 0))
            bpy.ops.object.light_add(type="AREA", location=(x, y, mount_height))
            light = bpy.context.object
            light.name = f"Interior_{kind}_{idx:02d}"
            light.data.name = f"{light.name}_Data"
            light.data.energy = max(10.0, target_lux * 2.0)
            light.data.size = float(layer.get("size_m", 2.0))
            try:
                light.data.color = self._kelvin_to_rgb(kelvin)
            except Exception:
                pass
            light["interior_light_layer"] = kind
            light["interior_kelvin"] = kelvin
            light["interior_target_lux"] = target_lux
            self._link_object_to_collection(light, collection_name)
            created.append(light.name)
        return {"created_lights": created, "layer_count": len(layers), "zones": zones or []}

    def create_interior_camera_set(self, views, targets=None, avoid_walls=True):
        if not isinstance(views, list) or not views:
            return {"error": "views must be a non-empty list"}
        created = []
        for idx, view in enumerate(views, start=1):
            name = str(view.get("name") or view.get("kind") or f"view_{idx:02d}")
            kind = str(view.get("kind") or "wide")
            location = view.get("location") or [4.0, -5.0, 1.6]
            target = view.get("target") or [0.0, 0.0, 1.2]
            bpy.ops.object.camera_add(location=tuple(location))
            cam = bpy.context.object
            cam.name = f"Camera_{name}"
            cam.data.lens = float(view.get("lens_mm", 24 if kind in {"wide", "corner"} else 35))
            direction = mathutils.Vector(target) - cam.location
            cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            cam["interior_view_kind"] = kind
            self._link_object_to_collection(cam, "07_CAMERAS")
            if idx == 1:
                bpy.context.scene.camera = cam
            created.append(cam.name)
        return {"created_cameras": created, "targets": targets or [], "avoid_walls": bool(avoid_walls)}

    def render_view_set(self, views, output_dir, resolution=None, engine="CYCLES",
                        samples=64, view_transform="AgX", return_previews=True):
        if not isinstance(views, list) or not views:
            return {"error": "views must be a non-empty list of camera names"}
        os.makedirs(output_dir, exist_ok=True)
        renders = []
        previous_camera = bpy.context.scene.camera
        for view in views:
            cam = bpy.data.objects.get(view)
            if cam is None or cam.type != "CAMERA":
                return {"error": f"Camera not found: {view}"}
            bpy.context.scene.camera = cam
            filepath = os.path.join(output_dir, f"{view}.png")
            render_result = self.render_image(
                filepath=filepath,
                resolution=resolution,
                samples=samples,
                engine=engine,
                view_transform=view_transform,
                return_preview=return_previews,
            )
            if isinstance(render_result, dict) and render_result.get("error") and view_transform == "AgX":
                render_result = self.render_image(
                    filepath=filepath,
                    resolution=resolution,
                    samples=samples,
                    engine=engine,
                    view_transform="Filmic",
                    return_preview=return_previews,
                )
            if isinstance(render_result, dict) and render_result.get("error"):
                return render_result
            renders.append(render_result)
        bpy.context.scene.camera = previous_camera
        return {"renders": renders, "output_dir": os.path.abspath(output_dir)}
```

- [ ] **Step 4: Run selected tests**

Run:

```bash
uv run pytest tests/test_interior_mcp_tools.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 5: Commit**

```bash
git add addon.py tests/test_interior_mcp_tools.py
git commit -m "feat: add interior zones lighting cameras and render sets"
```

## Task 8: Implement Scene Audit and Package Export

**Files:**
- Modify: `addon.py`
- Test: `tests/test_interior_design.py`

- [ ] **Step 1: Add audit status helper tests**

Append to `tests/test_interior_design.py`:

```python
from blender_mcp.interior_design import audit_status


def test_audit_status():
    assert audit_status([]) == "pass"
    assert audit_status([{"severity": "info"}]) == "pass"
    assert audit_status([{"severity": "warn"}]) == "warn"
    assert audit_status([{"severity": "fail"}]) == "fail"
```

- [ ] **Step 2: Implement audit status helper**

Add to `src/blender_mcp/interior_design.py`:

```python
def audit_status(findings: list[dict[str, Any]]) -> str:
    severities = {f.get("severity") for f in findings}
    if "fail" in severities:
        return "fail"
    if "warn" in severities:
        return "warn"
    return "pass"
```

Import `audit_status` into `addon.py`.

- [ ] **Step 3: Implement audit and export methods**

Add methods to `BlenderMCPServer`:

```python
    def audit_interior_scene(self, checks=None, strict=False, scope="scene"):
        findings = []
        scene = bpy.context.scene
        if scene.unit_settings.system != "METRIC":
            findings.append(audit_finding(
                severity="fail" if strict else "warn",
                code="NON_METRIC_UNITS",
                hint="Run create_interior_project to set metric units.",
                detail=f"Scene unit system is {scene.unit_settings.system}.",
            ))
        if not bpy.data.collections.get("02_SHELL"):
            findings.append(audit_finding(
                severity="warn",
                code="NO_INTERIOR_SHELL",
                hint="Create or import shell geometry before final render/export.",
                detail="Collection 02_SHELL does not exist.",
            ))
        plan_refs = [
            o for o in scene.objects
            if o.get("interior_reference_type") in {"image", "pdf"}
        ]
        for ref in plan_refs:
            if "interior_pixels_per_meter" not in ref:
                findings.append(audit_finding(
                    severity="warn",
                    code="UNCALIBRATED_PLAN",
                    hint="Calibrate the plan reference before measured extrusion.",
                    detail=f"{ref.name} has no calibration metadata.",
                    obj=ref.name,
                ))
        for obj in scene.objects:
            if obj.type == "LIGHT" and obj.name.startswith("Interior_"):
                kelvin = obj.get("interior_kelvin")
                if kelvin is None:
                    findings.append(audit_finding(
                        severity="warn",
                        code="LIGHT_MISSING_KELVIN",
                        hint="Use setup_interior_lighting_plan so light color temperature is auditable.",
                        detail=f"{obj.name} has no interior_kelvin metadata.",
                        obj=obj.name,
                    ))
        status = audit_status(findings)
        return {"status": status, "findings": findings, "strict": bool(strict), "scope": scope}

    def export_interior_package(self, output_dir, package_name, formats=None,
                                include_renders=True,
                                include_finish_schedule=True,
                                include_audit_report=True,
                                pack_textures=True):
        os.makedirs(output_dir, exist_ok=True)
        formats = formats or ["glb"]
        warnings = []
        audit = self.audit_interior_scene()
        if audit["status"] != "pass":
            warnings.extend([f"{f['code']}: {f['hint']}" for f in audit["findings"]])

        exports = []
        for fmt in formats:
            filepath = os.path.join(output_dir, f"{package_name}.{fmt}")
            exported = self.quick_export(filepath=filepath, format=fmt, pack_textures=pack_textures)
            if isinstance(exported, dict) and exported.get("error"):
                return exported
            exports.append(exported.get("filepath", filepath))

        reports = []
        if include_finish_schedule:
            schedule_path = os.path.join(output_dir, f"{package_name}_finish_schedule.json")
            schedule = self.create_finish_schedule(schedule_path)
            if isinstance(schedule, dict) and schedule.get("error"):
                warnings.append(schedule["error"])
            else:
                reports.append(schedule_path)
        if include_audit_report:
            audit_path = os.path.join(output_dir, f"{package_name}_audit.json")
            with open(audit_path, "w", encoding="utf-8") as f:
                json.dump(audit, f, indent=2)
            reports.append(audit_path)

        render_paths = []
        if include_renders:
            render_dir = os.path.join(output_dir, "renders")
            if os.path.isdir(render_dir):
                render_paths = [
                    os.path.join(render_dir, name)
                    for name in sorted(os.listdir(render_dir))
                    if name.lower().endswith((".png", ".jpg", ".jpeg"))
                ]

        manifest = package_manifest(
            package_name=package_name,
            geometry_exports=exports,
            renders=render_paths,
            reports=reports,
            warnings=warnings,
        )
        manifest_path = os.path.join(output_dir, f"{package_name}_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return {"manifest": manifest, "manifest_path": manifest_path}
```

- [ ] **Step 4: Run tests**

Run:

```bash
uv run pytest tests/test_interior_design.py -v
```

Expected:

```text
all selected tests pass
```

- [ ] **Step 5: Run full suite**

Run:

```bash
uv run pytest -v
```

Expected:

```text
all tests pass
```

- [ ] **Step 6: Commit**

```bash
git add addon.py src/blender_mcp/interior_design.py tests/test_interior_design.py
git commit -m "feat: audit and export interior design packages"
```

## Task 9: Documentation and Changelog

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add README section**

Add a neutral "Interior Design Workflow" section to `README.md`:

```markdown
## Interior Design Workflow

This fork includes generic interior-design tools for measured blockouts,
finish studies, lighting plans, render sets, and export packages.

Core workflow:

1. `create_interior_project(...)`
2. `import_plan_reference(filepath="/absolute/path/plan.png", known_distance=...)`
3. `create_floorplan_linework(linework={...})`
4. `extrude_floorplan_shell(linework_name="...")`
5. `apply_finish(target="...", finish={...})`
6. `setup_interior_lighting_plan(layers=[...])`
7. `create_interior_camera_set(views=[...])`
8. `render_view_set(views=[...], output_dir="...")`
9. `audit_interior_scene()`
10. `export_interior_package(output_dir="...", package_name="...")`

The tools are project-neutral. Put client-specific palettes, budgets, zones,
and finish decisions in caller-provided specs rather than in code.
```

- [ ] **Step 2: Add changelog entry**

Add a new top entry to `CHANGELOG.md`:

```markdown
## [2.3.0+fork.1] — 2026-04-29

Generic interior-design workflow layer.

### Added
- `create_interior_project` for metric scene setup and standard collections.
- `import_plan_reference` and `calibrate_plan_reference` for image floor plans and measured drawings.
- `create_floorplan_linework` and `extrude_floorplan_shell` for measured 2D wall specs to 3D blockout geometry.
- `create_interior_zones`, `apply_finish`, and `create_finish_schedule` for zone and finish workflows.
- `setup_interior_lighting_plan`, `create_interior_camera_set`, and `render_view_set` for design presentation views.
- `audit_interior_scene` and `export_interior_package` for handoff checks and export manifests.

### Notes
- The feature is generic and data-driven. Client-specific palettes, budgets, and site facts belong in external caller specs, not in the tool code.
- PDF floor-plan import returns a clear error unless a PDF conversion backend is added in a later slice.
```

- [ ] **Step 3: Run private-project term scan**

Run:

```bash
python - <<'PY'
import os
import pathlib
import sys

terms = [t for t in os.environ.get("PRIVATE_PROJECT_TERMS", "").splitlines() if t.strip()]
if not terms:
    raise SystemExit("Set PRIVATE_PROJECT_TERMS to newline-separated private terms before release.")

roots = [pathlib.Path(p) for p in ("src", "tests", "README.md", "CHANGELOG.md", "docs/superpowers")]
hits = []
for root in roots:
    paths = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for term in terms:
            if term in text:
                hits.append(f"{path}: contains private term")
if hits:
    print("\n".join(hits))
    sys.exit(1)
PY
```

Expected:

```text
no output
```

- [ ] **Step 4: Run full tests**

Run:

```bash
uv run pytest -v
```

Expected:

```text
all tests pass
```

- [ ] **Step 5: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: document generic interior design workflow"
```

## Task 10: Manual Blender Verification

**Files:**
- No code changes unless failures are found.

- [ ] **Step 1: Start Blender and connect addon**

Open Blender, enable the addon, and click the MCP connect button.

- [ ] **Step 2: Run MCP verification flow**

Use MCP tools in this order:

```text
create_interior_project(project_name="Generic Interior Verification")
import_plan_reference(filepath="/absolute/path/to/generic_plan.png", real_world_width_m=6.0)
calibrate_plan_reference(reference_object="generic_plan", point_a=[0,0], point_b=[300,0], real_distance_m=6.0)
create_floorplan_linework(linework={
  "name": "Verification Plan",
  "walls": [
    {"start": [0, 0], "end": [6, 0]},
    {"start": [6, 0], "end": [6, 4]},
    {"start": [6, 4], "end": [0, 4]},
    {"start": [0, 4], "end": [0, 0]}
  ],
  "rooms": [
    {"name": "main_room", "points": [[0,0], [6,0], [6,4], [0,4]]}
  ]
})
extrude_floorplan_shell(linework_name="Verification Plan")
apply_finish(target="Wall_wall_001", finish={"name":"neutral paint","category":"paint","color_hex":"#808080"})
setup_interior_lighting_plan(layers=[{"kind":"ambient","kelvin":2700,"target_lux":80}])
create_interior_camera_set(views=[{"name":"wide","kind":"wide","location":[5,-6,1.6],"target":[3,2,1.2]}])
render_view_set(views=["Camera_wide"], output_dir="/tmp/interior_verification_renders")
audit_interior_scene()
export_interior_package(output_dir="/tmp/interior_verification_package", package_name="interior_verification")
```

- [ ] **Step 3: Verify outputs**

Expected:

```text
- A calibrated plan reference plane exists.
- Four walls and one floor are visible.
- A camera renders a non-empty PNG.
- audit_interior_scene returns pass or warn with actionable findings.
- export package contains GLB and JSON reports.
```

- [ ] **Step 4: Fix any failures and commit**

If code changes were needed:

```bash
git add addon.py src tests README.md CHANGELOG.md
git commit -m "fix: pass interior design verification flow"
```

## Self-Review

Spec coverage:

- Project scaffold: Task 3.
- Image/PDF plan reference and calibration: Task 4.
- Floor-plan linework to 3D shell: Task 5.
- Zones, finishes, finish schedule: Tasks 6 and 7.
- Lighting, cameras, render sets: Task 7.
- Audit and export package: Task 8.
- Documentation and genericity scan: Task 9.
- Manual Blender validation: Task 10.

Private-project boundary:

- Tool names are generic.
- Test sample names are generic.
- The private-project term scan in Task 9 is mandatory before completion.

Scope:

- P0 does image plan import and explicit linework-to-shell.
- PDF import is intentionally allowed to fail clearly until a PDF backend is chosen.
- Automatic CV line detection is not included in this implementation plan.

Execution handoff:

Plan complete and saved to `docs/dev/plans/2026-04-29-interior-design-mcp.md`. Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. Inline Execution - execute tasks in this session using executing-plans, batch execution with checkpoints.
