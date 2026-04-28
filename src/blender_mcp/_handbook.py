"""Pure-Python handbook loader.

The handbook lives at <repo-root>/docs/handbook/ as plain markdown.
This module exposes:

- list_chapters() -> list of chapter slugs (e.g. "codes", "styles/scandinavian")
- read_chapter(slug) -> raw markdown content
- search_chapters(query) -> chapters whose body contains the query

No Blender or MCP dependencies — pure Python so unit tests run fast.
Path-traversal-safe: chapter slugs are validated against the discovered
chapter list before any filesystem access.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any


class HandbookError(Exception):
    """Raised on chapter-not-found, traversal, or read errors."""


_HANDBOOK_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "handbook"


def _handbook_root() -> Path:
    """Return the absolute handbook directory, raising if missing."""
    if not _HANDBOOK_DIR.is_dir():
        raise HandbookError(
            f"Handbook directory not found at {_HANDBOOK_DIR}. "
            "Run from repo root and ensure docs/handbook/ exists."
        )
    return _HANDBOOK_DIR


def list_chapters() -> List[str]:
    """Return the list of available chapter slugs.

    A slug is the path under docs/handbook/ without the .md suffix.
    Examples: "codes", "lighting", "styles/scandinavian".
    The README.md is excluded (it's the index, not a chapter).
    """
    root = _handbook_root()
    slugs: List[str] = []
    for md in root.rglob("*.md"):
        rel = md.relative_to(root)
        if rel.name.lower() == "readme.md":
            continue
        slug = str(rel.with_suffix(""))
        # POSIX-style slug for cross-platform consistency
        slug = slug.replace("\\", "/")
        slugs.append(slug)
    return sorted(slugs)


def _resolve_chapter_path(slug: str) -> Path:
    """Resolve slug → file path, rejecting traversal."""
    slug = (slug or "").strip()
    if not slug:
        raise HandbookError("chapter slug must not be empty")

    available = list_chapters()
    if slug not in available:
        raise HandbookError(
            f"chapter '{slug}' not found. available chapters: "
            f"{', '.join(available) if available else '(none yet)'}"
        )

    root = _handbook_root().resolve()
    candidate = (root / f"{slug}.md").resolve()
    # Defensive: ensure the resolved path is still inside the handbook root.
    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise HandbookError(
            f"chapter slug '{slug}' resolves outside handbook root"
        ) from e
    return candidate


def read_chapter(slug: str) -> str:
    """Return the markdown content of a chapter."""
    path = _resolve_chapter_path(slug)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        raise HandbookError(f"failed to read chapter '{slug}': {e}") from e


def search_chapters(query: str) -> List[Dict[str, Any]]:
    """Return chapters whose body contains the query (case-insensitive).

    Returns a list of dicts: {"chapter": slug, "matches": int, "preview": str}
    sorted by match count descending. Empty/whitespace query returns [].
    """
    query = (query or "").strip()
    if not query:
        return []

    needle = query.lower()
    results: List[Dict[str, Any]] = []
    for slug in list_chapters():
        try:
            body = read_chapter(slug).lower()
        except HandbookError:
            continue
        count = body.count(needle)
        if count == 0:
            continue
        # Find a small preview around the first match
        idx = body.find(needle)
        start = max(0, idx - 60)
        end = min(len(body), idx + 60 + len(needle))
        preview = body[start:end].replace("\n", " ").strip()
        results.append({
            "chapter": slug,
            "matches": count,
            "preview": preview,
        })

    results.sort(key=lambda r: r["matches"], reverse=True)
    return results
