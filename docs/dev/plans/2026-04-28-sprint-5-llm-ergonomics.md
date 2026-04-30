# Sprint 5 — LLM Ergonomics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship blender-mcp v2.0.0+fork.1 — every tool returns a unified `{ok, data?, error?}` envelope, naming becomes consistent (`<verb>_<provider>_<object>` for provider-bound tools), smart router actually works for all four AI 3D providers, OpenAI integration generalizes to any OpenAI-compatible endpoint, and telemetry defaults to opt-in.

**Architecture:** Introduce a `_tool_response()` helper + `@tool_envelope` decorator at the top of `src/blender_mcp/server.py`. Every existing `@mcp.tool()` gets wrapped; legacy `Error: ...` string returns and naked dict returns disappear in one mass migration. A minimal `SERVICE_REGISTRY` dict (`addon.py` top) backs the decorator's metadata and seeds Sprint 10's full registry refactor. Mass renames use a single mechanical pass; no aliases (BC-break decision B).

**Tech Stack:** Python 3.10+, `bpy` (Blender 4.x/5.x), `mcp[cli]`, `pytest` (new dev dep), GitHub Actions CI.

**Working tree:** `/Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp/` on branch `develop`. Sprint 5 work happens on a new feature branch `sprint-5-ergonomics`.

---

## File Structure

| File | Disposition | Responsibility |
|---|---|---|
| `src/blender_mcp/_envelope.py` | **Create** (~80 lines) | `_tool_response()` factory + `tool_envelope` decorator + `ToolError` exception + error-code enum |
| `src/blender_mcp/_errors.py` | **Create** (~60 lines) | `_format_error(exc)` pattern-matcher: socket / connection / API / state / input → user-facing hint |
| `src/blender_mcp/server.py` | **Modify heavily** | Apply `@tool_envelope` to all 56 tools; rewrite return statements to use envelope helpers; rename ~8 tools per spec |
| `addon.py` | **Modify (top + dispatcher + several methods)** | Add `SERVICE_REGISTRY` dict near top; rename dispatcher entries to match new tool names; flip `telemetry_consent` default; refactor `generate_image_openai` to use `openai_base_url`; smart-router fixes |
| `tests/` | **Create dir** | New test scaffold |
| `tests/__init__.py` | **Create** | Empty marker |
| `tests/conftest.py` | **Create** (~30 lines) | Shared pytest fixtures (mock socket, fake Blender connection) |
| `tests/test_envelope.py` | **Create** (~80 lines) | Unit tests for `_tool_response`, `tool_envelope` decorator, `_format_error` |
| `tests/test_naming.py` | **Create** (~40 lines) | Grep-style regression test: zero stale-name usages |
| `tests/test_smart_router.py` | **Create** (~100 lines) | Mock provider stubs; assert routing matrix |
| `tests/test_openai_compat.py` | **Create** (~60 lines) | Mock `requests.post` to verify base_url respected |
| `pyproject.toml` | **Modify** | Add pytest as dev dep; bump version 1.10.2 → 2.0.0 |
| `CHANGELOG.md` | **Modify** | New `## [2.0.0+fork.1]` section with breaking-changes list |
| `README.md` | **Modify** | Update Tools reference table to new names; add migration cheat sheet box |
| `CLAUDE.md` (project root) | **Modify** | Add migration cheat sheet section so next AI session adapts to v2 names |
| `AGENTS.md` (fork root) | **Create** (~80 lines) | Conventions for AI agents working on the fork (envelope rule, naming rule, dispatcher pattern) — same content the spec calls "Sprint 6 deliverable" but lighter version useful now to prevent regressions during this sprint |

The bulky `addon.py` and `server.py` stay single-file in this sprint. Splitting into modules is Sprint 10. The `SERVICE_REGISTRY` introduced here is designed as the seed: same Service dataclass, same field names, just minimal coverage.

---

## Task 1: Branch + test scaffold + pytest setup

**Files:**
- Create: `tests/__init__.py`, `tests/conftest.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create feature branch**

```bash
cd /Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp
git checkout develop
git pull
git checkout -b sprint-5-ergonomics
```

- [ ] **Step 2: Add pytest to pyproject dev dependencies**

In `pyproject.toml`, after the existing `[project.dependencies]` block, add:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-mock>=3.12.0",
]
```

Bump version while we're here: `version = "2.0.0+fork.1"` (was `1.10.2+fork.1`).

- [ ] **Step 3: Create empty test package**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 4: Write conftest.py with mock-socket fixture**

`tests/conftest.py`:

```python
"""Shared pytest fixtures for blender-mcp tests.

Mocks the socket layer so we can test server.py tool wrappers without a
running Blender instance.
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_blender_connection(monkeypatch):
    """Replace get_blender_connection() with a fake that returns whatever
    we set via .send_command.return_value."""
    fake = MagicMock()
    fake.send_command = MagicMock(return_value={"some": "result"})
    from blender_mcp import server
    monkeypatch.setattr(server, "get_blender_connection", lambda: fake)
    return fake
```

- [ ] **Step 5: Verify pytest collects the empty suite**

Run: `cd /Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp && uv sync && uv run pytest --collect-only`

Expected: `0 tests collected`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml tests/__init__.py tests/conftest.py
git commit -m "chore: add pytest scaffold and bump to v2.0.0-fork.1"
```

---

## Task 2: `_tool_response()` + `ToolError` + error-code enum

**Files:**
- Create: `src/blender_mcp/_envelope.py`
- Create: `tests/test_envelope.py`

- [ ] **Step 1: Write the failing test first**

`tests/test_envelope.py`:

```python
"""Unit tests for the tool envelope helpers."""
import json
from blender_mcp._envelope import (
    ErrorCode,
    ToolError,
    _tool_response,
    tool_envelope,
)


def test_tool_response_ok():
    out = _tool_response(ok=True, data={"x": 1})
    assert json.loads(out) == {"ok": True, "data": {"x": 1}}


def test_tool_response_error():
    out = _tool_response(
        ok=False,
        error={"code": ErrorCode.NO_API_KEY, "hint": "Set key", "detail": "Missing TRIPO key"},
    )
    parsed = json.loads(out)
    assert parsed == {
        "ok": False,
        "error": {"code": "NO_API_KEY", "hint": "Set key", "detail": "Missing TRIPO key"},
    }


def test_tool_error_carries_code_and_hint():
    err = ToolError(ErrorCode.STATE_REQUIRED, hint="Load HDRI first", detail="No TexEnvironment node")
    assert err.code is ErrorCode.STATE_REQUIRED
    assert err.hint == "Load HDRI first"
    assert err.detail == "No TexEnvironment node"
    assert "STATE_REQUIRED" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_envelope.py -v`
Expected: `ImportError: cannot import name '_tool_response' from 'blender_mcp._envelope'` or similar.

- [ ] **Step 3: Implement `_envelope.py`**

`src/blender_mcp/_envelope.py`:

```python
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
            logger.info(f"{fn.__name__} returned ToolError: {e.code}: {e.hint}")
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
        # Already-an-envelope passthrough: parse to confirm shape, else wrap
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict) and "ok" in parsed:
                    return result
            except json.JSONDecodeError:
                pass
            return _tool_response(ok=True, data=result)
        return _tool_response(ok=True, data=result)
    return wrapped
```

- [ ] **Step 4: Stub `_errors.py` so import works**

`src/blender_mcp/_errors.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify pass**

Run: `uv run pytest tests/test_envelope.py -v`
Expected: 3 PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/blender_mcp/_envelope.py src/blender_mcp/_errors.py tests/test_envelope.py
git commit -m "feat: tool envelope helpers + ToolError + error code enum"
```

---

## Task 3: `_format_error()` pattern matcher + tests

**Files:**
- Modify: `src/blender_mcp/_errors.py`
- Create: `tests/test_errors.py`

- [ ] **Step 1: Write failing tests**

`tests/test_errors.py`:

```python
import socket
from blender_mcp._errors import _format_error


def test_connection_refused_maps_to_state_required():
    exc = ConnectionRefusedError("[Errno 61] Connection refused")
    out = _format_error("get_scene_info", exc)
    assert out["code"] == "STATE_REQUIRED"
    assert "Connect to Claude" in out["hint"]


def test_socket_timeout_maps_to_network():
    exc = socket.timeout("timed out")
    out = _format_error("render_image", exc)
    assert out["code"] == "NETWORK"
    assert "timeout" in out["hint"].lower() or "busy" in out["hint"].lower()


def test_keyerror_for_api_key_maps_to_no_api_key():
    exc = KeyError("api_key")
    out = _format_error("generate_tripo3d_text_to_3d", exc)
    assert out["code"] == "NO_API_KEY"
    assert "api key" in out["hint"].lower()


def test_value_error_maps_to_bad_input():
    exc = ValueError("Invalid hex color: '#zzz'")
    out = _format_error("apply_material_color", exc)
    assert out["code"] == "BAD_INPUT"


def test_unknown_exception_maps_to_internal():
    exc = RuntimeError("something weird")
    out = _format_error("foo", exc)
    assert out["code"] == "INTERNAL"
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest tests/test_errors.py -v`
Expected: 5 fails (current stub returns INTERNAL for everything).

- [ ] **Step 3: Implement the pattern matcher**

Replace `src/blender_mcp/_errors.py` with:

```python
"""Error formatter — pattern-matches exceptions to actionable hints.

Used by tool_envelope to turn raw exceptions into the {code, hint, detail}
shape consumers can branch on."""
from __future__ import annotations
import socket
from typing import Any


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
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_errors.py -v`
Expected: 5 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/blender_mcp/_errors.py tests/test_errors.py
git commit -m "feat: _format_error pattern matcher with actionable hints"
```

---

## Task 4: `SERVICE_REGISTRY` seed in addon.py

**Files:**
- Modify: `addon.py` (top, after `_BLENDERMCP_CRED_SIDECAR` constant)

- [ ] **Step 1: Add the registry near the top of `addon.py`**

Insert after the `_BLENDERMCP_CRED_SIDECAR` line (~line 49):

```python
# --------------------------------------------------------------------------
# Service registry — minimal seed for Sprint 5; full god-class refactor in
# Sprint 10 reuses the same Service dataclass and field names.
# --------------------------------------------------------------------------
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Service:
    name: str
    """Lower-snake-case key (matches BLENDERMCP_<NAME>_API_KEY env var stem)."""

    needs_key: bool
    """If True, calls fail with NO_API_KEY when no key is configured."""

    key_pref: Optional[str] = None
    """Field name on BlenderMCPAddonPreferences holding the persistent key."""

    setup_url: Optional[str] = None
    """Where users get an API key — surfaced in error hints + N-panel link."""

    free_tier: bool = False
    """Indicates this provider is meaningfully usable without paying."""

    description: str = ""


SERVICE_REGISTRY: List[Service] = [
    Service(name="polyhaven",   needs_key=False, free_tier=True,
            setup_url="https://polyhaven.com/",
            description="CC0 PBR textures + HDRIs + models, ~1900 assets"),
    Service(name="ambientcg",   needs_key=False, free_tier=True,
            setup_url="https://ambientcg.com/",
            description="CC0 PBR materials, ~2000 assets"),
    Service(name="sketchfab",   needs_key=True, free_tier=True,
            key_pref="sketchfab_api_key",
            setup_url="https://sketchfab.com/settings/password",
            description="Massive 3D model library (CC + paid)"),
    Service(name="hyper3d",     needs_key=True, free_tier=True,
            key_pref="hyper3d_api_key",
            setup_url="https://hyper3d.ai/",
            description="AI 3D generation (Rodin) — built-in free trial key"),
    Service(name="hunyuan3d",   needs_key=True, free_tier=False,
            key_pref="hunyuan3d_secret_id",
            setup_url="https://cloud.tencent.com/",
            description="Tencent Hunyuan 3D AI generation (CN)"),
    Service(name="tripo3d",     needs_key=True, free_tier=False,
            key_pref="tripo3d_api_key",
            setup_url="https://platform.tripo3d.ai/",
            description="AI 3D generation (text/image-to-3D, full PBR)"),
    Service(name="meshy",       needs_key=True, free_tier=False,
            key_pref="meshy_api_key",
            setup_url="https://www.meshy.ai/settings/api",
            description="AI 3D generation (preview + refine, multi-format)"),
    Service(name="openai",      needs_key=True, free_tier=False,
            key_pref="openai_api_key",
            setup_url="https://platform.openai.com/api-keys",
            description="OpenAI-compatible image gen (DALL-E / Comfly / OpenRouter / vLLM via openai_base_url)"),
    Service(name="codex",       needs_key=False, free_tier=True,
            setup_url="https://github.com/openai/codex",
            description="Codex CLI image gen via ChatGPT subscription quota"),
]


def get_service(name: str) -> Optional[Service]:
    for s in SERVICE_REGISTRY:
        if s.name == name:
            return s
    return None
```

- [ ] **Step 2: Verify addon.py still parses**

Run: `cd /Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp && uv run python -c "import ast; ast.parse(open('addon.py').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add addon.py
git commit -m "feat: SERVICE_REGISTRY seed for envelope decorator (sprint 10 will expand)"
```

---

## Task 5: Apply `@tool_envelope` to all `get_*_status` tools (uniform pattern, lowest risk first)

**Files:**
- Modify: `src/blender_mcp/server.py` (every `get_*_status` function — there are ~9: polyhaven, sketchfab, hyper3d, hunyuan3d, tripo3d, meshy, ambientcg, openai, codex)

- [ ] **Step 1: Add envelope import at top of server.py**

In `src/blender_mcp/server.py`, near the existing imports:

```python
from ._envelope import tool_envelope, ToolError, ErrorCode, _tool_response
from ._errors import _format_error
```

- [ ] **Step 2: Migrate `get_polyhaven_status` as the template**

Find the existing `get_polyhaven_status` (~line 555). Replace its body to use the envelope:

```python
@tool_envelope
@telemetry_tool("get_polyhaven_status")
@mcp.tool()
def get_polyhaven_status(ctx: Context) -> str:
    """Check if PolyHaven integration is enabled. PolyHaven hosts CC0 PBR
    textures, HDRIs, and 3D models — no API key required."""
    blender = get_blender_connection()
    result = blender.send_command("get_polyhaven_status")
    return result
```

Note: drop the prose ("PolyHaven is good at Textures, …") — the registry has it. Drop the try/except — `tool_envelope` handles it. The `return result` is a dict; envelope wraps as ok=True.

- [ ] **Step 3: Apply identical pattern to the other 8 status tools**

For each of `get_sketchfab_status`, `get_hyper3d_status`, `get_hunyuan3d_status`, `get_tripo3d_status`, `get_meshy_status`, `get_ambientcg_status`, `get_openai_status`, `get_codex_status`:

Add `@tool_envelope` above `@mcp.tool()`. Strip the try/except. Strip prose epilogues. Return the bare result.

- [ ] **Step 4: Update `tests/test_envelope.py` with status-shape assertions**

Append to `tests/test_envelope.py`:

```python
def test_get_polyhaven_status_envelope_shape(mock_blender_connection):
    """All get_*_status tools should return the canonical envelope."""
    import json
    from blender_mcp.server import get_polyhaven_status
    mock_blender_connection.send_command.return_value = {
        "enabled": True,
        "message": "PolyHaven ready",
    }
    out = get_polyhaven_status(None)
    parsed = json.loads(out)
    assert parsed["ok"] is True
    assert parsed["data"]["enabled"] is True


def test_get_polyhaven_status_handles_addon_disconnect(mock_blender_connection):
    import json
    from blender_mcp.server import get_polyhaven_status
    mock_blender_connection.send_command.side_effect = ConnectionRefusedError("[Errno 61]")
    out = get_polyhaven_status(None)
    parsed = json.loads(out)
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "STATE_REQUIRED"
    assert "Connect to Claude" in parsed["error"]["hint"]
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_envelope.py -v`
Expected: 5 PASSED (3 original + 2 new).

- [ ] **Step 6: Commit**

```bash
git add src/blender_mcp/server.py tests/test_envelope.py
git commit -m "refactor: migrate all get_*_status tools to tool envelope"
```

---

## Task 6: Migrate remaining tools to envelope (in two batches)

Apply `@tool_envelope` + drop try/except + return raw dicts/structures (not JSON strings) for the remaining ~47 tools. Split into two batches to keep diffs reviewable.

**Files:**
- Modify: `src/blender_mcp/server.py` (extensively)

- [ ] **Step 1 (Batch A): Material / geometry / camera / render tools**

Tools to migrate: `apply_material_color`, `apply_archviz_material`, `list_archviz_genres`, `set_texture`, `place_on_ground`, `set_camera_view`, `frame_camera_to_objects`, `render_image`, `mesh_cleanup`, `boolean_cutout`, `setup_lighting`, `set_world_hdri_rotation`, `scatter_on_surface`, `array_duplicate`, `curve_extrude_profile`, `quick_export`.

Pattern for each:
1. Add `@tool_envelope` above the tool decorator.
2. Remove the outer `try / except: return f"Error in X: ..."`.
3. Return the raw dict (or whatever structured result the addon returns) instead of `json.dumps(result, indent=2)` — the envelope serializes.
4. Where the function called `bpy_send.send_command(...)` and got back a dict that already had a top-level `"error"` key, raise `ToolError(ErrorCode.INTERNAL, hint=…, detail=…)` instead.

- [ ] **Step 2 (Batch A): Verify and commit**

Run: `uv run pytest -v` — make sure existing tests still pass.

```bash
git add src/blender_mcp/server.py
git commit -m "refactor: migrate material/geometry/camera/render tools to envelope (batch A)"
```

- [ ] **Step 3 (Batch B): Asset library + AI 3D + image gen + diagnostic tools**

Tools to migrate: `search_polyhaven_assets`, `download_polyhaven_asset`, `get_polyhaven_categories`, `search_sketchfab_models`, `get_sketchfab_model_preview`, `download_sketchfab_model`, `search_ambientcg_assets`, `download_ambientcg_asset`, `generate_hyper3d_model_via_text`, `generate_hyper3d_model_via_images`, `poll_rodin_job_status`, `import_generated_asset`, `generate_hunyuan3d_model`, `poll_hunyuan_job_status`, `import_generated_asset_hunyuan`, `generate_tripo3d_text_to_3d`, `generate_tripo3d_image_to_3d`, `generate_meshy_text_to_3d`, `generate_meshy_image_to_3d`, `generate_3d_smart`, `generate_image_codex`, `generate_image_openai`, `check_services`, `get_usage_report`, `set_usage_budget`, `reset_usage_counters`, `verify_object_grounded`, `get_viewport_screenshot`, `get_object_info`, `get_scene_info`, `execute_blender_code`.

Same pattern. Note: `execute_blender_code` keeps its current `BlenderCommandError` distinction — that PR-228 logic stays inside the try-block but the outer wrapper is now envelope-style.

- [ ] **Step 4 (Batch B): Verify**

Run: `uv run pytest -v && uv run python -c "import ast; ast.parse(open('src/blender_mcp/server.py').read()); print('ok')"`
Expected: tests still pass, syntax ok.

- [ ] **Step 5 (Batch B): Commit**

```bash
git add src/blender_mcp/server.py
git commit -m "refactor: migrate asset-library / AI-gen / diagnostic tools to envelope (batch B)"
```

---

## Task 7: Mass naming pass (hard renames, no aliases)

Rename ~8 tools per the spec:

| Old name | New name |
|---|---|
| `import_generated_asset` | `import_hyper3d_asset` |
| `import_generated_asset_hunyuan` | `import_hunyuan3d_asset` |
| `poll_rodin_job_status` | `poll_hyper3d_job_status` |
| `poll_hunyuan_job_status` | unchanged (already consistent) |
| `generate_hyper3d_model_via_text` | `generate_hyper3d_text_to_3d` |
| `generate_hyper3d_model_via_images` | `generate_hyper3d_image_to_3d` |

**Files:**
- Modify: `src/blender_mcp/server.py` (function names + decorator order)
- Modify: `addon.py` (dispatcher entries in `_execute_command_internal`)
- Create: `tests/test_naming.py`

- [ ] **Step 1: Write the regression-style naming test FIRST**

`tests/test_naming.py`:

```python
"""After v2.0 mass-rename, no stale legacy names should remain in
server.py @mcp.tool() definitions or addon.py dispatcher entries."""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVER = (REPO / "src" / "blender_mcp" / "server.py").read_text()
ADDON = (REPO / "addon.py").read_text()

LEGACY_NAMES = [
    "import_generated_asset",
    "import_generated_asset_hunyuan",
    "poll_rodin_job_status",
    "generate_hyper3d_model_via_text",
    "generate_hyper3d_model_via_images",
]


def test_no_legacy_function_defs_in_server():
    for name in LEGACY_NAMES:
        # def lines (zero or one for old names — legacy deprecated, none allowed)
        assert f"def {name}(" not in SERVER, f"legacy name still defined: {name}"


def test_no_legacy_dispatcher_keys_in_addon():
    for name in LEGACY_NAMES:
        # exact dispatcher key match: "<name>": self.<name>
        assert f'"{name}"' not in ADDON, f"legacy dispatcher key remains: {name}"
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest tests/test_naming.py -v`
Expected: fails — legacy names still present.

- [ ] **Step 3: Rename in `server.py`**

For each legacy name, find the `def <old_name>` and rename to the new one. Update any internal references.

- [ ] **Step 4: Rename in `addon.py` dispatcher**

In `_execute_command_internal` find the `handlers = {...}` dict and rename the keys (`"import_generated_asset"` → `"import_hyper3d_asset"`, etc.). The method targets stay the same name (`self.import_generated_asset`) — only the dispatcher keys change.

OR — for cleanliness — also rename the addon-side methods. Do that: `addon.py:self.import_generated_asset` → `self.import_hyper3d_asset`, then dispatcher keys to match.

- [ ] **Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: previous tests pass + new naming test now passes (no legacy names found).

- [ ] **Step 6: Commit**

```bash
git add src/blender_mcp/server.py addon.py tests/test_naming.py
git commit -m "refactor!: rename hyper3d tools for consistency (BC-break)

- import_generated_asset -> import_hyper3d_asset
- import_generated_asset_hunyuan -> import_hunyuan3d_asset
- poll_rodin_job_status -> poll_hyper3d_job_status
- generate_hyper3d_model_via_text -> generate_hyper3d_text_to_3d
- generate_hyper3d_model_via_images -> generate_hyper3d_image_to_3d

No aliases per BC=B decision in roadmap spec."
```

---

## Task 8: Smart-router fixes (Hyper3D bail bug + cost calibration)

**Files:**
- Modify: `addon.py` (`generate_3d_smart` method around line 3329)
- Create: `tests/test_smart_router.py`

- [ ] **Step 1: Write a failing test for the Hyper3D bail bug**

`tests/test_smart_router.py`:

```python
"""Mock-based tests for generate_3d_smart routing logic.

We don't actually invoke providers — we patch the underlying
generate_*_text_to_3d methods on BlenderMCPServer and assert the right
one was called with the right args."""
from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture
def server_with_hyper3d_only():
    """Return a fake server where only Hyper3D is configured."""
    from addon import BlenderMCPServer
    s = BlenderMCPServer.__new__(BlenderMCPServer)
    s.check_services = lambda: {
        "summary": {"ready": ["polyhaven", "hyper3d"]},
        "services": {},
    }
    s.generate_hyper3d_text_to_3d = MagicMock(return_value={"imported_objects": ["A"]})
    s.generate_tripo3d_text_to_3d = MagicMock()
    s.generate_meshy_text_to_3d = MagicMock()
    return s


def test_smart_router_actually_invokes_hyper3d(server_with_hyper3d_only):
    """Regression: pre-v2 the router silently bailed with fallback_required."""
    from addon import BlenderMCPServer
    result = BlenderMCPServer.generate_3d_smart(
        server_with_hyper3d_only,
        prompt="brass door knocker",
        quality="fast",
    )
    server_with_hyper3d_only.generate_hyper3d_text_to_3d.assert_called_once()
    assert "fallback_required" not in (result or {})
    assert result.get("imported_objects") == ["A"]


def test_smart_router_cost_estimate_tripo_best_is_six_not_ten():
    """Regression: pre-v2 'best' Tripo3D was estimated at 10 credits,
    skipping Tripo when max_credits=8 even though typical cost is ~6."""
    from addon import BlenderMCPServer
    s = BlenderMCPServer.__new__(BlenderMCPServer)
    s.check_services = lambda: {
        "summary": {"ready": ["tripo3d", "meshy"]},
        "services": {},
    }
    s.generate_tripo3d_text_to_3d = MagicMock(return_value={"imported_objects": ["X"]})
    s.generate_meshy_text_to_3d = MagicMock()
    result = BlenderMCPServer.generate_3d_smart(
        s, prompt="x", quality="best", max_credits=8,
    )
    s.generate_tripo3d_text_to_3d.assert_called_once()
    s.generate_meshy_text_to_3d.assert_not_called()
```

- [ ] **Step 2: Run to confirm failures**

Run: `uv run pytest tests/test_smart_router.py -v`
Expected: 2 fails (hyper3d bails / tripo skipped due to bad cost).

- [ ] **Step 3: Refactor `generate_3d_smart` in addon.py**

In `addon.py` `generate_3d_smart` method:

a) Update `cost_estimates` to median values per spec C3:

```python
cost_estimates = {
    ("tripo3d", "fast"):     3,
    ("tripo3d", "standard"): 5,
    ("tripo3d", "best"):     6,    # was 10
    ("meshy", "fast"):       20,
    ("meshy", "standard"):   20,
    ("meshy", "best"):       40,
    ("hyper3d", "fast"):     0,
    ("hyper3d", "standard"): 0,
    ("hyper3d", "best"):     0,
    ("hunyuan3d", "fast"):   0,
    ("hunyuan3d", "standard"): 0,
    ("hunyuan3d", "best"):   0,
}
```

b) Replace the Hyper3D bail block (`return {"chosen_provider": "hyper3d", "fallback_required": True, ...}`) with an actual delegation:

```python
elif chosen == "hyper3d":
    # Map quality tier to Rodin model_version (best ≈ Standard, fast/standard ≈ Detailed-fast)
    result = self.generate_hyper3d_text_to_3d(
        prompt=prompt,
        target_size=target_size,
        max_wait_seconds=max_wait_seconds,
    )
elif chosen == "hunyuan3d":
    result = self.generate_hunyuan3d_model(
        text_prompt=prompt,
        target_size=target_size,
    )
```

(Adjust method signatures to whatever the addon methods actually accept — verify with grep before writing.)

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_smart_router.py -v`
Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add addon.py tests/test_smart_router.py
git commit -m "fix: smart router actually invokes Hyper3D/Hunyuan3D + calibrate cost estimates"
```

---

## Task 9: Smart router accepts `reference_image_path`

**Files:**
- Modify: `addon.py` (`generate_3d_smart` signature and routing branches)
- Modify: `src/blender_mcp/server.py` (`generate_3d_smart` MCP wrapper signature + docstring)
- Modify: `tests/test_smart_router.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/test_smart_router.py`:

```python
def test_smart_router_routes_to_image_to_3d_when_ref_provided():
    from addon import BlenderMCPServer
    s = BlenderMCPServer.__new__(BlenderMCPServer)
    s.check_services = lambda: {
        "summary": {"ready": ["tripo3d"]},
        "services": {},
    }
    s.generate_tripo3d_image_to_3d = MagicMock(return_value={"imported_objects": ["I"]})
    s.generate_tripo3d_text_to_3d = MagicMock()
    BlenderMCPServer.generate_3d_smart(
        s,
        prompt="brass knob",
        quality="standard",
        reference_image_url="https://example.com/x.jpg",
    )
    s.generate_tripo3d_image_to_3d.assert_called_once()
    s.generate_tripo3d_text_to_3d.assert_not_called()
```

(Note: parameter name is `reference_image_url` — public URL only, file upload is out of scope per the existing image-to-3D tools' contract.)

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest tests/test_smart_router.py::test_smart_router_routes_to_image_to_3d_when_ref_provided -v`
Expected: TypeError or KeyError because parameter doesn't exist.

- [ ] **Step 3: Update method signatures**

In `addon.py` `generate_3d_smart`:

```python
def generate_3d_smart(self, prompt, quality="standard",
                      max_credits=None, prefer_provider=None,
                      target_size=2.0, max_wait_seconds=240,
                      reference_image_url=None):    # NEW
    ...
    # In each routing branch, if reference_image_url is set, call the
    # provider's image-to-3D variant instead:
    if chosen == "tripo3d":
        if reference_image_url:
            result = self.generate_tripo3d_image_to_3d(
                image_url=reference_image_url,
                model_version={...}[quality],
                target_size=target_size,
                max_wait_seconds=max_wait_seconds,
            )
        else:
            result = self.generate_tripo3d_text_to_3d(prompt=prompt, ...)
    elif chosen == "meshy":
        if reference_image_url:
            result = self.generate_meshy_image_to_3d(
                image_url=reference_image_url,
                target_size=target_size,
                max_wait_seconds=max_wait_seconds,
            )
        else:
            result = self.generate_meshy_text_to_3d(prompt=prompt, ...)
```

In `src/blender_mcp/server.py` `generate_3d_smart` MCP wrapper, add `reference_image_url: str = None` parameter and pass to the send_command params.

Update the docstring to mention image-to-3D routing when the param is set.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_smart_router.py -v`
Expected: all PASSED.

- [ ] **Step 5: Commit**

```bash
git add addon.py src/blender_mcp/server.py tests/test_smart_router.py
git commit -m "feat: generate_3d_smart accepts reference_image_url for image-to-3D routing"
```

---

## Task 10: State leakage fail-fast

Tools that silently no-op (or worse) when prerequisites aren't met must raise `ToolError(STATE_REQUIRED)` instead.

**Files:**
- Modify: `addon.py` (multiple methods)

- [ ] **Step 1: Identify and fix offenders**

For each:

a) `set_world_hdri_rotation` (~line 2005): currently returns `{"error": "No TexEnvironment node — set an HDRI first via download_polyhaven_asset"}` as a dict. Change to raise `ToolError(ErrorCode.STATE_REQUIRED, hint="Call download_polyhaven_asset(asset_type='hdris', asset_id=...) first to load an HDRI.", detail="No TexEnvironment node found in world")`.

b) `apply_archviz_material` with `genre='painted_wall'` (~line 1814): currently returns `{"error": "genre='painted_wall' requires custom_hex='#RRGGBB'"}`. Change to raise `ToolError(ErrorCode.BAD_INPUT, hint="Pass custom_hex='#RRGGBB' when genre='painted_wall'.")`.

c) `frame_camera_to_objects` (already creates a camera if none — keep, but add `data["camera_created"] = True/False` to the return so the LLM can tell).

d) `generate_image_codex` when codex CLI is missing: currently returns `{"error": "Codex CLI not found"}`. Change to raise `ToolError(ErrorCode.STATE_REQUIRED, hint="Install Codex CLI from https://github.com/openai/codex and run codex login.")`.

(Note: `tool_envelope` in `server.py` doesn't see addon-side errors — it sees what `send_command` returns. We need a small helper at the addon side: when an addon method raises a custom exception, the dispatcher wraps as `{"status":"error", "message":"<code>:<hint>"}` and the existing `BlenderCommandError` in server.py already turns this into a Python error caught by `tool_envelope`. So really we want to update each addon method that returns `{"error": ...}` dicts so that the server-side wrapper gets `{"error": ...}` and converts.)

Simpler approach: have the server.py wrappers detect dict returns with an `"error"` key and re-raise as `ToolError`:

In each `@mcp.tool()` wrapper that calls `blender.send_command(...)`:

```python
result = blender.send_command(...)
if isinstance(result, dict) and "error" in result:
    raise ToolError(ErrorCode.STATE_REQUIRED, hint=result["error"], detail="")
return result
```

This is one helper — `_check_addon_result(result)` — applied uniformly. We can add this to `_envelope.py`:

```python
def _check_addon_result(result):
    """Convert addon-side {"error": "..."} dicts into ToolError.
    Used by server.py @mcp.tool wrappers right after send_command."""
    if isinstance(result, dict) and "error" in result and result.get("error"):
        msg = result["error"]
        # Heuristic: if it mentions "first" / "load" / "before" → STATE_REQUIRED
        # If it mentions param / required → BAD_INPUT
        # Else INTERNAL
        low = msg.lower()
        if any(x in low for x in ("first", "before", "load", "configure", "no key", "no api key", "not configured")):
            raise ToolError(ErrorCode.STATE_REQUIRED, hint=msg)
        if any(x in low for x in ("required", "must", "invalid", "bad", "unknown")):
            raise ToolError(ErrorCode.BAD_INPUT, hint=msg)
        raise ToolError(ErrorCode.INTERNAL, hint=msg)
    return result
```

Apply `_check_addon_result(...)` after every `blender.send_command(...)` call in `server.py`.

- [ ] **Step 2: Run all tests + smoke**

Run: `uv run pytest -v`
Expected: pass.

- [ ] **Step 3: Commit**

```bash
git add src/blender_mcp/_envelope.py src/blender_mcp/server.py
git commit -m "feat: addon error dicts raise structured ToolError (state leakage fail-fast)"
```

---

## Task 11: Docstring + cross-ref + download_polyhaven target_size

Three small `S` items bundled.

**Files:**
- Modify: `src/blender_mcp/server.py` (docstrings)
- Modify: `addon.py` (`download_polyhaven_asset`)

- [ ] **Step 1: Rewrite `execute_blender_code` docstring**

Replace the body of the `execute_blender_code` docstring in `server.py` with:

```python
@tool_envelope
@telemetry_tool("execute_blender_code")
@mcp.tool()
def execute_blender_code(ctx: Context, code: str) -> str:
    """
    Run arbitrary Python in Blender — the escape hatch.

    USE ONLY WHEN no purpose-built tool fits. First check whether one of
    these covers your need:

      Materials: apply_material_color, apply_archviz_material, set_texture
      Geometry:  boolean_cutout, mesh_cleanup, scatter_on_surface,
                 array_duplicate, curve_extrude_profile, place_on_ground
      Camera:    set_camera_view, frame_camera_to_objects
      Lighting:  setup_lighting, set_world_hdri_rotation
      Render:    render_image
      Export:    quick_export
      AI gen:    generate_3d_smart, generate_image_codex, generate_image_openai
      Verify:    verify_object_grounded, get_viewport_screenshot

    Direct execute_blender_code is appropriate for one-offs that don't fit
    the above (custom modifier stacks, drivers, geometry-nodes graph
    editing, undocumented operators). Always save your .blend before
    running it — generated code can corrupt the scene.

    Parameters:
    - code: Python code to execute. `bpy` is in scope.

    Returns: any stdout from the executed code, plus a list of newly
    created/modified object names.
    """
    ...
```

- [ ] **Step 2: Add cross-reference to `set_camera_view` docstring**

Prepend to existing docstring:

```
WHEN TO USE THIS vs frame_camera_to_objects:
- set_camera_view: pick a preset angle (front/back/left/right/top/3q/iso)
  for a quick one-call camera positioning. No DOF, no composition rules.
- frame_camera_to_objects: fit camera to a list of target objects with
  composition (thirds/center) + optional DOF. Preferred for hero shots.
```

And the reciprocal in `frame_camera_to_objects`:

```
WHEN TO USE THIS vs set_camera_view:
- frame_camera_to_objects: needed when you want the camera to actually
  contain specific objects in its frame, with composition + DOF.
- set_camera_view: when you just need a preset angle, no specific subject.
```

- [ ] **Step 3: Add `target_size` to `download_polyhaven_asset`**

In `addon.py` `download_polyhaven_asset`, change signature:

```python
def download_polyhaven_asset(self, asset_id, asset_type,
                             resolution="1k", file_format=None,
                             target_size=None):     # NEW
```

After successful import, if `target_size is not None and asset_type == "models"`, compute the imported model's largest dimension and rescale so it equals `target_size`. Mirror the logic already in `download_sketchfab_model`.

In `src/blender_mcp/server.py` `download_polyhaven_asset` MCP wrapper, add `target_size: float = None` param.

- [ ] **Step 4: Verify**

Run: `uv run pytest -v`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/blender_mcp/server.py addon.py
git commit -m "docs+feat: execute_blender_code guidance, camera cross-ref, polyhaven target_size"
```

---

## Task 12: OpenAI-compat generalization (base_url + model)

**Files:**
- Modify: `addon.py` (`BlenderMCPAddonPreferences`, scene props, `_get_openai_*` helpers, `generate_image_openai`)
- Modify: `src/blender_mcp/server.py` (`generate_image_openai` MCP wrapper)
- Create: `tests/test_openai_compat.py`

- [ ] **Step 1: Add `openai_base_url` field to AddonPreferences**

In `addon.py` `BlenderMCPAddonPreferences`:

```python
openai_base_url: bpy.props.StringProperty(
    name="OpenAI base URL",
    description="OpenAI-compatible API endpoint. Default: https://api.openai.com/v1. "
                "Use ai.comfly.chat/v1 for Comfly, openrouter.ai/api/v1 for OpenRouter, etc.",
    default="https://api.openai.com/v1",
    update=_persist_credentials,
)
```

Also add to scene props (`blendermcp_openai_base_url`) and the `_get_*` helpers:

```python
def _get_openai_base_url(self):
    return self._get_config_value(
        "blendermcp_openai_base_url",
        "openai_base_url",
        "BLENDERMCP_OPENAI_BASE_URL",
    ) or "https://api.openai.com/v1"
```

Update sidecar field list: `"openai_base_url"` joins the persisted set in `_persist_credentials`.

- [ ] **Step 2: Refactor `generate_image_openai` to use the configurable base URL**

In `addon.py` `generate_image_openai` method, replace the hardcoded `self.OPENAI_BASE` with `self._get_openai_base_url()`.

- [ ] **Step 3: Add provider templates dropdown to N-panel**

In the panel-draw method's OpenAI section:

```python
if scene.blendermcp_use_openai:
    sb = ai_box.box()
    sb.prop(scene, "blendermcp_openai_base_url", text="Base URL")
    if prefs:
        sb.prop(prefs, "openai_api_key", text="API Key")
    else:
        sb.prop(scene, "blendermcp_openai_api_key", text="API Key")
    # Provider preset dropdown
    op_row = sb.row(align=True)
    op_row.label(text="Preset:")
    for label, url in [
        ("Official", "https://api.openai.com/v1"),
        ("Comfly",   "https://ai.comfly.chat/v1"),
        ("OpenRouter", "https://openrouter.ai/api/v1"),
    ]:
        op = op_row.operator("wm.context_set_string", text=label)
        op.data_path = "scene.blendermcp_openai_base_url"
        op.value = url
    sb.label(text="⚠ Separate billing from ChatGPT Plus", icon='INFO')
```

- [ ] **Step 4: Write the live + mock test**

`tests/test_openai_compat.py`:

```python
"""Tests that generate_image_openai routes to the configured base_url."""
from unittest.mock import patch, MagicMock


def test_image_gen_uses_configured_base_url(monkeypatch, tmp_path):
    """Mock requests.post to capture the URL it's called with."""
    from addon import BlenderMCPServer
    s = BlenderMCPServer.__new__(BlenderMCPServer)
    s._get_openai_api_key = lambda: "sk-test"
    s._get_openai_base_url = lambda: "https://ai.comfly.chat/v1"
    s.OPENAI_IMAGE_PRICING = {("dall-e-3", "standard", "1024x1024"): 0.04}

    captured = {}
    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        m = MagicMock()
        m.json.return_value = {"data": [{"url": "https://x/y.png"}]}
        m.status_code = 200
        return m

    with patch("addon.requests.post", side_effect=fake_post), \
         patch("addon._resilient_download_to_file", lambda u, p, **k: open(p, "wb").close()):
        out = BlenderMCPServer.generate_image_openai(
            s, prompt="test", model="dall-e-3", size="1024x1024", quality="standard",
            save_to=str(tmp_path / "out.png"),
        )
    assert captured["url"].startswith("https://ai.comfly.chat/v1/")
    assert "out.png" in (out.get("saved_paths") or [""])[0]
```

- [ ] **Step 5: Run mock test**

Run: `uv run pytest tests/test_openai_compat.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add addon.py src/blender_mcp/server.py tests/test_openai_compat.py
git commit -m "feat: OpenAI-compatible base_url config (Comfly/OpenRouter/vLLM)"
```

---

## Task 13: Comfly live test — DEFERRED to Task 17 integration phase

This task is **deferred to Task 17** so the subagent driving Tasks 1–16 never blocks on Blender's socket lifecycle. Subagents do code edits + `uv run pytest` only.

The Task 12 mock test already proves `generate_image_openai` honors `openai_base_url`. The live Comfly test (gpt-image-2 + gemini-3.1-flash-image-preview-2k) runs in Task 17 once all code changes are committed.

---

## Task 14: Telemetry default → opt-in

**Files:**
- Modify: `addon.py` (`BlenderMCPAddonPreferences.telemetry_consent`)

- [ ] **Step 1: Flip the default**

In `BlenderMCPAddonPreferences`:

```python
telemetry_consent: BoolProperty(
    name="Allow Telemetry",
    description="Allow collection of prompts, code snippets, and screenshots to help improve Blender MCP. "
                "Off by default in this fork — opt-in only.",
    default=False,    # was True
)
```

- [ ] **Step 2: Add a smoke test**

Append to `tests/test_envelope.py`:

```python
def test_telemetry_default_is_opt_in():
    """In the v2 fork, telemetry_consent defaults to False (opt-in)."""
    import re
    src = open("addon.py").read()
    # Match the telemetry_consent property block — default must be False
    m = re.search(
        r"telemetry_consent:\s*BoolProperty\([^)]*default\s*=\s*(\w+)",
        src,
        re.DOTALL,
    )
    assert m, "could not find telemetry_consent property"
    assert m.group(1) == "False", \
        f"telemetry default is {m.group(1)}; should be False (opt-in)"
```

- [ ] **Step 3: Run test**

Run: `uv run pytest tests/test_envelope.py::test_telemetry_default_is_opt_in -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add addon.py tests/test_envelope.py
git commit -m "feat: telemetry default flipped to opt-in (was on by default in upstream)"
```

---

## Task 15: AGENTS.md + CLAUDE.md migration cheat sheet

**Files:**
- Create: `AGENTS.md` (fork root)
- Modify: `/Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/CLAUDE.md` (project root, not fork)

- [ ] **Step 1: Write `AGENTS.md`**

`/Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp/AGENTS.md`:

```markdown
# Conventions for AI agents working ON the blender-mcp fork

When extending the fork, follow these rules to keep the toolkit coherent.

## Tool naming
- Provider-bound tools: `<verb>_<provider>_<object>` — e.g. `generate_tripo3d_text_to_3d`, `import_hyper3d_asset`, `poll_meshy_job_status`.
- Generic tools: `<verb>_<object>` — e.g. `apply_material_color`, `frame_camera_to_objects`.
- No legacy aliases when renaming. v2 is BC-break by design.

## Return shape
- Every `@mcp.tool()` returns the canonical envelope:
  - `{"ok": true, "data": ...}` on success
  - `{"ok": false, "error": {"code": ..., "hint": ..., "detail": ...}}` on failure
- Use the `@tool_envelope` decorator. Don't return naked strings or `Error: ...` prose.

## Errors
- Raise `ToolError(ErrorCode.<NAME>, hint=..., detail=...)` for known failure modes.
- Codes: `NO_API_KEY`, `RATE_LIMITED`, `NETWORK`, `BAD_INPUT`, `STATE_REQUIRED`, `NOT_FOUND`, `INTERNAL`.
- Hints must teach the user the fix, not echo the exception.

## Dispatcher pattern (until Sprint 10 refactor)
- New addon-side method goes on `BlenderMCPServer`.
- Register in `_execute_command_internal`'s handlers dict (key = same as new MCP tool name).
- Add a service entry to `SERVICE_REGISTRY` if it's a new external integration.

## Docstrings
- No prompt-steering directives. ("Don't reveal X to the user" etc.)
- Include "WHEN TO USE THIS vs <other tool>" for any tool that overlaps with another.
- Keep ≤ 8 lines for parameter descriptions.

## Telemetry
- Default off. Never re-enable in any example or default value.

## Tests
- Unit tests for pure helpers in `tests/test_*.py` (no Blender required).
- Smoke tests for tool round-trip in `tests/test_envelope.py` using the
  `mock_blender_connection` fixture.
- After every code change, run `uv run pytest -v` before committing.

## Sidecar credentials
- Lives at `~/.blendermcp_credentials.json` (mode 0600).
- Updated automatically via the `update=_persist_credentials` callback on
  every credential StringProperty.
- Sprint 10 will namespace this — don't add new credential fields to the
  shared file in the meantime; use the same callback.
```

- [ ] **Step 2: Add migration cheat sheet to project CLAUDE.md**

In `/Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/CLAUDE.md`, add a new section:

```markdown
## blender-mcp v2 migration cheat sheet (added Sprint 5)

The blender-mcp fork went BC-break at v2.0.0+fork.1. If you're an AI
agent picking up an old chat history, these mappings apply:

| Old name | New name |
|---|---|
| `import_generated_asset` | `import_hyper3d_asset` |
| `import_generated_asset_hunyuan` | `import_hunyuan3d_asset` |
| `poll_rodin_job_status` | `poll_hyper3d_job_status` |
| `generate_hyper3d_model_via_text` | `generate_hyper3d_text_to_3d` |
| `generate_hyper3d_model_via_images` | `generate_hyper3d_image_to_3d` |

All `@mcp.tool` returns now use the envelope `{"ok": bool, "data"?: ..., "error"?: {"code": str, "hint": str, "detail": str}}`. Branch on
`result["ok"]`, retry on `result["error"]["code"]` ∈ {NETWORK, RATE_LIMITED}, surface `result["error"]["hint"]` to the user.
```

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md ../CLAUDE.md
git commit -m "docs: AGENTS.md for fork contributors + v2 migration cheat sheet in project CLAUDE.md"
```

---

## Task 16: CHANGELOG + version bump + final smoke + tag + release

**Files:**
- Modify: `CHANGELOG.md`, `pyproject.toml`, `README.md`

- [ ] **Step 1: Add `[2.0.0+fork.1]` section at top of CHANGELOG.md**

Below the `# Changelog` heading, before the existing `[1.10.2+fork.1]`:

```markdown
## [2.0.0+fork.1] — 2026-04-29

**Breaking changes** — every `@mcp.tool()` now returns a canonical JSON envelope. Tool renames hard-applied without aliases. Migration cheat sheet in CLAUDE.md.

### Breaking
- All tools return `{"ok": bool, "data"?: ..., "error"?: {"code": str, "hint": str, "detail": str}}`. Legacy `Error: ...` strings and naked dicts are gone. LLM clients should branch on `ok` and `error.code`.
- Renames (no aliases):
  - `import_generated_asset` → `import_hyper3d_asset`
  - `import_generated_asset_hunyuan` → `import_hunyuan3d_asset`
  - `poll_rodin_job_status` → `poll_hyper3d_job_status`
  - `generate_hyper3d_model_via_text` → `generate_hyper3d_text_to_3d`
  - `generate_hyper3d_model_via_images` → `generate_hyper3d_image_to_3d`
- `telemetry_consent` defaults to `False` (was `True`). Re-opt-in via Blender prefs if desired.

### Added
- `tool_envelope` decorator + `ToolError` + `ErrorCode` enum (`src/blender_mcp/_envelope.py`)
- `_format_error()` actionable-hint mapper (`src/blender_mcp/_errors.py`)
- `SERVICE_REGISTRY` dataclass-based service spec at top of `addon.py`
- `generate_3d_smart` accepts `reference_image_url` for image-to-3D routing
- `download_polyhaven_asset` accepts `target_size` (None = native scale)
- OpenAI integration generalized to OpenAI-compatible: new `openai_base_url` config field on AddonPreferences/scene/env. Provider templates dropdown in N-panel: Official, Comfly, OpenRouter.
- `AGENTS.md` at fork root — conventions for AI agents extending the fork
- pytest scaffold + 5 test files (`tests/test_envelope.py`, `test_errors.py`, `test_naming.py`, `test_smart_router.py`, `test_openai_compat.py`)

### Fixed
- `generate_3d_smart` no longer silently bails when picking Hyper3D / Hunyuan3D — actually invokes the underlying generation flow.
- `generate_3d_smart` cost estimates calibrated to median observed cost (Tripo3D best 6 not 10, etc.).
- State leakage: `set_world_hdri_rotation` without HDRI, `apply_archviz_material(genre='painted_wall')` without `custom_hex` etc. now raise `STATE_REQUIRED` instead of silent no-op or vague string error.

### Documentation
- `execute_blender_code` docstring rewritten to point to purpose-built tools first.
- `set_camera_view` ↔ `frame_camera_to_objects` cross-reference each other.
- v2 migration cheat sheet added to project CLAUDE.md.

### Migration

Re-enter API keys is NOT required (sidecar persistence works across this update). Old tool-name calls in saved chat histories will fail — see the cheat sheet for the rename map.
```

- [ ] **Step 2: Update README's tool-reference and bump version banner**

Search README for the version badge/text and update to v2.0.0. Update the "Highlights vs upstream" table — add a v2.0 row noting envelope unification + OpenAI-compat.

Replace any references to old tool names with the v2 names in README's Tools reference table.

- [ ] **Step 3: Run the full test suite**

```bash
cd /Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp
uv run pytest -v
```

Expected: all green.

- [ ] **Step 4: Commit, push, tag, release**

```bash
git add CHANGELOG.md README.md pyproject.toml
git commit -m "chore: bump v2.0.0+fork.1 — Sprint 5 (LLM ergonomics) ship"
git push fork sprint-5-ergonomics
```

Open a PR from `sprint-5-ergonomics` → `develop` for review (since this is BC-break, treat as a real PR, not a fast-forward). After merge:

```bash
git checkout develop
git pull
git tag -a v2.0.0-fork.1 -m "v2.0.0+fork.1 — LLM ergonomics: envelope, naming, OpenAI-compat, telemetry opt-in"
git push fork v2.0.0-fork.1
gh release create v2.0.0-fork.1 --repo MickeyBadBad/atelier-mcp \
  --title "v2.0.0+fork.1 — Sprint 5: LLM ergonomics" \
  --notes-file <(awk '/## \[2.0.0/,/^## \[1.10.2/' CHANGELOG.md | head -n -1)
```

- [ ] **Step 5: Smoke test deferred to Task 17 integration phase**

This step is folded into Task 17 along with Task 13's live Comfly test. Keep Task 16 strictly file-edit + git operations; subagents never touch the Blender socket.

---

## Task 17: Integration phase (single live-Blender batch — runs at the very end)

**Constraint that drove this batching:** subagents driving Tasks 1–16 must not call `mcp__blender__*` or trigger addon reload. All Blender-touching verification happens here, sequentially, after every code/doc/release task is complete and committed.

**Files:** none (verification only)

- [ ] **Step 1: Sync the v2 addon.py to Blender's installed location**

```bash
cp /Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp/addon.py \
   "$HOME/Library/Application Support/Blender/5.1/scripts/addons/addon.py"
diff -q /Users/mickey/Desktop/personal_projects/FriendsInteriorDesign/blender-mcp/addon.py \
        "$HOME/Library/Application Support/Blender/5.1/scripts/addons/addon.py" \
   && echo "synced ✓"
```

- [ ] **Step 2: Trigger addon reload via execute_blender_code**

Via the running MCP socket:

```python
import sys, importlib, bpy
mod = sys.modules['addon']
bpy.ops.preferences.addon_disable(module='addon')
importlib.reload(mod)
bpy.ops.preferences.addon_enable(module='addon')
print("v2 reloaded; please click Connect to Claude")
```

User clicks Connect to Claude. Confirm reconnection by calling `mcp__blender__get_scene_info` and verifying the response is now in the v2 envelope (`{"ok": true, "data": {...}}`).

- [ ] **Step 3: Smoke `check_services`**

Call `mcp__blender__check_services`. Verify:
- Response shape is the v2 envelope
- All previously-ready services (polyhaven, sketchfab, hyper3d, tripo3d, meshy, ambientcg, openai, codex) still report `enabled=True`
- New `data.summary` structure intact

- [ ] **Step 4: Live Comfly test — gpt-image-2**

```python
prefs = bpy.context.preferences.addons['addon'].preferences
prefs.openai_base_url = "https://ai.comfly.chat/v1"
# openai_api_key already set via sidecar from earlier session
```

Via MCP, call:

```
mcp__blender__generate_image_openai(
    prompt="brass speakeasy door knocker, dark background, photographic",
    model="gpt-image-2",
    size="1024x1024",
    save_to="/tmp/sprint5_comfly_gpt2.png",
)
```

Read the PNG, confirm it's a valid 1024×1024 image of a brass door knocker.

- [ ] **Step 5: Live Comfly test — gemini-3.1-flash-image-preview-2k**

Same shape, `model="gemini-3.1-flash-image-preview-2k"`, save to `/tmp/sprint5_comfly_gemini.png`. Verify file + visual.

- [ ] **Step 6: Reset base_url back to official OpenAI**

```python
prefs.openai_base_url = "https://api.openai.com/v1"
```

(No live OpenAI test required — the mock test in Task 12 already proves base_url is honored. Real call is only made if user has direct OpenAI credit and explicitly asks.)

- [ ] **Step 7: Verify naming migration is live**

Call a renamed tool (e.g. `mcp__blender__poll_hyper3d_job_status` with a fake task id) — should error gracefully with envelope shape, not "tool not found". Then call the OLD name (`mcp__blender__poll_rodin_job_status`) — MUST fail with "tool not found" (no aliases per BC=B).

- [ ] **Step 8: Spot-check telemetry default**

```python
prefs = bpy.context.preferences.addons['addon'].preferences
assert prefs.telemetry_consent is False, "telemetry should default off"
```

- [ ] **Step 9: Verify smart router invokes Hyper3D for free-tier prompts**

```
mcp__blender__generate_3d_smart(
    prompt="small brass cube, simple",
    quality="fast",
    max_credits=0,         # only free providers (hyper3d) qualify
    max_wait_seconds=120,
)
```

If Hyper3D free-trial credits are still alive: should return `{"ok": true, "data": {"chosen_provider": "hyper3d", "imported_objects": [...]}}`. If trial is exhausted: should return envelope-shaped error with `code=NO_API_KEY` or `RATE_LIMITED` — NOT silently bail.

- [ ] **Step 10: If any bugs surfaced, hotfix + commit**

```bash
git add ...
git commit -m "fix: <bug found during Sprint 5 integration test>"
git push fork sprint-5-ergonomics
```

- [ ] **Step 11: Merge sprint-5-ergonomics → develop and finalize the release**

```bash
gh pr create --base develop --head sprint-5-ergonomics \
  --title "Sprint 5 — LLM ergonomics (v2.0.0+fork.1)" \
  --body-file docs/dev/specs/2026-04-28-blender-mcp-optimization-roadmap.md
# Review, then merge:
gh pr merge --squash --delete-branch
git checkout develop && git pull
git tag -a v2.0.0-fork.1 -m "v2.0.0+fork.1 — Sprint 5: LLM ergonomics (BC-break)"
git push fork v2.0.0-fork.1
gh release create v2.0.0-fork.1 --repo MickeyBadBad/atelier-mcp \
  --title "v2.0.0+fork.1 — Sprint 5: LLM ergonomics" \
  --notes-file <(awk '/## \[2.0.0/,/^## \[1.10.2/' CHANGELOG.md | head -n -1)
```

Sprint 5 ships when this PR is merged + tagged + released.

---

## Self-review notes

This plan covers all 14 spec deliverables:

| Spec deliverable | Tasks |
|---|---|
| 1. Error envelope unification | Tasks 2, 5, 6 |
| 2. Error messages → actionable | Task 3 |
| 3. Smart router Hyper3D bail fix | Task 8 |
| 4. Cost estimates calibrated | Task 8 |
| 5. State leakage fail-fast | Task 10 |
| 6. execute_blender_code docstring | Task 11 |
| 7. Camera tools cross-ref | Task 11 |
| 8. download_polyhaven target_size | Task 11 |
| 9. get_*_status structured envelope | Task 5 |
| 10. Mass naming pass | Task 7 |
| 11. Smart router reference_image_url | Task 9 |
| 12. Service descriptor seed | Task 4 |
| 13. OpenAI-compat generalization | Tasks 12, 13 |
| 14. Telemetry default → opt-in | Task 14 |

Plus: Task 1 (test scaffold), Task 15 (docs), Task 16 (release).

Sprint 5 spec verification matrix is covered:
- Pure helpers tests: Tasks 2, 3
- Envelope shape: Task 5
- Naming migration: Task 7
- Smart router: Tasks 8, 9
- OpenAI-compat: Tasks 12 (mock), 13 (live)
- State leakage: Task 10
- Telemetry default: Task 14

No placeholders, no "TBD". Type names match across tasks (`ToolError`, `ErrorCode`, `Service`, `_tool_response`, `tool_envelope` — consistent).

Estimated wall-clock: 4-5 days as scoped in the spec.
