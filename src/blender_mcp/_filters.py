"""Response-shape filters for verbose third-party APIs.

Sketchfab and PolyHaven return JSON with many fields the LLM never uses
(four thumbnail sizes, archive metadata for formats we don't import,
GPS coordinates, sponsor IDs, file hashes, etc.). Slimming each result
to a stable 5-9 field summary cuts typical search response by ~70%.

The slimmers are pure functions: no I/O, no Blender deps. Each accepts
the raw dict the addon-side handler returned and emits the slim shape.
If the input looks like an error envelope (`{"error": "..."}`) it
passes through unchanged so the envelope decorator can still classify.
"""
from __future__ import annotations
from typing import Any


def _largest_thumb_url(thumbs: dict | None) -> str | None:
    """Pick the largest-width image URL from a Sketchfab thumbnails
    block. Sketchfab returns 4 sizes; we keep one."""
    if not thumbs:
        return None
    images = thumbs.get("images", []) if isinstance(thumbs, dict) else []
    if not images:
        return None
    chosen = max(images, key=lambda im: im.get("width", 0))
    return chosen.get("url")


def slim_sketchfab(raw: dict) -> dict:
    """Trim a Sketchfab /v3/search response.

    Keeps: results[].{uid, name, face_count, vertex_count, license,
    downloadable, view_count, like_count, category, thumb_url, author,
    description (first 200 chars), created_at}
    Drops: thumbnails (4 sizes), archives (4 formats), user avatar,
    tags array, embed_url, viewer_url, uri, files_hash, sponsors,
    backplates, etc.
    """
    if not isinstance(raw, dict) or raw.get("error"):
        return raw
    results = raw.get("results")
    if results is None:
        return raw

    out_results = []
    for r in results:
        if not isinstance(r, dict):
            continue
        # First category if any
        cats = r.get("categories") or []
        cat_name = cats[0].get("name") if cats and isinstance(cats[0], dict) else None
        # License label
        lic = r.get("license") or {}
        lic_label = lic.get("label") if isinstance(lic, dict) else None
        # User
        user = r.get("user") or {}
        author = user.get("displayName") or user.get("username") if isinstance(user, dict) else None
        # Description capped
        desc = r.get("description") or ""
        if isinstance(desc, str) and len(desc) > 200:
            desc = desc[:200] + "..."

        out_results.append({
            "uid": r.get("uid"),
            "name": r.get("name"),
            "face_count": r.get("faceCount"),
            "vertex_count": r.get("vertexCount"),
            "license": lic_label,
            "downloadable": r.get("isDownloadable"),
            "view_count": r.get("viewCount"),
            "like_count": r.get("likeCount"),
            "category": cat_name,
            "thumb_url": _largest_thumb_url(r.get("thumbnails")),
            "author": author,
            "description": desc or None,
            "created_at": r.get("createdAt"),
        })

    slim = {"results": out_results}
    if "cursors" in raw:
        slim["cursors"] = raw["cursors"]
    return slim


def slim_polyhaven(raw: dict) -> dict:
    """Trim a PolyHaven /assets response.

    Keeps: assets[id].{name, categories, tags, max_resolution,
    download_count, thumb_url, description (cap 200)}
    Drops: evs_cap, whitebalance, files_hash, sponsors, coords,
    authors detail, date_taken, date_published, type, backplates,
    info, donated, similarity (sort score).
    """
    if not isinstance(raw, dict) or raw.get("error"):
        return raw
    assets = raw.get("assets")
    if assets is None:
        return raw

    out_assets = {}
    for asset_id, a in assets.items():
        if not isinstance(a, dict):
            continue
        max_res = a.get("max_resolution")
        if isinstance(max_res, list) and len(max_res) == 2:
            res_str = f"{max_res[0]}x{max_res[1]}"
        else:
            res_str = None
        desc = a.get("description") or ""
        if isinstance(desc, str) and len(desc) > 200:
            desc = desc[:200] + "..."
        out_assets[asset_id] = {
            "name": a.get("name"),
            "categories": a.get("categories"),
            "tags": a.get("tags"),
            "max_resolution": res_str,
            "download_count": a.get("download_count"),
            "thumb_url": a.get("thumbnail_url"),
            "description": desc or None,
        }

    out = {"assets": out_assets}
    for k in ("total_count", "returned_count"):
        if k in raw:
            out[k] = raw[k]
    return out
