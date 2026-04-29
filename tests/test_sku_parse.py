"""Tests for SKU metadata extraction."""
from __future__ import annotations

from blender_mcp._sku_parse import (
    detect_vendor,
    extract_image_url,
    extract_price_rmb,
    extract_quantity,
    extract_title,
    parse_sku_metadata,
)


def test_detect_vendor_1688():
    assert detect_vendor("https://detail.1688.com/offer/12345.html") == "1688"


def test_detect_vendor_taobao():
    assert detect_vendor("https://item.taobao.com/item.htm?id=99") == "taobao"


def test_detect_vendor_tmall():
    assert detect_vendor("https://detail.tmall.com/item.htm?id=99") == "tmall"


def test_detect_vendor_jd():
    assert detect_vendor("https://item.jd.com/100.html") == "jd"


def test_detect_vendor_sketchfab():
    assert detect_vendor("https://sketchfab.com/3d-models/foo") == "sketchfab"


def test_detect_vendor_unknown():
    assert detect_vendor("https://random-shop.example/x") == "other"


def test_extract_title_from_og():
    html = '<meta property="og:title" content="Linen Sectional Sofa" />'
    assert extract_title(html) == "Linen Sectional Sofa"


def test_extract_title_from_title_tag():
    html = "<html><title>Walnut Coffee Table — Vendor</title></html>"
    assert "Walnut Coffee Table" in extract_title(html)


def test_extract_title_from_plain_text():
    text = "Brushed Brass Pendant Lamp\n\nA classic mid-century fixture..."
    assert extract_title(text) == "Brushed Brass Pendant Lamp"


def test_extract_price_with_yuan_symbol():
    text = "全场特价 ¥1,299.00 包邮"
    assert extract_price_rmb(text) == 1299.0


def test_extract_price_with_yuan_word():
    text = "现价 380元 起"
    assert extract_price_rmb(text) == 380.0


def test_extract_price_with_cny():
    text = "Price: CNY 2400.50"
    assert extract_price_rmb(text) == 2400.5


def test_extract_price_with_jsonish():
    text = '{"price": "599.00", "stock": 42}'
    assert extract_price_rmb(text) == 599.0


def test_extract_price_returns_none_when_absent():
    assert extract_price_rmb("a description with no price anywhere") is None


def test_extract_quantity_default():
    assert extract_quantity("no count info here") == 1


def test_extract_image_url_from_og():
    html = '<meta property="og:image" content="https://cdn.example/x.jpg" />'
    assert extract_image_url(html) == "https://cdn.example/x.jpg"


def test_parse_sku_metadata_full_round_trip():
    url = "https://detail.1688.com/offer/12345.html"
    html = (
        '<html><head>'
        '<title>Walnut Side Table - Vendor</title>'
        '<meta property="og:title" content="Walnut Side Table 0.5m" />'
        '<meta property="og:image" content="https://cdn.1688.com/x.jpg" />'
        '</head><body>'
        '<div class="price">¥ 480.00</div>'
        '</body></html>'
    )
    rec = parse_sku_metadata(url, html, category_hint="table")
    assert rec["category"] == "table"
    assert rec["label"] == "Walnut Side Table 0.5m"
    assert rec["vendor"] == "1688"
    assert rec["price_rmb"] == 480.0
    assert rec["image_url"] == "https://cdn.1688.com/x.jpg"
    assert rec["url"] == url


def test_parse_sku_metadata_missing_fields_dont_crash():
    rec = parse_sku_metadata("https://item.taobao.com/x.htm", "minimal text")
    assert rec["vendor"] == "taobao"
    assert rec["price_rmb"] == 0.0
    assert rec["category"] == "other"
