# Interior Design Workflow — Slice 4: Construction Handoff Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans. Steps use `- [ ]`.

**Goal:** Add procurement + BoM (Bill of Materials) infrastructure so the AI can produce a contractor-ready shopping list. Defers PDF dimensioned drawings (still pending — needs Blender addon work; addressed in a later slice).

**Architecture:** Two new pure-Python modules — `_procurement.py` (SKU records, list management) and `_bom.py` (collect material metadata from `taste-profile.locked_material_vocab` + procurement records, render markdown/CSV). One new MCP tool to parse SKU metadata from raw HTML / text (`extract_sku_metadata`), four to manage procurement.

**Tech Stack:** Python stdlib + pyyaml. No new external deps. SKU URL fetching is delegated to caller (claude-in-chrome MCP or manual paste) — this slice handles the parsing of pasted page content, not the fetching.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/blender_mcp/_procurement.py` | Procurement record validation, JSON I/O for `procurement.json` |
| `src/blender_mcp/_bom.py` | BoM aggregator: combine procurement + finish-vocab → markdown/CSV |
| `src/blender_mcp/server.py` | 5 new MCP tools: `record_sku_purchase`, `list_procurement`, `remove_sku_purchase`, `extract_sku_metadata`, `generate_bom` |
| `tests/test_procurement.py` | Tests for procurement schema + I/O |
| `tests/test_bom.py` | Tests for BoM aggregation |

---

## Task 1: `_procurement.py` Module

Schema for one SKU record:

```python
{
  "id": "auto-generated short id",
  "category": "sofa | chair | table | rug | lamp | art | hardware | finish | other",
  "label": "human-readable name",
  "url": "1688/淘宝/京东 product URL",
  "vendor": "1688 | taobao | jd | sketchfab | polyhaven | other",
  "price_rmb": 2400,
  "quantity": 1,
  "lead_time_days": 7,
  "image_url": "thumbnail URL",
  "notes": "freeform",
  "linked_object": "optional Blender object name",
  "added_at": "ISO timestamp"
}
```

Functions:
- `record_purchase(project_root, record_dict) -> id`
- `list_purchases(project_root) -> list[record]`
- `remove_purchase(project_root, sku_id) -> bool`
- `validate_record(record_dict) -> normalized_dict`

## Task 2: `_bom.py` Module

Functions:
- `collect_bom_rows(project_root) -> list[row]` — combines:
  - procurement.json records (SKUs, quantities, prices)
  - taste-profile `locked_material_vocab` (in/out lists)
  - if scene_info passed: object→finish mapping from finishes
- `render_bom_markdown(rows) -> str` — formatted markdown table
- `render_bom_csv(rows) -> str` — CSV
- `bom_summary(rows) -> dict` — total cost, lead time max, item count

## Task 3: `extract_sku_metadata` MCP Tool

Parses pasted HTML / text from a 1688 / 淘宝 / 京东 / Sketchfab / Polyhaven product page. Doesn't fetch — caller provides the content. Uses simple heuristics + regex over typical e-commerce page structures (no full DOM parser dependency).

## Task 4: Procurement MCP Tools

Standard pattern: validate input, call _procurement function, return envelope.

## Task 5: Tests + push

Run full suite. Push to fork.
