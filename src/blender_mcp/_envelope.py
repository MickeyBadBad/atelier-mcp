"""Tool response envelope: every @mcp.tool() returns this exact shape.

Envelope:
  ok=True  -> {"ok": true, "data": <any json-serializable>}
  ok=False -> {"ok": false, "error": {"code": str, "hint": str, "detail": str}}

LLM clients branch on `ok` and on `error.code` for retry/recovery logic.
"""
from __future__ import annotations
import enum
import functools
import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("BlenderMCPServer")


class ErrorCode(str, enum.Enum):
    NO_API_KEY = "NO_API_KEY"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK = "NETWORK"
    BAD_INPUT = "BAD_INPUT"
    STATE_REQUIRED = "STATE_REQUIRED"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL = "INTERNAL"


class ToolError(Exception):
    """Raise from inside a @tool_envelope-wrapped tool to surface a
    structured error to the LLM. Catches uniformly through the decorator."""

    def __init__(self, code: ErrorCode, hint: str = "", detail: str = ""):
        super().__init__(f"{code.value}: {hint or detail}")
        self.code = code
        self.hint = hint
        self.detail = detail


def _tool_response(
    ok: bool,
    data: Any = None,
    error: Optional[dict] = None,
) -> str:
    """Serialize the canonical envelope. Always returns a JSON string,
    suitable for direct return from a @mcp.tool() function."""
    if ok:
        return json.dumps({"ok": True, "data": data}, default=str)
    err = error or {}
    code = err.get("code")
    if hasattr(code, "value"):
        code = code.value
    return json.dumps(
        {
            "ok": False,
            "error": {
                "code": code or ErrorCode.INTERNAL.value,
                "hint": err.get("hint", ""),
                "detail": err.get("detail", ""),
            },
        },
        default=str,
    )


def tool_envelope(fn: Callable) -> Callable:
    """Decorator: wraps a @mcp.tool function so its return is normalized.

    - Returns of type `str` that are already JSON envelopes are passed through.
    - Returns of any other JSON-serializable type are wrapped as ok=True.
    - ToolError -> ok=False with structured error.
    - Other exceptions -> ok=False, code=INTERNAL, hint=str(exc).
    """
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
        except ToolError as e:
            logger.info(f"{fn.__name__} returned ToolError: {e.code.value}: {e.hint}")
            return _tool_response(
                ok=False,
                error={"code": e.code, "hint": e.hint, "detail": e.detail},
            )
        except Exception as e:
            logger.exception(f"{fn.__name__} crashed")
            from ._errors import _format_error
            return _tool_response(
                ok=False,
                error=_format_error(fn.__name__, e),
            )
        # Already-an-envelope passthrough: parse to confirm shape, else wrap.
        # Require ok to be a real bool AND the matching companion key to be
        # present, so we don't silently pass through fake-looking JSON strings
        # that happen to have a top-level "ok" key for unrelated reasons.
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict) and isinstance(parsed.get("ok"), bool):
                    if parsed["ok"] and "data" in parsed:
                        return result
                    if not parsed["ok"] and "error" in parsed:
                        return result
            except json.JSONDecodeError:
                pass
            return _tool_response(ok=True, data=result)
        return _tool_response(ok=True, data=result)
    return wrapped
