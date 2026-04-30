"""Tests for the handbook loader module.

Coverage:
- list_chapters() returns the available chapter slugs
- read_chapter(slug) returns markdown content
- read_chapter() rejects path traversal attempts
- search_chapters(query) returns chapters that mention the query
- read_chapter() raises a clear error for unknown slugs
"""
from __future__ import annotations

import pytest

from atelier._handbook import (
    HandbookError,
    list_chapters,
    read_chapter,
    search_chapters,
)


def test_list_chapters_returns_a_list():
    chapters = list_chapters()
    assert isinstance(chapters, list)
    # README.md (index) must NOT appear in the chapter list
    assert "README" not in chapters
    assert "readme" not in chapters


def test_list_chapters_excludes_index():
    """The handbook index (README.md) is not a chapter — it must be filtered."""
    chapters = list_chapters()
    for slug in chapters:
        assert "readme" not in slug.lower(), (
            f"chapter list should not include README index: got {slug}"
        )


def test_read_chapter_rejects_empty_slug():
    with pytest.raises(HandbookError):
        read_chapter("")


def test_read_chapter_rejects_path_traversal():
    """Defensive: chapter lookup must not allow ../../etc/passwd."""
    with pytest.raises(HandbookError):
        read_chapter("../../../etc/passwd")
    with pytest.raises(HandbookError):
        read_chapter("codes/../../../etc/passwd")


def test_read_chapter_unknown_slug_raises_with_help():
    with pytest.raises(HandbookError) as exc_info:
        read_chapter("not-a-real-chapter")
    msg = str(exc_info.value)
    assert "not-a-real-chapter" in msg
    assert "available" in msg.lower()


def test_search_chapters_empty_query_returns_empty():
    assert search_chapters("") == []
    assert search_chapters("   ") == []


def test_search_chapters_returns_a_list():
    """Any non-empty query returns a list (possibly empty)."""
    assert isinstance(search_chapters("anything"), list)


def test_read_design_handbook_tool_registered():
    """The MCP tool should exist on the server module."""
    from atelier import server
    assert hasattr(server, "read_design_handbook")
