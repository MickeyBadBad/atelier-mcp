"""Pure-Python Bill-of-Materials (BoM) aggregator.

Combines `procurement.json` SKU records and `taste-profile.json`
locked-material vocab into one canonical row list, then renders as
markdown or CSV for contractor handoff.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Dict, List

from ._procurement import list_purchases
from ._project import ProjectError, read_taste_profile


# Canonical BoM row schema:
# {
#   "source": "procurement" | "taste_profile",
#   "category": str,
#   "label": str,
#   "vendor": str,
#   "url": str,
#   "quantity": int,
#   "unit_price_rmb": float,
#   "subtotal_rmb": float,
#   "lead_time_days": int,
#   "notes": str,
# }


def collect_bom_rows(project_root: Path) -> List[Dict[str, Any]]:
    """Aggregate procurement records + taste-profile material vocab."""
    project_root = Path(project_root)
    rows: List[Dict[str, Any]] = []

    # 1) Procurement records
    for rec in list_purchases(project_root):
        unit = float(rec.get("price_rmb", 0))
        qty = int(rec.get("quantity", 1))
        rows.append({
            "source": "procurement",
            "category": rec.get("category", "other"),
            "label": rec.get("label", ""),
            "vendor": rec.get("vendor", ""),
            "url": rec.get("url", ""),
            "quantity": qty,
            "unit_price_rmb": unit,
            "subtotal_rmb": unit * qty,
            "lead_time_days": int(rec.get("lead_time_days", 0)),
            "notes": rec.get("notes", ""),
        })

    # 2) Taste-profile locked material vocab
    profile_path = project_root / "taste-profile.json"
    if profile_path.is_file():
        try:
            profile = read_taste_profile(profile_path)
        except ProjectError:
            profile = {}
        vocab = profile.get("locked_material_vocab", {})
        for item in vocab.get("in", []) or []:
            rows.append({
                "source": "taste_profile",
                "category": "finish",
                "label": str(item),
                "vendor": "",
                "url": "",
                "quantity": 0,
                "unit_price_rmb": 0.0,
                "subtotal_rmb": 0.0,
                "lead_time_days": 0,
                "notes": "from locked palette (taste-profile.locked_material_vocab.in)",
            })

    return rows


def render_bom_markdown(rows: List[Dict[str, Any]]) -> str:
    """Render BoM rows as a markdown table grouped by category."""
    if not rows:
        return "_(BoM is empty — no procurement records or locked materials)_"

    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_category.setdefault(row["category"], []).append(row)

    out: List[str] = []
    out.append("# Bill of Materials")
    out.append("")
    grand_total = sum(r.get("subtotal_rmb", 0) for r in rows)
    grand_qty = sum(r.get("quantity", 0) for r in rows if r.get("quantity"))
    out.append(
        f"**{len(rows)} item(s)** · "
        f"**{grand_qty} unit(s) priced** · "
        f"**¥{grand_total:,.2f}** total"
    )
    out.append("")

    for category in sorted(by_category.keys()):
        out.append(f"## {category.title()}")
        out.append("")
        out.append(
            "| Label | Vendor | Qty | Unit (RMB) | Subtotal (RMB) | Lead (d) | URL |"
        )
        out.append(
            "|---|---|---:|---:|---:|---:|---|"
        )
        cat_rows = by_category[category]
        for r in cat_rows:
            url = r.get("url", "")
            url_md = f"[link]({url})" if url else "—"
            out.append(
                f"| {r.get('label', '')} "
                f"| {r.get('vendor', '') or '—'} "
                f"| {r.get('quantity', 0)} "
                f"| {r.get('unit_price_rmb', 0):,.2f} "
                f"| {r.get('subtotal_rmb', 0):,.2f} "
                f"| {r.get('lead_time_days', 0)} "
                f"| {url_md} |"
            )
        out.append("")
    return "\n".join(out)


def render_bom_csv(rows: List[Dict[str, Any]]) -> str:
    """Render BoM rows as CSV (UTF-8, with header)."""
    fieldnames = (
        "source", "category", "label", "vendor", "url",
        "quantity", "unit_price_rmb", "subtotal_rmb",
        "lead_time_days", "notes",
    )
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return buf.getvalue()


def bom_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """High-level summary for the AI to surface to the user."""
    total_cost = sum(r.get("subtotal_rmb", 0) for r in rows)
    max_lead = max(
        (r.get("lead_time_days", 0) for r in rows),
        default=0,
    )
    item_count = len(rows)
    by_category: Dict[str, int] = {}
    for r in rows:
        cat = r.get("category", "other")
        by_category[cat] = by_category.get(cat, 0) + 1
    return {
        "item_count": item_count,
        "total_cost_rmb": round(total_cost, 2),
        "max_lead_time_days": max_lead,
        "by_category": by_category,
    }
