"""Pure-Python project schema + taste-profile I/O.

A project record describes the top-level state of an interior design
project. taste-profile.json is the Discovery output that drives all
downstream design decisions (style locking, material selection,
lighting plan, etc.).

Both records are persisted as JSON sidecars in the project root, next
to the .blend file — explicit, human-editable, version-controllable.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List


class ProjectError(Exception):
    """Raised on invalid project type or taste-profile I/O failures."""


# Canonical project-type taxonomy. Keep in sync with
# docs/handbook/project-types.md.
PROJECT_TYPES = (
    "residential_apartment",
    "residential_house",
    "cafe_lounge",
    "restaurant_full_service",
    "retail_boutique",
    "office_small",
)


# Standard top-level Blender collection names per the workflow spec
# § "Project State" / "Blender collections inside <project>.blend".
STANDARD_COLLECTIONS = (
    "00_REFERENCES", "01_PLAN", "02_SHELL", "03_ZONES",
    "04_FINISHES", "05_FIXTURES", "06_LIGHTING", "07_CAMERAS",
    "08_RENDER_OUT", "09_EXPORT", "90_VARIANTS",
)


def write_project(path: Path, record: Dict[str, Any]) -> None:
    """Write a project record to a JSON file (utf-8, indent=2)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def read_project(path: Path) -> Dict[str, Any]:
    """Read a project record from JSON; raise ProjectError on failure."""
    path = Path(path)
    if not path.is_file():
        raise ProjectError(f"project file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ProjectError(f"corrupt project json: {e}") from e


def new_project_record(
    project_name: str,
    project_type: str,
    spaces: List[str],
    units: str = "metric",
) -> Dict[str, Any]:
    """Validate inputs and return a project record dict."""
    if project_type not in PROJECT_TYPES:
        raise ProjectError(
            f"unknown project_type '{project_type}'. "
            f"valid: {sorted(PROJECT_TYPES)}"
        )
    if not project_name or not project_name.strip():
        raise ProjectError("project_name must not be empty")
    if not spaces:
        raise ProjectError("spaces list must not be empty")
    return {
        "project_name": project_name.strip(),
        "project_type": project_type,
        "spaces": list(spaces),
        "units": units,
        "standard_collections": list(STANDARD_COLLECTIONS),
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_taste_profile(path: Path, profile: Dict[str, Any]) -> None:
    """Atomic-ish write of a JSON profile."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def read_taste_profile(path: Path) -> Dict[str, Any]:
    """Load taste-profile.json. Raises ProjectError on missing/corrupt."""
    path = Path(path)
    if not path.is_file():
        raise ProjectError(f"taste-profile not found at {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ProjectError(
            f"failed to read taste-profile at {path}: {e}"
        ) from e


def update_taste_profile(
    path: Path, updates: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge updates into the existing profile (or create if absent)."""
    path = Path(path)
    base: Dict[str, Any] = {}
    if path.is_file():
        base = read_taste_profile(path)
    base.update(updates)
    write_taste_profile(path, base)
    return base
