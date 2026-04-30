"""Tests for the procurement module."""
from __future__ import annotations

import pytest

from atelier._procurement import (
    PROCUREMENT_CATEGORIES,
    PROCUREMENT_VENDORS,
    ProcurementError,
    list_purchases,
    record_purchase,
    remove_purchase,
    validate_record,
)


def test_categories_canonical():
    expected = {
        "sofa", "chair", "table", "rug", "lamp",
        "art", "hardware", "finish", "appliance", "other",
    }
    assert set(PROCUREMENT_CATEGORIES) == expected


def test_vendors_includes_chinese_marketplaces():
    assert "1688" in PROCUREMENT_VENDORS
    assert "taobao" in PROCUREMENT_VENDORS
    assert "jd" in PROCUREMENT_VENDORS
    assert "sketchfab" in PROCUREMENT_VENDORS


def test_validate_record_fills_id_and_timestamp():
    rec = validate_record({
        "category": "sofa",
        "label": "Linen sectional",
        "url": "https://1688.com/item.html?id=12345",
        "vendor": "1688",
        "price_rmb": 2400,
        "quantity": 1,
    })
    assert "id" in rec
    assert len(rec["id"]) >= 6
    assert "added_at" in rec
    assert rec["category"] == "sofa"
    assert rec["price_rmb"] == 2400


def test_validate_record_rejects_unknown_category():
    with pytest.raises(ProcurementError):
        validate_record({
            "category": "spaceship",
            "label": "x",
            "url": "https://x",
            "vendor": "1688",
            "price_rmb": 1,
        })


def test_validate_record_rejects_unknown_vendor():
    with pytest.raises(ProcurementError):
        validate_record({
            "category": "sofa",
            "label": "x",
            "url": "https://x",
            "vendor": "alibaba_secret",
            "price_rmb": 1,
        })


def test_validate_record_rejects_missing_required_fields():
    with pytest.raises(ProcurementError):
        validate_record({"category": "sofa"})  # no label / url / vendor / price


def test_validate_record_rejects_negative_price():
    with pytest.raises(ProcurementError):
        validate_record({
            "category": "sofa", "label": "x", "url": "https://x",
            "vendor": "1688", "price_rmb": -10,
        })


def test_validate_record_quantity_defaults_to_one():
    rec = validate_record({
        "category": "sofa", "label": "x", "url": "https://x",
        "vendor": "1688", "price_rmb": 100,
    })
    assert rec["quantity"] == 1


def test_record_purchase_writes_to_procurement_json(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    sku_id = record_purchase(proj, {
        "category": "sofa",
        "label": "Linen sectional",
        "url": "https://1688.com/item.html?id=1",
        "vendor": "1688",
        "price_rmb": 2400,
    })
    assert sku_id is not None
    assert (proj / "procurement.json").is_file()


def test_list_purchases_empty_when_no_file(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    assert list_purchases(proj) == []


def test_list_purchases_returns_records_in_order(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    a = record_purchase(proj, {
        "category": "sofa", "label": "A", "url": "https://x/a",
        "vendor": "1688", "price_rmb": 100,
    })
    b = record_purchase(proj, {
        "category": "lamp", "label": "B", "url": "https://x/b",
        "vendor": "taobao", "price_rmb": 50,
    })
    items = list_purchases(proj)
    assert len(items) == 2
    assert {x["id"] for x in items} == {a, b}


def test_remove_purchase(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    sku_id = record_purchase(proj, {
        "category": "sofa", "label": "x", "url": "https://x",
        "vendor": "1688", "price_rmb": 100,
    })
    assert remove_purchase(proj, sku_id) is True
    assert remove_purchase(proj, sku_id) is False  # already gone
    assert list_purchases(proj) == []


def test_record_purchase_rejects_invalid_record(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    with pytest.raises(ProcurementError):
        record_purchase(proj, {"category": "spaceship"})
