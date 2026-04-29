"""Best-effort SKU metadata extractor for pasted e-commerce HTML / text.

The AI client uses claude-in-chrome (or asks the user to paste) to
fetch the product page content; this module parses it. Coverage is
heuristic — Chinese marketplace anti-scraping makes a deterministic
parser impossible, so we extract what we can.

Returns a `dict` matching the procurement.validate_record() schema as
closely as possible. Fields the parser couldn't find are left empty
and the caller can prompt the user to fill them.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse


# Vendor detection from URL host patterns
_VENDOR_HOST_PATTERNS = [
    (r"(?:^|\.)1688\.com$", "1688"),
    (r"(?:^|\.)taobao\.com$", "taobao"),
    (r"(?:^|\.)tmall\.com$", "tmall"),
    (r"(?:^|\.)tmall\.hk$", "tmall"),
    (r"(?:^|\.)jd\.com$", "jd"),
    (r"(?:^|\.)jd\.hk$", "jd"),
    (r"(?:^|\.)xiaohongshu\.com$", "xiaohongshu"),
    (r"(?:^|\.)xhscdn\.com$", "xiaohongshu"),
    (r"(?:^|\.)sketchfab\.com$", "sketchfab"),
    (r"(?:^|\.)polyhaven\.com$", "polyhaven"),
    (r"(?:^|\.)ambientcg\.com$", "ambientcg"),
    (r"(?:^|\.)tripo3d\.ai$", "tripo3d"),
    (r"(?:^|\.)ikea\.com(?:\.[a-z]+)?$", "ikea"),
    (r"(?:^|\.)muji\.com$", "muji"),
    (r"(?:^|\.)muji\.[a-z]+$", "muji"),
    (r"(?:^|\.)vipp\.com$", "vipp"),
]


def detect_vendor(url: str) -> str:
    """Return the vendor slug for a given URL (or 'other')."""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return "other"
    for pattern, vendor in _VENDOR_HOST_PATTERNS:
        if re.search(pattern, host):
            return vendor
    return "other"


# Generic title extractors (works for most pages with <title>)
_TITLE_RE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE | re.DOTALL)
_OG_TITLE_RE = re.compile(
    r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_IMAGE_RE = re.compile(
    r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def extract_title(html_or_text: str) -> str:
    """Extract a product title from HTML (og:title preferred) or text."""
    m = _OG_TITLE_RE.search(html_or_text)
    if m:
        return _strip_tags(m.group(1)).strip()
    m = _TITLE_RE.search(html_or_text)
    if m:
        return _strip_tags(m.group(1)).strip()
    # Plain text — first non-empty line
    for line in html_or_text.splitlines():
        line = line.strip()
        if line and len(line) < 200:
            return line
    return ""


def extract_image_url(html_or_text: str) -> str:
    """Best-effort thumbnail URL extraction (og:image)."""
    m = _OG_IMAGE_RE.search(html_or_text)
    return m.group(1).strip() if m else ""


# Price patterns. Chinese marketplaces use ¥ / RMB / 元 / CNY.
_PRICE_PATTERNS = [
    # ¥ 1234.56 / ￥ 1,234.56
    re.compile(r"[¥￥]\s*([\d,]+(?:\.\d{1,2})?)"),
    # 1234.56 元 / 1234元
    re.compile(r"([\d,]+(?:\.\d{1,2})?)\s*元(?:\b|$)"),
    # CNY 1234.56
    re.compile(r"\bCNY\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE),
    # 价格: 1234.56
    re.compile(r"价格[\s:：]*([\d,]+(?:\.\d{1,2})?)"),
    # "price": 1234.56  (JSON-ish)
    re.compile(r'"price"\s*:\s*"?([\d,]+(?:\.\d{1,2})?)"?'),
]


def extract_price_rmb(html_or_text: str) -> Optional[float]:
    """Extract a price in RMB. Returns None if no plausible price found."""
    for pattern in _PRICE_PATTERNS:
        for match in pattern.finditer(html_or_text):
            raw = match.group(1).replace(",", "")
            try:
                value = float(raw)
                if 0 < value < 10_000_000:  # plausibility bounds
                    return value
            except ValueError:
                continue
    return None


# Quantity / pack-size patterns (e.g. "x2 件" / "包装：1件")
_QUANTITY_RE = re.compile(
    r"(?:数量|件数|x|×)\s*[:：]?\s*(\d{1,3})", re.IGNORECASE,
)


def extract_quantity(html_or_text: str) -> int:
    """Extract a default quantity. Returns 1 if none found or implausible."""
    m = _QUANTITY_RE.search(html_or_text)
    if not m:
        return 1
    try:
        n = int(m.group(1))
        return n if 1 <= n <= 1000 else 1
    except ValueError:
        return 1


def parse_sku_metadata(
    url: str,
    html_or_text: str,
    category_hint: str = "other",
) -> Dict[str, Any]:
    """Parse pasted page content into a procurement-shape draft record.

    The AI / user must still review and fill missing fields before
    calling record_purchase. category_hint defaults to 'other' since
    we can't reliably classify products from page text.
    """
    return {
        "category": category_hint,
        "label": extract_title(html_or_text) or "(title not detected — fill in)",
        "url": url,
        "vendor": detect_vendor(url),
        "price_rmb": extract_price_rmb(html_or_text) or 0.0,
        "quantity": extract_quantity(html_or_text),
        "image_url": extract_image_url(html_or_text),
        "notes": "auto-extracted; please verify before recording",
    }
