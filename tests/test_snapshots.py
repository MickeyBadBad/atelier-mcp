"""Tests for snapshot directory layout + version log."""
from __future__ import annotations

import time

import pytest

from blender_mcp._snapshots import (
    LoopLevel,
    SnapshotError,
    snapshot_create,
    snapshot_list,
    snapshot_read,
    version_log_append,
    version_log_read,
)


def test_snapshot_create_writes_directory(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    blend = project_root / "scene.blend"
    blend.write_bytes(b"fake-blend-bytes")
    profile = project_root / "taste-profile.json"
    profile.write_text('{"version": 1}')

    snap = snapshot_create(
        project_root=project_root,
        label="phase-3-shell-complete",
        files=[blend, profile],
    )
    assert snap["path"].is_dir()
    assert (snap["path"] / "scene.blend").is_file()
    assert (snap["path"] / "taste-profile.json").is_file()
    assert (snap["path"] / "manifest.json").is_file()
    assert snap["label"] == "phase-3-shell-complete"


def test_snapshot_create_sanitizes_label(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    f = project_root / "x.json"
    f.write_text("{}")
    snap = snapshot_create(
        project_root=project_root,
        label="phase 3 / shell complete!",
        files=[f],
    )
    # Original label preserved in manifest, but directory name is sanitized
    assert snap["label"] == "phase 3 / shell complete!"
    assert snap["path"].is_dir()
    assert "/" not in snap["path"].name
    assert " " not in snap["path"].name or "-" in snap["path"].name


def test_snapshot_list_returns_chronological(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    blend = project_root / "scene.blend"
    blend.write_bytes(b"a")
    snapshot_create(project_root=project_root, label="v1", files=[blend])
    # Sleep briefly so the second timestamp is > first
    time.sleep(1.1)
    snapshot_create(project_root=project_root, label="v2", files=[blend])
    listed = snapshot_list(project_root)
    assert len(listed) == 2
    # Most recent first
    assert listed[0]["label"] == "v2"
    assert listed[1]["label"] == "v1"


def test_snapshot_list_empty_when_no_snapshots(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    assert snapshot_list(project_root) == []


def test_version_log_append_and_read(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    version_log_append(
        project_root,
        level=LoopLevel.L3,
        why="user changed sofa layout from L-shape to two-facing",
        snapshot_label="phase-4-pre-layout-change",
    )
    version_log_append(
        project_root,
        level=LoopLevel.L4,
        why="user pivoted from Scandinavian to Japanese 侘寂",
        snapshot_label="phase-2.5-pre-style-pivot",
    )
    log = version_log_read(project_root)
    assert len(log) == 2
    assert log[0]["level"] == "L3"
    assert log[1]["level"] == "L4"
    assert "timestamp" in log[0]


def test_version_log_read_empty_when_absent(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    assert version_log_read(project_root) == []


def test_snapshot_create_rejects_missing_file(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    with pytest.raises(SnapshotError):
        snapshot_create(
            project_root=project_root,
            label="bad",
            files=[project_root / "does-not-exist.blend"],
        )


def test_snapshot_create_rejects_empty_label(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    f = project_root / "x.json"
    f.write_text("{}")
    with pytest.raises(SnapshotError):
        snapshot_create(project_root=project_root, label="!!!", files=[f])
