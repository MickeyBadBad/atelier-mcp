# Atelier — Architecture

For developers extending the codebase, debugging cross-layer behavior, or porting Atelier to other 3D applications.

## Repository layout

```
atelier-mcp/
├── .claude/skills/         # Claude skills (5 files, trigger-based)
├── .claude-plugin/         # Plugin manifest (plugin.json, marketplace.json)
├── addon.py                # Blender addon — installs in Blender, exposes socket commands
├── commands/               # Claude plugin slash commands
├── agents/                 # Claude plugin specialized subagents
├── docs/
│   ├── OVERVIEW.md         # Product-level intro (this file's sibling)
│   ├── ARCHITECTURE.md     # ← you are here
│   ├── handbook/           # 39 cited chapters — the design knowledge base
│   └── dev/                # Internal: specs, plans, test plan
├── src/atelier/
│   ├── server.py           # MCP server — 80 @mcp.tool() registrations
│   ├── cli.py              # CLI entry point (atelier ...)
│   ├── _handbook.py        # Handbook loader (path-traversal-safe)
│   ├── _discovery.py       # 25-question bank + scoring + 19-style match
│   ├── _project.py         # Project schema + multi-space scaffold
│   ├── _snapshots.py       # Version snapshots + version log
│   ├── _gates.py           # 9-dimension quality gates with handbook citations
│   ├── _procurement.py     # SKU records + 15-vendor whitelist
│   ├── _bom.py             # BoM aggregator — markdown / CSV
│   ├── _sku_parse.py       # 1688 / Taobao / JD / Sketchfab page parser
│   ├── _moodboard.py       # Image-gen prompt builder (cites style palette)
│   ├── _style_vocab.py     # Style chapter parser → structured vocab
│   ├── _envelope.py        # Canonical {ok, data?, error?} response shape
│   ├── _errors.py          # ErrorCode enum + ToolError
│   ├── _filters.py         # Response slimming
│   ├── _phases.py          # Tool taxonomy (per phase)
│   ├── _query_guide.py     # asset_query_help cheat sheets
│   ├── telemetry.py        # Opt-in telemetry
│   └── telemetry_decorator.py
├── tests/                  # 250 tests (pure-Python, no Blender required)
├── pyproject.toml          # PyPI atelier-mcp + 3 entry points
└── README.md
```

## Layer responsibilities

| Layer | Owner | Decisions live here |
|---|---|---|
| Handbook | Markdown files in `docs/handbook/` | Design rules, all citations |
| Skills | `.claude/skills/interior-*.md` | When to invoke + which handbook chapters to load + how to instruct AI |
| Quality Gates | `src/atelier/_gates.py` | Refusal / warning thresholds (each cites a handbook chapter) |
| MCP Tools | `src/atelier/server.py` | The 80 callable surfaces; thin wrappers around the pure-Python modules |
| CLI | `src/atelier/cli.py` | Same surfaces, callable without an AI client |
| Addon | `addon.py` | Native Blender ops via `bpy` (audit scan, project scaffold, etc.) |
| Project state | `<project_root>/{project,taste-profile,procurement}.json + snapshots/` | User's design decisions, persisted as JSON sidecars |

## Key invariants

1. **Pure-Python modules contain all logic.** The MCP server tools and the CLI are both thin shims around `src/atelier/_*.py`. This guarantees feature parity between MCP and CLI surfaces without code duplication.
2. **Every quality gate cites a handbook chapter.** `_gates.py` Finding objects always have a non-empty `citation` field. `tests/test_e2e_workflow.py::test_gates_emit_handbook_citations` enforces this.
3. **No fabricated section numbers.** Handbook content is fetched via WebFetch from authoritative sources; tests scan for plausible GB/IES/IBC section markers. See `tests/test_handbook_acceptance.py::test_no_fabricated_section_markers`.
4. **Every MCP tool returns the canonical envelope.** `{ok: bool, data?: ..., error?: {code, hint, detail}}` — enforced by `_envelope.tool_envelope` decorator.
5. **`bpy` access is confined to `addon.py`.** Pure-Python modules under `src/atelier/` must never import `bpy`. This makes everything else testable without Blender.

## How a tool call flows (typical)

1. AI client (Claude/Cursor) sends `mcp__atelier__<tool>` with args
2. FastMCP dispatches to the function in `server.py`
3. The function imports + calls a pure-Python module (e.g. `_gates.run_audit`)
4. If Blender state is needed, the function calls `get_blender_connection().send_command("...", params)`
5. The addon's `_execute_command_internal` dispatches to a method on `BlenderMCPServer`
6. The method walks `bpy.data.*`, returns a JSON-serializable dict
7. Back in `server.py`, the result is wrapped via `_tool_response(...)` → canonical envelope
8. AI client receives the envelope, branches on `ok`, surfaces `error.hint` to the user if not ok

## Where to extend

| Want to | Touch |
|---|---|
| Add a new handbook chapter | `docs/handbook/<slug>.md` (run `pytest tests/test_handbook_acceptance.py` — citation density is gated) |
| Add a new style | `docs/handbook/styles/<slug>.md` + `_discovery.STYLE_VECTORS` (6-axis vector for matching) |
| Add a new MCP tool | `src/atelier/server.py` with `@mcp.tool() @telemetry_tool() @tool_envelope` |
| Add a new CLI subcommand | `src/atelier/cli.py` — extend `build_parser()` + add a `_cmd_<name>` handler |
| Add a Blender-side native command | `addon.py` — add a method on `BlenderMCPServer` + register in `_execute_command_internal` handlers |
| Add a Claude skill | `.claude/skills/interior-<name>.md` (plus add to `commands/` if it should also be a slash command) |
| Add a quality gate | `src/atelier/_gates.py` — add a `check_<name>` function + register in `GATE_FUNCTIONS` |

## Test layers

See [`dev/specs/2026-04-30-test-plan.md`](dev/specs/2026-04-30-test-plan.md). TL;DR: 250 pure-Python tests run in 2 sec; manual Blender verification for socket-touching changes.
