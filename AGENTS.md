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
- New addon-side method goes on `BlenderMCPServer` in `addon.py`.
- Register in `_execute_command_internal`'s handlers dict (key = same as new MCP tool name).
- Add a service entry to `SERVICE_REGISTRY` if it's a new external integration.

## Docstrings
- No prompt-steering directives. ("Don't reveal X to the user" etc.)
- Include "WHEN TO USE THIS vs <other tool>" for any tool that overlaps with another.
- Keep parameter descriptions ≤ 8 lines.

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
