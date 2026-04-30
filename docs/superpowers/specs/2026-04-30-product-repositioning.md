# Atelier Product Repositioning — Decisions Notes

> Not a formal spec — this is the decisions record for the v2.4.0 → v2.5.0 repositioning pass. The user explicitly delegated execution ("你先自己考虑好，然后执行就可以"), so this document captures the reasoning so they can review the path after the fact.

## Why repositioning now

Three forces converged this week:

1. **Anthropic's official Blender connector** (2026-04-28) — `ahujasid/blender-mcp` v1.4.0 packaged into Claude Desktop's connector marketplace. The "Blender × Claude × MCP" positioning is now occupied by the official path.
2. **Our actual product surface outgrew the framing** — by v2.4.0 we have 39 handbook chapters (4400+ lines, all sourced + cited), 5 Claude skills, 80 MCP tools, 9-dimension quality gates with handbook citation enforcement, a 25-question Discovery questionnaire, procurement + BoM tooling, moodboard prompt builder, native addon commands. "Blender MCP server" is no longer an honest description.
3. **User's explicit signal** — "MCP 只是作为项目的一个特点，我们需要 skills rules 等做一个 AI 辅助的完整的 interior design 的工具，可能更像是一个 SuperPowers 的工具集"

## What the user picked

A → B → C → D → E in order. All five concerns are real; treat them as five passes of one repositioning.

| | Concern | What it means concretely |
|---|---|---|
| A | Reach | MCP-only locks us out of users without Claude/Cursor. Need a CLI mode that runs without an MCP client at all. |
| B | Tone | Top-of-README must read like a design product, not a developer library. |
| C | Scope | Handbook + skills + workflow >> MCP. Restructure docs so handbook is a top-level asset, MCP appears further down. |
| D | Distribution | Become a Claude plugin per the SuperPowers / Anthropic plugin format (`.claude-plugin/plugin.json` + skills/ commands/ agents/ at top level). One-click install via Claude plugin manager. |
| E | Identity | Explicit "Why Atelier vs the official Blender connector" section + GitHub repo rename + topics/description. |

## Architectural decisions

### A. CLI

- New module `src/atelier/cli.py`
- Subcommands wrap existing pure-Python modules (no logic duplication):
  - `atelier init <project_name> --type <residential_apartment|cafe_lounge|...>` — calls `_project.new_project_record` + `_project.write_project`
  - `atelier discover [--depth quick|standard|deep|adaptive]` — runs `_discovery.list_questions` interactively, calls `_discovery.score_answers`
  - `atelier audit <scene_info_json> [--mode hero|exploration|construction]` — calls `_gates.run_audit`
  - `atelier bom <project_root> [--format markdown|csv]` — calls `_bom.collect_bom_rows` + render
  - `atelier moodboard <project_root> [--style <slug>] [-n 4]` — calls `_moodboard.build_moodboard_prompts` + `_style_vocab.parse_style_chapter`
  - `atelier handbook [<chapter>] [--query <q>]` — calls `_handbook` module
  - `atelier styles` — list available styles
- New entry point `atelier = "atelier.cli:main"` (alongside `atelier-mcp = "atelier.server:main"` and legacy `blender-mcp`)
- No new tests required — every command thin-wraps an already-tested pure-Python function. Add one smoke test that invokes each subcommand once via `argparse.parse_args` to catch wiring breakage.

### B. README rebrand

- New top section: 1-line tagline + 3-bullet "what you can do" + 3-bullet "who it's for"
- Move "Highlights vs upstream" table further down
- Replace "BlenderMCP exposes Blender as a set of MCP tools" with workflow-first language
- Add a "Why Atelier?" section near the top covering the project's distinctive value prop (handbook-grounded + citation policy + zero-design-knowledge-assumed)

### C. Docs nav

- Promote `docs/handbook/` to be a navigable asset with its own README and topical index
- Add `docs/OVERVIEW.md` — the 5-layer architecture explained for a non-technical reader
- Add `docs/ARCHITECTURE.md` — for technical readers who want to understand the code layout
- Move `docs/superpowers/` → `docs/dev/` (it's developer-internal stuff; rename also avoids confusion with the SuperPowers plugin)
- Result: `docs/handbook/`, `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `docs/dev/` (specs + plans)

### D. Claude plugin format

Cleanest path: this same repo IS the plugin. Add at root:

- `.claude-plugin/plugin.json` — Anthropic plugin manifest (name, description, version, author, repo, license, keywords). Format observed from cached SuperPowers + code-review plugins.
- `.claude-plugin/marketplace.json` — optional, can be added later if we want to publish to a marketplace
- `commands/` — slash commands at top-level (move/copy from elsewhere as needed)
  - `/atelier-start` — start a new project (calls discovery + project init)
  - `/atelier-style` — moodboard candidates + lock
  - `/atelier-edit` — plain-language scene edits
  - `/atelier-render` — render with audit gates
  - `/atelier-handoff` — final renders + BoM + audit report
- `agents/` — specialized subagents
  - `interior-designer` — the canonical design subagent that absorbs the handbook + style chapter for a project
  - `style-historian` — for "tell me about <style>" deep-dives, cites real published projects
- `skills/` — move from `.claude/skills/` to top-level `skills/` (so plugin manifest can find them at the canonical path)
- `mcpServers` field in plugin.json or a separate `.mcp.json` — declares the MCP server used by the plugin (`atelier-mcp` via uvx)

The PyPI distribution stays — the plugin uses the PyPI MCP server. The plugin layer adds skills/commands/agents on top.

### E. Identity

- Add to README: "Why Atelier vs the official Anthropic Blender connector" section. Should be short (5-6 bullets), neutral in tone, and link to both docs.
- GitHub repo: rename `MickeyBadBad/blender-mcp` → `MickeyBadBad/atelier-mcp` via `gh repo rename`. GitHub auto-redirects old URLs.
- Update install URLs across README, INSTALL_AI.md, install.sh
- GitHub repo description + topics — refresh to match the new positioning (interior-design, AI-assistant, Blender-MCP, claude-plugin)

## Out of scope for this pass

- New skills / agents / commands content — placeholder MVPs only; deeper specialized agents (style-historian, etc.) get their own slice later
- Web / mobile companion — A's CLI mode is the reach delta this round; web is a much bigger project
- Pricing / monetization — too early
- Marketplace publishing — local plugin install via path is enough; marketplace listing later
- Slice 7 (PDF construction docs) — still queued; this repositioning doesn't replace it

## Sequence

1. Write this notes doc (you are reading it)
2. Pass A — CLI
3. Pass B — README rebrand
4. Pass C — docs nav
5. Pass D — plugin format
6. Pass E — identity + repo rename
7. Bump v2.5.0+fork.1, full CHANGELOG entry, tag, push
8. Hand back with a summary

Each pass is a single atomic commit so the user can review one concern at a time on GitHub.

## Verification gate

- All 235 existing tests must continue to pass
- New CLI smoke test must pass (wiring correctness)
- `uvx atelier` runs at least one subcommand end-to-end
- `gh repo rename` succeeds and `gh repo view` shows the new URL
- README opens with brand language, not protocol language
