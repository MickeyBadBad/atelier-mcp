"""Pure-Python procurement (SKU shopping list) module.

Per the workflow spec § Slice 4, the project keeps a `procurement.json`
sidecar listing every SKU the user / AI has linked to the design.
Records are append-mostly; the user can remove items by id.

The MCP tool layer (in server.py) wraps these functions; this module
stays pure-Python so unit tests run without Blender or network.
"""
from __future__ import annotations

import datetime
import json
import secrets
from pathlib import Path
from typing import Any, Dict, List


class ProcurementError(Exception):
    """Raised on invalid record schema or I/O failures."""


# Canonical categories for SKU classification.
PROCUREMENT_CATEGORIES = (
    "sofa", "chair", "table", "rug", "lamp",
    "art", "hardware", "finish", "appliance", "other",
)


# Vendor whitelist. Chinese marketplaces are explicit; international ones
# are namespaced.
PROCUREMENT_VENDORS = (
    # Chinese marketplaces
    "1688", "taobao", "tmall", "jd", "xiaohongshu",
    # 3D / asset stores
    "sketchfab", "polyhaven", "ambientcg", "tripo3d",
    # Specialty
    "ikea", "muji", "vipp",
    # Misc
    "manufacturer", "showroom", "other",
)


REQUIRED_FIELDS = ("category", "label", "url", "vendor", "price_rmb")


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _new_id() -> str:
    return secrets.token_urlsafe(6)


def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a SKU record. Returns a copy with id + timestamp."""
    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        raise ProcurementError(
            f"missing required fields: {missing}. required: "
            f"{list(REQUIRED_FIELDS)}"
        )

    category = record.get("category")
    if category not in PROCUREMENT_CATEGORIES:
        raise ProcurementError(
            f"unknown category '{category}'. valid: "
            f"{list(PROCUREMENT_CATEGORIES)}"
        )

    vendor = record.get("vendor")
    if vendor not in PROCUREMENT_VENDORS:
        raise ProcurementError(
            f"unknown vendor '{vendor}'. valid: {list(PROCUREMENT_VENDORS)}"
        )

    price = record.get("price_rmb")
    if not isinstance(price, (int, float)) or price < 0:
        raise ProcurementError(
            f"price_rmb must be a non-negative number, got: {price!r}"
        )

    label = str(record.get("label", "")).strip()
    if not label:
        raise ProcurementError("label must not be empty")

    url = str(record.get("url", "")).strip()
    if not url:
        raise ProcurementError("url must not be empty")

    quantity = record.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1:
        raise ProcurementError(
            f"quantity must be a positive int, got: {quantity!r}"
        )

    out = {
        "id": record.get("id") or _new_id(),
        "category": category,
        "label": label,
        "url": url,
        "vendor": vendor,
        "price_rmb": float(price),
        "quantity": int(quantity),
        "lead_time_days": int(record.get("lead_time_days", 0)),
        "image_url": str(record.get("image_url", "")).strip(),
        "notes": str(record.get("notes", "")).strip(),
        "linked_object": str(record.get("linked_object", "")).strip(),
        "added_at": record.get("added_at") or _utc_now_iso(),
    }
    return out


def _procurement_path(project_root: Path) -> Path:
    return Path(project_root) / "procurement.json"


def _read_records(project_root: Path) -> List[Dict[str, Any]]:
    path = _procurement_path(project_root)
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ProcurementError(f"corrupt procurement.json: {e}") from e


def _write_records(
    project_root: Path,
    records: List[Dict[str, Any]],
) -> None:
    path = _procurement_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def record_purchase(project_root: Path, record: Dict[str, Any]) -> str:
    """Validate + append a new SKU record. Returns the assigned id."""
    project_root = Path(project_root)
    if not project_root.is_dir():
        raise ProcurementError(
            f"project_root not a directory: {project_root}"
        )
    normalized = validate_record(record)
    records = _read_records(project_root)
    records.append(normalized)
    _write_records(project_root, records)
    return normalized["id"]


def list_purchases(project_root: Path) -> List[Dict[str, Any]]:
    """Return all SKU records in the order they were added."""
    return _read_records(Path(project_root))


def remove_purchase(project_root: Path, sku_id: str) -> bool:
    """Remove the SKU with the given id. Returns True if removed."""
    project_root = Path(project_root)
    records = _read_records(project_root)
    new_records = [r for r in records if r.get("id") != sku_id]
    if len(new_records) == len(records):
        return False
    _write_records(project_root, new_records)
    return True
