#!/usr/bin/env bash
# blender-mcp fork installer (macOS / Linux)
#
# One-liner usage:
#   curl -fsSL https://raw.githubusercontent.com/MickeyBadBad/blender-mcp/develop/install.sh | bash
#
# What it does:
#   1. Installs uv if missing
#   2. Clones the fork into ~/.blender-mcp-fork (or pulls latest)
#   3. Runs uv sync inside the clone
#   4. Detects your AI client (claude-code / cursor / claude-desktop / vscode)
#      and adds the MCP server config
#   5. Copies addon.py to your Blender user-scripts directory if Blender's
#      installed
#   6. Prints final manual steps (enable addon + Connect to Claude)

set -euo pipefail

# ---------- pretty output ----------
GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; NC='\033[0m'; BOLD='\033[1m'
log()   { printf "${GREEN}[blender-mcp]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[blender-mcp]${NC} %s\n" "$*" >&2; }
err()   { printf "${RED}[blender-mcp]${NC} %s\n" "$*" >&2; exit 1; }
step()  { printf "${BOLD}\n→ %s${NC}\n" "$*"; }

REPO_URL="${BLENDERMCP_REPO_URL:-https://github.com/MickeyBadBad/blender-mcp.git}"
REPO_BRANCH="${BLENDERMCP_REPO_BRANCH:-develop}"
INSTALL_DIR="${BLENDERMCP_INSTALL_DIR:-$HOME/.blender-mcp-fork}"

# ---------- detect OS ----------
case "$(uname -s)" in
    Darwin)  OS="macos";;
    Linux)   OS="linux";;
    *)       err "Unsupported OS: $(uname -s). Try install.ps1 on Windows.";;
esac
log "Detected OS: $OS"

# ---------- 1. install uv ----------
step "Step 1/6 — checking uv"
if ! command -v uv >/dev/null 2>&1; then
    warn "uv not found. Installing..."
    if [ "$OS" = "macos" ] && command -v brew >/dev/null 2>&1; then
        brew install uv
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # uv installs to ~/.local/bin by default
        export PATH="$HOME/.local/bin:$PATH"
    fi
    command -v uv >/dev/null 2>&1 || err "uv installation failed. Install manually from https://docs.astral.sh/uv/"
fi
log "uv: $(uv --version)"

# ---------- 2. clone or pull repo ----------
step "Step 2/6 — fetching blender-mcp fork"
if [ -d "$INSTALL_DIR/.git" ]; then
    log "Repo exists at $INSTALL_DIR — pulling latest"
    git -C "$INSTALL_DIR" fetch --all --prune
    git -C "$INSTALL_DIR" checkout "$REPO_BRANCH"
    git -C "$INSTALL_DIR" pull --ff-only origin "$REPO_BRANCH"
else
    log "Cloning $REPO_URL → $INSTALL_DIR"
    git clone --branch "$REPO_BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

# ---------- 3. uv sync ----------
step "Step 3/6 — installing Python deps (uv sync)"
( cd "$INSTALL_DIR" && uv sync )
log "Python env ready"

# ---------- 4. detect & configure AI client ----------
step "Step 4/6 — configuring MCP client"
configured_client=""

# Helper to register with claude-code
register_claude_code() {
    if command -v claude >/dev/null 2>&1; then
        log "Found Claude Code CLI — registering MCP server (user scope)"
        # Idempotent: remove first if exists
        claude mcp remove blender 2>/dev/null || true
        claude mcp add -s user blender -e DISABLE_TELEMETRY=true -- \
            uv --directory "$INSTALL_DIR" run blender-mcp
        configured_client="claude-code"
        return 0
    fi
    return 1
}

# Helper for Claude Desktop config
register_claude_desktop() {
    local cfg
    if [ "$OS" = "macos" ]; then
        cfg="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    else
        cfg="$HOME/.config/Claude/claude_desktop_config.json"
    fi
    [ -f "$cfg" ] || return 1
    log "Found Claude Desktop config — adding manual entry suggestion"
    cat <<EOF

  Add this to ${cfg} (under mcpServers):
  {
    "blender": {
      "command": "uv",
      "args": ["--directory", "$INSTALL_DIR", "run", "blender-mcp"],
      "env": {"DISABLE_TELEMETRY": "true"}
    }
  }
EOF
    configured_client="claude-desktop"
    return 0
}

if register_claude_code; then
    :
elif register_claude_desktop; then
    :
else
    warn "No supported AI client detected automatically."
    cat <<EOF

  Manual config — add to your MCP client (Cursor / VS Code / Codex / etc.):
    command: uv
    args:    --directory $INSTALL_DIR run blender-mcp
    env:     DISABLE_TELEMETRY=true
EOF
fi

# ---------- 5. install Blender addon ----------
step "Step 5/6 — looking for Blender"
BLENDER_USER_DIR=""
if [ "$OS" = "macos" ]; then
    # Find the most recent ~/Library/Application Support/Blender/X.Y/
    if [ -d "$HOME/Library/Application Support/Blender" ]; then
        BLENDER_USER_DIR=$(ls -1d "$HOME/Library/Application Support/Blender"/[0-9]* 2>/dev/null | sort -V | tail -1 || true)
    fi
elif [ "$OS" = "linux" ]; then
    if [ -d "$HOME/.config/blender" ]; then
        BLENDER_USER_DIR=$(ls -1d "$HOME/.config/blender"/[0-9]* 2>/dev/null | sort -V | tail -1 || true)
    fi
fi

if [ -n "$BLENDER_USER_DIR" ] && [ -d "$BLENDER_USER_DIR" ]; then
    addons_dir="$BLENDER_USER_DIR/scripts/addons"
    mkdir -p "$addons_dir"
    cp "$INSTALL_DIR/addon.py" "$addons_dir/addon.py"
    log "Copied addon.py → $addons_dir/addon.py"
    log "Blender version detected: $(basename "$BLENDER_USER_DIR")"
else
    warn "Couldn't auto-detect Blender's user-scripts directory."
    warn "After installing Blender, manually install $INSTALL_DIR/addon.py via:"
    warn "  Edit > Preferences > Add-ons > Install... → pick addon.py"
fi

# ---------- 6. final instructions ----------
step "Step 6/6 — final manual steps"
cat <<EOF

  ${BOLD}Almost done.${NC} Two things you still need to do:

  1. ${BOLD}Open Blender${NC} → Edit → Preferences → Add-ons
     - Find "Blender MCP" (search for 'mcp')
     - Tick the checkbox to enable it
     - (If not auto-installed, click "Install..." and pick:
        $INSTALL_DIR/addon.py)

  2. ${BOLD}In a Blender 3D viewport${NC}: press N → BlenderMCP tab
     - (Optional) tick "Use assets from Poly Haven", Sketchfab, etc.
     - Click "Connect to Claude"

  3. Restart your AI client (claude-code, Cursor, etc.) so it picks up
     the new MCP server.

  Then ask your AI:
     "Test the Blender MCP — call get_scene_info"

  Configured for: ${configured_client:-manual}
  Repo:           $INSTALL_DIR (branch: $REPO_BRANCH)
  Docs:           https://github.com/MickeyBadBad/blender-mcp

EOF
log "Done."
