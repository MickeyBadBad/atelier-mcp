"""Error formatter — pattern-matches exceptions to actionable hints.

Used by tool_envelope to turn raw exceptions into the {code, hint, detail}
shape consumers can branch on."""
from __future__ import annotations
import socket


def _format_error(tool_name: str, exc: Exception) -> dict:
    detail = f"{type(exc).__name__}: {exc}"
    msg = str(exc).lower()

    # Socket / connection
    if isinstance(exc, ConnectionRefusedError) or "connection refused" in msg:
        return {
            "code": "STATE_REQUIRED",
            "hint": "Blender addon not connected. In Blender: press N → BlenderMCP → click Connect to Claude.",
            "detail": detail,
        }
    if isinstance(exc, (socket.timeout, TimeoutError)) or "timed out" in msg or "timeout" in msg:
        return {
            "code": "NETWORK",
            "hint": "Blender is busy or unresponsive — try again in 10s, or restart the addon.",
            "detail": detail,
        }
    if isinstance(exc, (ConnectionError, BrokenPipeError, ConnectionResetError)):
        return {
            "code": "NETWORK",
            "hint": "Connection to Blender lost. Reconnect via N panel → BlenderMCP → Connect to Claude.",
            "detail": detail,
        }

    # Auth / API key
    if isinstance(exc, KeyError) and "key" in str(exc).lower():
        return {
            "code": "NO_API_KEY",
            "hint": f"{tool_name} needs an API key. Run check_services for setup links.",
            "detail": detail,
        }
    if "401" in msg or "unauthorized" in msg or "authentication failed" in msg:
        return {
            "code": "NO_API_KEY",
            "hint": "API auth failed. Check the relevant *_api_key in Blender addon prefs or env.",
            "detail": detail,
        }

    # Rate limits
    if "429" in msg or "rate limit" in msg or "too many requests" in msg:
        return {
            "code": "RATE_LIMITED",
            "hint": "Provider rate-limited the request. Back off 30-60s or upgrade tier.",
            "detail": detail,
        }

    # Bad input
    if isinstance(exc, (ValueError, TypeError)):
        return {
            "code": "BAD_INPUT",
            "hint": f"Bad parameter to {tool_name}. See detail for the offending value.",
            "detail": detail,
        }

    # File / asset not found
    if isinstance(exc, FileNotFoundError):
        return {
            "code": "NOT_FOUND",
            "hint": "A required file/asset was not found. Verify path or call the relevant download_* tool first.",
            "detail": detail,
        }

    return {
        "code": "INTERNAL",
        "hint": "An internal error occurred. Re-run after addressing the detail.",
        "detail": detail,
    }
