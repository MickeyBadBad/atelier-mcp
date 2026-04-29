"""Pure-Python snapshot + version log infrastructure.

Snapshots live under `<project_root>/snapshots/<timestamp>-<label>/`.
Each snapshot is a directory containing copies of the named files plus
a manifest.json. The version log is a single `version-log.json` at the
project root recording L1–L4 loop transitions per the workflow spec.
"""
from __future__ import annotations

import datetime
import enum
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List


class SnapshotError(Exception):
    """Raised on snapshot I/O failures."""


class LoopLevel(str, enum.Enum):
    L1 = "L1"  # tweak (within Stage 5)
    L2 = "L2"  # material/light swap
    L3 = "L3"  # layout / Stage 3-4 change
    L4 = "L4"  # style redo / Stage 2.5 pivot


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _utc_now_for_dirname() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )


def _snapshots_dir(project_root: Path) -> Path:
    return Path(project_root) / "snapshots"


def _version_log_path(project_root: Path) -> Path:
    return Path(project_root) / "version-log.json"


def _sanitize_label(label: str) -> str:
    """Map an arbitrary label to a safe directory-name fragment."""
    cleaned = "".join(
        c if c.isalnum() or c in "-_." else "-" for c in label
    )
    # Collapse runs of dashes to single
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-_.")


def snapshot_create(
    project_root: Path,
    label: str,
    files: List[Path],
) -> Dict[str, Any]:
    """Create a snapshot directory containing copies of the listed files."""
    project_root = Path(project_root)
    if not project_root.is_dir():
        raise SnapshotError(f"project_root not a directory: {project_root}")

    safe_label = _sanitize_label(label)
    if not safe_label:
        raise SnapshotError(
            f"label '{label}' resolved to an empty/invalid string"
        )

    target = _snapshots_dir(project_root) / (
        f"{_utc_now_for_dirname()}-{safe_label}"
    )
    target.mkdir(parents=True, exist_ok=True)

    copied: List[str] = []
    for src in files:
        src = Path(src)
        if not src.is_file():
            raise SnapshotError(f"file not found: {src}")
        shutil.copy2(src, target / src.name)
        copied.append(src.name)

    manifest = {
        "label": label,
        "created_at": _utc_now_iso(),
        "files": copied,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"path": target, "label": label, "files": copied}


def snapshot_list(project_root: Path) -> List[Dict[str, Any]]:
    """Return all snapshots in reverse chronological order."""
    snap_dir = _snapshots_dir(Path(project_root))
    if not snap_dir.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    for entry in sorted(snap_dir.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        manifest = entry / "manifest.json"
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["path"] = str(entry)
            out.append(data)
    return out


def snapshot_read(
    project_root: Path, snapshot_dir_name: str,
) -> Dict[str, Any]:
    """Read a single snapshot's manifest by directory name."""
    target = _snapshots_dir(Path(project_root)) / snapshot_dir_name
    manifest = target / "manifest.json"
    if not manifest.is_file():
        raise SnapshotError(f"snapshot manifest missing: {manifest}")
    return json.loads(manifest.read_text(encoding="utf-8"))


def version_log_append(
    project_root: Path,
    level: LoopLevel,
    why: str,
    snapshot_label: str = "",
) -> None:
    """Append a single entry to version-log.json."""
    log_path = _version_log_path(Path(project_root))
    log: List[Dict[str, Any]] = []
    if log_path.is_file():
        try:
            log = json.loads(log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SnapshotError(f"corrupt version-log.json: {e}") from e
    log.append({
        "timestamp": _utc_now_iso(),
        "level": level.value,
        "why": why,
        "snapshot_label": snapshot_label,
    })
    log_path.write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def version_log_read(project_root: Path) -> List[Dict[str, Any]]:
    """Return all version-log entries, oldest first."""
    log_path = _version_log_path(Path(project_root))
    if not log_path.is_file():
        return []
    return json.loads(log_path.read_text(encoding="utf-8"))
