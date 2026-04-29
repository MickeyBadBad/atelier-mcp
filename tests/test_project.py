"""Tests for project schema + taste-profile read/write."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from blender_mcp._project import (
    PROJECT_TYPES,
    ProjectError,
    new_project_record,
    read_taste_profile,
    update_taste_profile,
    write_taste_profile,
)


def test_project_types_canonical():
    expected = {
        "residential_apartment", "residential_house",
        "cafe_lounge", "restaurant_full_service",
        "retail_boutique", "office_small",
    }
    assert set(PROJECT_TYPES) == expected


def test_new_project_record_fills_defaults():
    rec = new_project_record(
        project_name="My Apt",
        project_type="residential_apartment",
        spaces=["living", "bedroom", "kitchen"],
    )
    assert rec["project_name"] == "My Apt"
    assert rec["project_type"] == "residential_apartment"
    assert rec["spaces"] == ["living", "bedroom", "kitchen"]
    assert rec["units"] == "metric"
    assert "created_at" in rec
    assert "standard_collections" in rec


def test_new_project_rejects_unknown_type():
    with pytest.raises(ProjectError):
        new_project_record(
            project_name="X",
            project_type="bogus_type",
            spaces=["living"],
        )


def test_new_project_rejects_empty_name():
    with pytest.raises(ProjectError):
        new_project_record(
            project_name="   ",
            project_type="residential_apartment",
            spaces=["living"],
        )


def test_new_project_rejects_empty_spaces():
    with pytest.raises(ProjectError):
        new_project_record(
            project_name="X",
            project_type="residential_apartment",
            spaces=[],
        )


def test_write_and_read_taste_profile(tmp_path):
    path = tmp_path / "taste-profile.json"
    profile = {
        "version": 1,
        "feeling_anchors": ["warm"],
        "style_axes": {"warmth": 0.5},
        "recommended_style": "scandinavian",
    }
    write_taste_profile(path, profile)
    loaded = read_taste_profile(path)
    assert loaded["recommended_style"] == "scandinavian"
    assert loaded["style_axes"]["warmth"] == 0.5


def test_write_taste_profile_creates_parent_dirs(tmp_path):
    path = tmp_path / "deeply" / "nested" / "taste-profile.json"
    write_taste_profile(path, {"version": 1})
    assert path.is_file()


def test_update_taste_profile_merges_new_fields(tmp_path):
    path = tmp_path / "taste-profile.json"
    write_taste_profile(path, {"version": 1, "feeling_anchors": ["warm"]})
    update_taste_profile(path, {"locked_style": "scandinavian"})
    loaded = read_taste_profile(path)
    assert loaded["locked_style"] == "scandinavian"
    assert loaded["feeling_anchors"] == ["warm"]
    assert loaded["version"] == 1


def test_update_taste_profile_creates_when_absent(tmp_path):
    path = tmp_path / "taste-profile.json"
    update_taste_profile(path, {"version": 1, "starter": "ok"})
    assert path.is_file()


def test_read_taste_profile_missing_raises(tmp_path):
    with pytest.raises(ProjectError):
        read_taste_profile(tmp_path / "nonexistent.json")


def test_read_taste_profile_corrupt_raises(tmp_path):
    path = tmp_path / "taste-profile.json"
    path.write_text("not valid json {", encoding="utf-8")
    with pytest.raises(ProjectError):
        read_taste_profile(path)
