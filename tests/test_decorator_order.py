"""Regression test for the Sprint 5 decorator-order bug.

The MCP framework's ``@mcp.tool()`` decorator (FastMCP) registers whatever
function it receives at decoration time and returns it unchanged. That
means ``@mcp.tool()`` must be the OUTERMOST decorator — applied LAST in
the source — so it sees the fully-wrapped function:

    @mcp.tool()           # outermost: registers the wrapped function
    @telemetry_tool(...)   # middle (when present)
    @tool_envelope         # innermost: closest to def
    def foo(...): ...

If ``@mcp.tool()`` is innermost, it registers the BARE function and the
outer wrappers are bypassed by MCP-side dispatch. Tests that import the
module-level name still pass (because the name binds to the outer
wrapper), masking the bug — only live MCP calls expose it.

This test scans server.py for any ``@mcp.tool()`` line that is followed
by another ``@tool_envelope`` or ``@telemetry_tool`` decorator before the
``def`` — which would be the wrong order.
"""
from __future__ import annotations
import re
from pathlib import Path

SERVER_PY = Path(__file__).parent.parent / "src" / "blender_mcp" / "server.py"

DECO_RE = re.compile(r"^@(tool_envelope|telemetry_tool\(.*\)|mcp\.tool\(\))\s*$")
DEF_RE = re.compile(r"^\s*(async\s+)?def\s+\w+")


def _collect_decorator_blocks() -> list[tuple[int, list[str], str]]:
    """Return [(start_line, [decorator_lines...], def_line), ...]."""
    lines = SERVER_PY.read_text().splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        if DECO_RE.match(lines[i]):
            start = i
            decorators = []
            while i < len(lines) and DECO_RE.match(lines[i]):
                decorators.append(lines[i])
                i += 1
            # Skip blank lines between decorators and def
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines) and DEF_RE.match(lines[i]):
                blocks.append((start + 1, decorators, lines[i].strip()))
            continue
        i += 1
    return blocks


def test_mcp_tool_decorator_is_always_outermost():
    """Every decorator stack with @mcp.tool() must place it at the top.

    A misplaced @mcp.tool() (anywhere except the very first decorator
    line) causes MCP-side dispatch to bypass @tool_envelope and
    @telemetry_tool wrappers — the symptom is naked dict responses
    coming back to LLM clients instead of the canonical envelope shape.
    """
    blocks = _collect_decorator_blocks()
    failures = []
    for line_no, decos, def_line in blocks:
        has_mcp_tool = any(d == "@mcp.tool()" for d in decos)
        if not has_mcp_tool:
            continue
        if decos[0] != "@mcp.tool()":
            failures.append(
                f"  line {line_no}, {def_line}\n"
                f"    decorators (top-down): {decos}\n"
                f"    expected: @mcp.tool() must be the FIRST line"
            )
    assert not failures, (
        "Found {} tool(s) with @mcp.tool() not in the outermost position. "
        "MCP-side dispatch will bypass the envelope/telemetry wrappers for these:\n\n{}"
        .format(len(failures), "\n\n".join(failures))
    )


def test_envelope_is_innermost_when_present():
    """When @tool_envelope is present, it must be closest to def.

    @tool_envelope MUST run last in the call chain (= innermost in
    source) so it sees the actual function's return value before any
    other wrapper transforms it. If @telemetry_tool is between
    @tool_envelope and def, telemetry wraps the bare result before
    envelope sees it — the envelope still works for the result shape,
    but error-type classification (ToolError catch) becomes order-
    sensitive in subtle ways. Best to keep envelope innermost.
    """
    blocks = _collect_decorator_blocks()
    failures = []
    for line_no, decos, def_line in blocks:
        has_envelope = any(d == "@tool_envelope" for d in decos)
        if not has_envelope:
            continue
        # Find position of @tool_envelope and the def
        envelope_idx = decos.index("@tool_envelope")
        # @tool_envelope should be the LAST decorator (closest to def)
        if envelope_idx != len(decos) - 1:
            failures.append(
                f"  line {line_no}, {def_line}\n"
                f"    decorators (top-down): {decos}\n"
                f"    expected: @tool_envelope must be the LAST line "
                f"(closest to def)"
            )
    assert not failures, (
        "Found {} tool(s) where @tool_envelope is not innermost:\n\n{}"
        .format(len(failures), "\n\n".join(failures))
    )


def test_at_least_one_tool_uses_envelope_decorator():
    """Sanity: regression-protect against accidentally removing envelope
    from every tool (e.g. via a buggy refactor that strips decorators)."""
    blocks = _collect_decorator_blocks()
    envelope_count = sum(
        1 for _, decos, _ in blocks
        if any(d == "@tool_envelope" for d in decos)
    )
    assert envelope_count >= 50, (
        f"Expected at least 50 tools to use @tool_envelope; found "
        f"{envelope_count}. Did a refactor accidentally strip envelope "
        f"decorators?"
    )
