"""Tests for BoM aggregation."""
from __future__ import annotations

import pytest

from blender_mcp._bom import (
    bom_summary,
    collect_bom_rows,
    render_bom_csv,
    render_bom_markdown,
)
from blender_mcp._procurement import record_purchase
from blender_mcp._project import write_taste_profile


def _setup_project(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    return proj


def test_collect_bom_empty_when_no_data(tmp_path):
    proj = _setup_project(tmp_path)
    rows = collect_bom_rows(proj)
    assert rows == []


def test_collect_bom_includes_procurement_records(tmp_path):
    proj = _setup_project(tmp_path)
    record_purchase(proj, {
        "category": "sofa",
        "label": "Linen sectional",
        "url": "https://1688.com/x",
        "vendor": "1688",
        "price_rmb": 2400,
        "quantity": 1,
    })
    record_purchase(proj, {
        "category": "lamp",
        "label": "Brass pendant",
        "url": "https://taobao.com/x",
        "vendor": "taobao",
        "price_rmb": 380,
        "quantity": 2,
    })
    rows = collect_bom_rows(proj)
    assert len(rows) == 2
    assert any(r["label"] == "Linen sectional" for r in rows)
    assert any(r["label"] == "Brass pendant" for r in rows)


def test_collect_bom_includes_locked_material_vocab(tmp_path):
    proj = _setup_project(tmp_path)
    write_taste_profile(proj / "taste-profile.json", {
        "version": 1,
        "locked_material_vocab": {
            "in": ["light oak", "linen", "brushed brass"],
            "out": ["chrome", "glossy white"],
        },
    })
    rows = collect_bom_rows(proj)
    # Material-vocab rows should appear with category='finish'
    finishes = [r for r in rows if r["source"] == "taste_profile"]
    assert len(finishes) >= 3


def test_render_bom_markdown_includes_header_and_rows(tmp_path):
    proj = _setup_project(tmp_path)
    record_purchase(proj, {
        "category": "sofa", "label": "X", "url": "https://x",
        "vendor": "1688", "price_rmb": 100, "quantity": 1,
    })
    md = render_bom_markdown(collect_bom_rows(proj))
    assert "| Item " in md or "| Label " in md
    assert "X" in md
    assert "1688" in md or "￥" in md or "RMB" in md or "100" in md


def test_render_bom_csv_has_header(tmp_path):
    proj = _setup_project(tmp_path)
    record_purchase(proj, {
        "category": "sofa", "label": "X", "url": "https://x",
        "vendor": "1688", "price_rmb": 100, "quantity": 1,
    })
    csv = render_bom_csv(collect_bom_rows(proj))
    lines = csv.strip().splitlines()
    assert len(lines) >= 2  # header + 1 row
    assert "label" in lines[0].lower() or "item" in lines[0].lower()


def test_bom_summary_aggregates_total_cost(tmp_path):
    proj = _setup_project(tmp_path)
    record_purchase(proj, {
        "category": "sofa", "label": "A", "url": "https://x",
        "vendor": "1688", "price_rmb": 1000, "quantity": 2,
    })
    record_purchase(proj, {
        "category": "lamp", "label": "B", "url": "https://x",
        "vendor": "taobao", "price_rmb": 500, "quantity": 1,
    })
    summary = bom_summary(collect_bom_rows(proj))
    assert summary["total_cost_rmb"] == 2500.0  # 1000*2 + 500*1
    assert summary["item_count"] >= 2


def test_bom_summary_max_lead_time(tmp_path):
    proj = _setup_project(tmp_path)
    record_purchase(proj, {
        "category": "sofa", "label": "A", "url": "https://x",
        "vendor": "1688", "price_rmb": 100, "quantity": 1,
        "lead_time_days": 14,
    })
    record_purchase(proj, {
        "category": "lamp", "label": "B", "url": "https://x",
        "vendor": "taobao", "price_rmb": 50, "quantity": 1,
        "lead_time_days": 3,
    })
    summary = bom_summary(collect_bom_rows(proj))
    assert summary["max_lead_time_days"] == 14
