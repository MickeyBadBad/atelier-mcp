"""Quality-gate validators for the Interior Design Workflow (Slice 3).

Per the workflow spec § "Quality Gates — 9 Dimensions", every interior
render passes through 9 validators before being declared ready. Each
validator is a pure Python function — the AI client fetches scene_info
via the existing fork tool `get_scene_info(full=True)` and passes it in.

Severity tiers (γ-mode adapted):
- HARD   — blocks render unless caller passes force=True
- SOFT   — warns before render, caller decides whether to continue
- INFO   — silently records in the audit report

Strictness modes:
- EXPLORATION (Stages 0-4, L1 loops): only HARD enforced
- HERO        (Stage 5 final, Stage 6): HARD + SOFT + INFO active
- CONSTRUCTION (Stage 6.5): all + dimension #9 upgraded to HARD

Every finding carries a handbook citation so the AI explanation to the
user can trace back to the source rule.
"""
from __future__ import annotations

import enum
from typing import Any, Dict, List, NamedTuple, Optional


class Severity(str, enum.Enum):
    HARD = "hard"
    SOFT = "soft"
    INFO = "info"


class StrictnessMode(str, enum.Enum):
    EXPLORATION = "exploration"
    HERO = "hero"
    CONSTRUCTION = "construction"


class Finding(NamedTuple):
    gate: str
    severity: Severity
    message: str
    citation: str
    suggested_fix: str = ""


# ----- Kelvin ranges by project type (sourced from lighting.md / GB 50034) -----

KELVIN_RANGES_BY_PROJECT_TYPE: Dict[str, tuple] = {
    "residential_apartment": (2700, 3000),
    "residential_house": (2700, 3000),
    "cafe_lounge": (2200, 3000),  # speakeasy/lounge convention
    "restaurant_full_service": (2400, 3000),
    "retail_boutique": (3000, 4000),
    "office_small": (3500, 4000),
}


# Furniture scale sanity bounds (per furniture.md)
SCALE_BANDS_M: Dict[str, tuple] = {
    "sofa": (0.65, 1.10),       # height
    "chair": (0.70, 1.10),
    "table_dining": (0.72, 0.78),
    "table_coffee": (0.35, 0.48),
    "bed": (0.40, 0.65),
    "door": (1.90, 2.40),
    "wardrobe": (1.80, 2.40),
}


def _is_temp(name: str) -> bool:
    return name.startswith("_") or name.lower().startswith("temp")


# ----- Gate 1: Materials -----

def check_materials(scene_info: Dict[str, Any]) -> List[Finding]:
    """Every non-temp mesh object must carry albedo or roughness data."""
    findings: List[Finding] = []
    for obj in scene_info.get("objects", []):
        if obj.get("type") != "MESH":
            continue
        name = obj.get("name", "")
        if _is_temp(name):
            continue
        has_albedo = bool(obj.get("has_albedo_map"))
        has_rough = bool(obj.get("has_roughness_map"))
        if not (has_albedo or has_rough):
            findings.append(Finding(
                gate="materials",
                severity=Severity.HARD,
                message=(
                    f"Object '{name}' has no albedo or roughness map. "
                    "Plain Principled BSDF reads as plastic."
                ),
                citation=(
                    "materials.md §PBR principles "
                    "(per Disney BSDF Burley 2012; LearnOpenGL PBR)"
                ),
                suggested_fix=(
                    "apply_archviz_material(name='wood'|'plaster'|... ) "
                    "or set_texture(...) on this object"
                ),
            ))
    return findings


# ----- Gate 2: Lighting layers -----

def check_lighting_layers(scene_info: Dict[str, Any]) -> List[Finding]:
    """At least 2 light layers (ambient + accent minimum)."""
    lights = scene_info.get("lights", [])
    layers = {lt.get("layer", "ambient") for lt in lights}
    if len(layers) < 2:
        return [Finding(
            gate="lighting_layers",
            severity=Severity.HARD,
            message=(
                f"Scene has {len(layers)} light layer(s). Interior renders "
                "need at least ambient + accent."
            ),
            citation=(
                "lighting.md §Four-layer model (per IES Lighting Handbook "
                "10th ed., indoor lighting)"
            ),
            suggested_fix=(
                "setup_lighting(zones=['<zone>'], layers=['ambient','accent'])"
            ),
        )]
    return []


# ----- Gate 3: Kelvin in range -----

def check_kelvin_range(
    scene_info: Dict[str, Any],
    project: Optional[Dict[str, Any]] = None,
) -> List[Finding]:
    """All lights must have Kelvin metadata within the project-type range."""
    if not project:
        return []
    project_type = project.get("project_type")
    rng = KELVIN_RANGES_BY_PROJECT_TYPE.get(project_type)
    if not rng:
        return []
    lo, hi = rng
    findings: List[Finding] = []
    for lt in scene_info.get("lights", []):
        kelvin = lt.get("kelvin")
        if kelvin is None:
            continue  # missing metadata is a separate concern
        if not (lo <= kelvin <= hi):
            findings.append(Finding(
                gate="kelvin_range",
                severity=Severity.SOFT,
                message=(
                    f"Light '{lt.get('name', '?')}' is at {kelvin}K. "
                    f"Project type '{project_type}' expects {lo}-{hi}K."
                ),
                citation=(
                    "lighting.md §Kelvin by space type "
                    "(per GB 50034-2013; IES Lighting Handbook)"
                ),
                suggested_fix=(
                    f"set the light's Kelvin into [{lo}, {hi}] range"
                ),
            ))
    return findings


# ----- Gate 4: Camera parameters -----

def check_camera_params(scene_info: Dict[str, Any]) -> List[Finding]:
    """Each camera: focal 18-35mm, height 1.4-1.7m, no wall clipping."""
    findings: List[Finding] = []
    for cam in scene_info.get("cameras", []):
        name = cam.get("name", "?")
        focal = cam.get("focal_mm")
        if focal is not None and not (18 <= focal <= 35):
            findings.append(Finding(
                gate="camera_focal",
                severity=Severity.HARD,
                message=(
                    f"Camera '{name}' focal length {focal}mm is outside "
                    "the 18-35mm interior range."
                ),
                citation=(
                    "camera.md §Lens choice (per McGrath; ASMP "
                    "architectural photography guidelines)"
                ),
                suggested_fix=f"set_camera_view(name='{name}', lens=24)",
            ))
        height = cam.get("height_m")
        if height is not None and not (1.4 <= height <= 1.7):
            findings.append(Finding(
                gate="camera_height",
                severity=Severity.HARD,
                message=(
                    f"Camera '{name}' height {height}m outside the "
                    "1.4-1.7m interior eye-level range."
                ),
                citation=(
                    "camera.md §Camera height "
                    "(per Panero & Zelnik 1979; spatial.md cross-ref)"
                ),
                suggested_fix=(
                    f"set_camera_view(name='{name}', position=[..., 1.55])"
                ),
            ))
        if cam.get("inside_wall"):
            findings.append(Finding(
                gate="camera_clipping",
                severity=Severity.HARD,
                message=(
                    f"Camera '{name}' is inside or clipping a wall mesh."
                ),
                citation="camera.md §Common mistakes (geometry collisions)",
                suggested_fix=(
                    f"frame_camera_to_objects(name='{name}', "
                    "camera_xyz=[from outside the wall])"
                ),
            ))
        near = cam.get("near_clip")
        if near is not None and near > 0.05:
            findings.append(Finding(
                gate="camera_clipping",
                severity=Severity.SOFT,
                message=(
                    f"Camera '{name}' near plane {near}m may clip "
                    "foreground props (ideal < 0.05m)."
                ),
                citation="camera.md §Common mistakes",
                suggested_fix=f"set near clip to 0.01 on '{name}'",
            ))
    return findings


# ----- Gate 5: Color management -----

def check_color_management(scene_info: Dict[str, Any]) -> List[Finding]:
    """View transform must be AgX (preferred) or Filmic (fallback)."""
    vt = scene_info.get("view_transform", "")
    if vt not in ("AgX", "Filmic"):
        return [Finding(
            gate="color_management",
            severity=Severity.HARD,
            message=(
                f"View transform is '{vt}'. Interior renders require AgX "
                "(or Filmic as fallback) — Standard sRGB clips highlights."
            ),
            citation=(
                "render-output.md §View transforms "
                "(per Blender Manual Color Management; AgX rationale)"
            ),
            suggested_fix=(
                "set bpy.context.scene.view_settings.view_transform = 'AgX'"
            ),
        )]
    return []


# ----- Gate 6: Render samples -----

def check_render_samples(
    scene_info: Dict[str, Any],
    mode: StrictnessMode = StrictnessMode.HERO,
) -> List[Finding]:
    """Cycles ≥ 64 / EEVEE Next ≥ 32 in exploration; ≥ 512 / ≥ 128 for hero."""
    rs = scene_info.get("render_settings", {})
    cycles = rs.get("cycles_samples", 0)
    eevee = rs.get("eevee_samples", 0)
    engine = rs.get("engine", "CYCLES").upper()
    if mode == StrictnessMode.EXPLORATION:
        cy_floor, ee_floor = 64, 32
    else:
        cy_floor, ee_floor = 512, 128
    findings: List[Finding] = []
    if engine == "CYCLES" and cycles < cy_floor:
        findings.append(Finding(
            gate="render_samples",
            severity=Severity.SOFT,
            message=(
                f"Cycles samples {cycles} below {cy_floor} floor for "
                f"{mode.value} mode."
            ),
            citation=(
                "render-output.md §Sample counts "
                "(per Blender Manual Cycles sampling)"
            ),
            suggested_fix=(
                f"render_image(samples={cy_floor}) "
                "(plus enable OpenImageDenoise)"
            ),
        ))
    elif engine.startswith("EEVEE") and eevee < ee_floor:
        findings.append(Finding(
            gate="render_samples",
            severity=Severity.SOFT,
            message=(
                f"EEVEE Next samples {eevee} below {ee_floor} floor."
            ),
            citation="render-output.md §Sample counts",
            suggested_fix=f"render_image(samples={ee_floor})",
        ))
    return findings


# ----- Gate 7: Prop density -----

def check_prop_density(
    scene_info: Dict[str, Any],
    threshold_per_m2: float = 0.5,
) -> List[Finding]:
    """At least N props per m². Empty rooms read as kid-drawing renders."""
    objects = scene_info.get("objects", [])
    props = [o for o in objects if o.get("is_prop")]
    area = scene_info.get("scene_meta", {}).get("floor_area_m2")
    if not area or area <= 0:
        return []
    density = len(props) / area
    if density < threshold_per_m2:
        return [Finding(
            gate="prop_density",
            severity=Severity.SOFT,
            message=(
                f"Prop density {density:.2f}/m² (target ≥ {threshold_per_m2}). "
                "Empty surfaces read as unfurnished."
            ),
            citation=(
                "styling.md §Prop density "
                "(per Rockport Interior Design Reference; "
                "AD coffee-table styling features)"
            ),
            suggested_fix=(
                "scatter_on_surface(...) for plants/books, then a "
                "vignette per styling.md's triangle composition rule"
            ),
        )]
    return []


# ----- Gate 8: Scale sanity -----

def check_scale_sanity(scene_info: Dict[str, Any]) -> List[Finding]:
    """Furniture / fixtures within published dimension bands per furniture.md."""
    findings: List[Finding] = []
    for obj in scene_info.get("objects", []):
        if obj.get("type") != "MESH":
            continue
        name = obj.get("name", "?")
        if _is_temp(name):
            continue
        category = obj.get("category", "")
        height = obj.get("height_m")
        if height is None or category not in SCALE_BANDS_M:
            continue
        lo, hi = SCALE_BANDS_M[category]
        if not (lo <= height <= hi):
            findings.append(Finding(
                gate="scale_sanity",
                severity=Severity.HARD,
                message=(
                    f"Object '{name}' (category={category}) height "
                    f"{height}m outside the typical {lo}-{hi}m band."
                ),
                citation=(
                    "furniture.md §Standard dimensions "
                    "(per Neufert; Panero & Zelnik 1979)"
                ),
                suggested_fix=(
                    f"normalize the object's scale so its height is "
                    f"within [{lo}, {hi}] m, or pick a different asset"
                ),
            ))
    return findings


# ----- Gate 9: Texture packing -----

def check_texture_packing(
    scene_info: Dict[str, Any],
    mode: StrictnessMode = StrictnessMode.EXPLORATION,
) -> List[Finding]:
    """Final + construction-doc renders must have textures packed."""
    pack = scene_info.get("scene_meta", {}).get("pack_resources", False)
    if pack:
        return []
    if mode == StrictnessMode.CONSTRUCTION:
        sev = Severity.HARD
    elif mode == StrictnessMode.HERO:
        sev = Severity.SOFT
    else:
        sev = Severity.INFO
    return [Finding(
        gate="texture_packing",
        severity=sev,
        message=(
            "Scene has external (unpacked) textures. Delivery files "
            "with unpacked textures break on the contractor's machine."
        ),
        citation=(
            "render-output.md §Texture packing for handoff "
            "(per Blender Manual Packed Data)"
        ),
        suggested_fix=(
            "File › External Data › Pack Resources, or "
            "quick_export(pack_textures=True)"
        ),
    )]


# ----- Audit entrypoint -----

GATE_FUNCTIONS = (
    check_materials,
    check_lighting_layers,
    check_color_management,
    check_camera_params,
    check_scale_sanity,
)

# Gates that need extra args:
def _run_kelvin(scene, project, mode):
    return check_kelvin_range(scene, project)


def _run_render_samples(scene, project, mode):
    return check_render_samples(scene, mode)


def _run_prop_density(scene, project, mode):
    return check_prop_density(scene)


def _run_texture_packing(scene, project, mode):
    return check_texture_packing(scene, mode)


def run_audit(
    scene_info: Dict[str, Any],
    mode: StrictnessMode = StrictnessMode.HERO,
    project: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run all 9 gates and return a single audit report.

    EXPLORATION mode drops SOFT/INFO findings (only HARD blockers).
    HERO mode keeps everything.
    CONSTRUCTION mode keeps everything + upgrades texture-packing to HARD
    (already handled inside check_texture_packing).

    Returns:
        {"mode": str, "status": "pass" | "warn" | "fail",
         "findings": list[Finding]}
    """
    if not isinstance(mode, StrictnessMode):
        mode = StrictnessMode(str(mode).lower())

    all_findings: List[Finding] = []

    # No-extra-arg gates
    for fn in GATE_FUNCTIONS:
        all_findings.extend(fn(scene_info))
    # Extra-arg gates
    all_findings.extend(_run_kelvin(scene_info, project, mode))
    all_findings.extend(_run_render_samples(scene_info, project, mode))
    all_findings.extend(_run_prop_density(scene_info, project, mode))
    all_findings.extend(_run_texture_packing(scene_info, project, mode))

    # Filter by mode
    if mode == StrictnessMode.EXPLORATION:
        all_findings = [f for f in all_findings if f.severity == Severity.HARD]

    severities = {f.severity for f in all_findings}
    if Severity.HARD in severities:
        status = "fail"
    elif Severity.SOFT in severities:
        status = "warn"
    else:
        status = "pass"

    return {
        "mode": mode.value,
        "status": status,
        "findings": all_findings,
    }
