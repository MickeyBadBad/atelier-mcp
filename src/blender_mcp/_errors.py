"""Error formatter — pattern-matches exceptions to user-facing hints.

Filled out properly in Task 3."""
from __future__ import annotations
from typing import Any


def _format_error(tool_name: str, exc: Exception) -> dict:
    return {
        "code": "INTERNAL",
        "hint": "An internal error occurred. Re-run after addressing the detail below.",
        "detail": f"{type(exc).__name__}: {exc}",
    }
