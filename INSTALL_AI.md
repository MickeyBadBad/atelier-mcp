# Install Atelier MCP via AI assistant

> Renamed from `blender-mcp` v2.3.0 → `atelier-mcp` v2.4.0 on 2026-04-30. CLI command is now `atelier-mcp`. Legacy alias `blender-mcp` still resolves through 2.4. The **BlenderMCP** sidebar tab inside Blender keeps its name (it's the addon's UI label, not the package name).

This document is written for an **AI agent** (Claude Code, Cursor, Codex, etc.) to walk a user through installing Atelier MCP end-to-end. The user just pastes one prompt; the AI does the rest.

---

## For users — copy-paste this prompt

> Help me install [blender-mcp](https://github.com/MickeyBadBad/atelier-mcp). Follow the [INSTALL_AI.md](https://github.com/MickeyBadBad/atelier-mcp/blob/develop/INSTALL_AI.md) playbook on the develop branch — run each step, diagnose failures, and report status before moving on. My OS is **{macOS / Linux / Windows}**. My AI client is **{Claude Code / Cursor / Claude Desktop / VS Code Copilot / OpenAI Codex}**.

That's it. The AI will handle the rest.

---

## For AI agents — playbook

You are helping a user install `blender-mcp` (the actively-maintained fork at `MickeyBadBad/atelier-mcp`). Walk through these steps **in order** and **diagnose** at each step before continuing.

### Step 0 — Survey the user's environment

Run these in parallel and **report what you find**:

```bash
which uv && uv --version || echo "uv: missing"
which python3 && python3 --version || echo "python3: missing"
which git && git --version || echo "git: missing"
ls /Applications/Blender.app 2>/dev/null && echo "Blender: installed (macOS)" \
  || ls -d ~/.config/blender/[0-9]* 2>/dev/null | tail -1 \
  || echo "Blender: not found in standard paths"
which claude 2>/dev/null && claude --version || echo "claude-code: not installed"
test -f ~/Library/Application\ Support/Claude/claude_desktop_config.json && echo "claude-desktop: config present" || true
```

**Branch on findings:**

- **No `git`** → stop and tell the user to install git first.
- **No `python3`** → stop and tell the user to install Python 3.10+ from python.org.
- **No `Blender`** → install path is unaffected, but flag that they'll need Blender 4.x or 5.x before final use; link [blender.org/download](https://www.blender.org/download/).
- **No AI client detected** → ask the user explicitly which one they're using.

### Step 1 — Install uv if missing

If `uv` was missing in Step 0:

```bash
# macOS preferred path:
brew install uv 2>/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

# Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Then ensure ~/.local/bin is on PATH:
export PATH="$HOME/.local/bin:$PATH"
```

Verify with `uv --version` before moving on.

### Step 2 — Clone the fork

```bash
INSTALL_DIR="$HOME/.blender-mcp-fork"
if [ -d "$INSTALL_DIR/.git" ]; then
    git -C "$INSTALL_DIR" pull --ff-only origin develop
else
    git clone --branch develop --depth 1 https://github.com/MickeyBadBad/atelier-mcp.git "$INSTALL_DIR"
fi
cd "$INSTALL_DIR" && uv sync
```

Verify `uv sync` exits 0. If it fails on `supabase` or any specific dep, surface the actual error to the user — don't silently retry.

### Step 3 — Register the MCP server with the user's AI client

Match on what the user said:

**Claude Code:**

```bash
claude mcp remove blender 2>/dev/null
claude mcp add -s user blender -e DISABLE_TELEMETRY=true -- \
  uv --directory "$INSTALL_DIR" run blender-mcp
claude mcp list | grep blender
```

**Cursor / VS Code / Codex** — you need to edit the user's MCP config file. Point them to the relevant docs section in the README and offer to print the JSON snippet they need to paste:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["--directory", "<INSTALL_DIR>", "run", "atelier-mcp"],
      "env": {"DISABLE_TELEMETRY": "true"}
    }
  }
}
```

**Claude Desktop** — modify `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows). Use the same JSON shape as Cursor.

### Step 4 — Install the Blender addon

The addon (`addon.py`) needs to be loaded **inside Blender**. Two paths:

**Auto-copy (preferred when Blender's user dir is reachable):**

```bash
# macOS:
BLENDER_USER_DIR=$(ls -1d "$HOME/Library/Application Support/Blender"/[0-9]* 2>/dev/null | sort -V | tail -1)

# Linux:
BLENDER_USER_DIR=$(ls -1d "$HOME/.config/blender"/[0-9]* 2>/dev/null | sort -V | tail -1)

if [ -n "$BLENDER_USER_DIR" ]; then
    mkdir -p "$BLENDER_USER_DIR/scripts/addons"
    cp "$INSTALL_DIR/addon.py" "$BLENDER_USER_DIR/scripts/addons/addon.py"
fi
```

Then tell the user to **enable the addon in Blender**:

> 1. Open Blender → **Edit → Preferences → Add-ons**
> 2. Search for "mcp" → tick the **Blender MCP** checkbox
> 3. Save preferences

**Manual install (if auto-copy didn't work):**

> 1. Open Blender → **Edit → Preferences → Add-ons**
> 2. Click **"Install..."** → pick `<INSTALL_DIR>/addon.py`
> 3. Tick the **Blender MCP** checkbox

### Step 5 — Connect Blender to the MCP server

Blender's addon runs a socket on port 9876. The user must start it:

> 1. In a 3D viewport, press <kbd>N</kbd> to open the side panel
> 2. Find the **BlenderMCP** tab
> 3. (Optional) tick **"Use assets from Poly Haven"** — free, no key
> 4. Click **"Connect to Claude"**

### Step 6 — Restart the AI client

The MCP server tools become available only after the AI client (Claude Code session, Cursor, etc.) restarts. Tell the user:

> Restart your AI client now. In Claude Code: type `/quit` and run `claude` again.

### Step 7 — Verify end-to-end

Once the user is back in a fresh AI session, the AI should call:

```
mcp__blender__get_scene_info
```

If it returns scene info with a `blender_version` field, **everything works**. If it errors with "Could not connect to Blender":

- Confirm Blender is open with the addon enabled
- Confirm "Connect to Claude" button was clicked (the panel shows "Disconnect..." when active)
- Confirm port 9876 isn't taken: `lsof -i :9876` (macOS / Linux) or `netstat -ano | findstr 9876` (Windows)

### Step 8 — Suggest a hello-world

Show off the toolkit by asking the AI to build something simple:

> "Build a small house with brick walls (`brick_wall` genre), a clay tile roof, and `warm_intimate` lighting. Frame the camera with `frame_camera_to_objects`, render at 1280×720 Cycles. Save the .blend to `scenes/hello.blend`."

This exercises about 8 tools end-to-end and gives the user a concrete result.

---

## Diagnostic checklist (for AI to run on demand)

When the user reports "something's broken", run this in order:

| Check | Command | What "good" looks like |
|---|---|---|
| uv installed | `uv --version` | `uv X.Y.Z (...)` |
| Repo cloned | `ls $HOME/.blender-mcp-fork/addon.py` | file exists |
| Python deps | `cd $HOME/.blender-mcp-fork && uv sync` | exits 0 |
| MCP server registered | `claude mcp list` (Claude Code) | shows `blender` row |
| MCP server starts | `claude mcp get blender` then check process | no health-check error |
| Addon installed | `ls "$HOME/Library/Application Support/Blender/*/scripts/addons/addon.py"` (macOS) | file exists |
| Blender running | `pgrep -fl Blender` | process exists |
| Socket open | `lsof -i :9876` (macOS) / `netstat -ano \| findstr 9876` (Win) | shows Blender |
| Tools available | call `mcp__blender__get_scene_info` | returns JSON, not "Could not connect" |

For each failing row, show the user a single specific fix — don't dump the whole list.

---

## Common failures and fixes

| Symptom | Root cause | Fix |
|---|---|---|
| `Could not connect to Blender` | Addon's socket not running | Click **Connect to Claude** in Blender's N-panel |
| `Could not connect to Blender` after Blender restart | Addon disables auto-start | Re-click **Connect to Claude** every Blender session |
| `Node type ShaderNodeSeparateRGB undefined` | Stale upstream addon — Blender 4.x removed the node | Already fixed in this fork; re-copy `addon.py` to Blender's addon dir and reload addon |
| `IncompleteRead` from Sketchfab | CDN flaky | Already fixed in this fork (retry + Range-resume) — just retry the call |
| `MCP server initialization timeout` (Claude Desktop) | First-run uvx download exceeds 60s timeout | `uv tool install atelier-mcp` once, then restart client |
| Sketchfab token disappears after Blender restart | Upstream stored in scene props | Already fixed in this fork (persistent prefs) |
| `Module not found: blender_mcp` | uv venv path wrong | `cd $INSTALL_DIR && uv sync` then restart AI client |

---

## After install — recommended next steps

1. **Save your project** — pick a working directory (e.g. `~/Projects/MyDesign/`), create a `.mcp.json` there with project-scope config so the MCP only runs in that dir.

2. **Get free API tokens** for the optional integrations:
   - [Sketchfab](https://sketchfab.com/settings/password) → API Token field — free, 80% of models are CC-licensed
   - [Hyper3D Rodin](https://hyper3d.ai/) → free trial key built into the addon (button in N-panel)
   - [Tripo3D](https://platform.tripo3d.ai/) → free 5,000-credit Game Hub grant (~$50 worth)
   - [Meshy.ai](https://www.meshy.ai/settings/api) → Pro tier required; test key `msy_dummy_api_key_for_test_mode_12345678` works for development

3. **Tour the tools** — ask your AI to call `mcp__blender__list_archviz_genres` to discover what's available.
