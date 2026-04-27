# BlenderMCP — Control Blender with Claude AI, Cursor & MCP

> **Drive Blender 4.x and 5.x from any MCP client** — Claude Code, Claude Desktop, Cursor, VS Code Copilot, Codex — using the [Model Context Protocol](https://modelcontextprotocol.io/). Build scenes, apply PBR materials, drop in Sketchfab/PolyHaven assets, generate AI 3D models with Hyper3D/Rodin, render with Cycles, all through natural-language prompts.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Blender 4.0+ / 5.x](https://img.shields.io/badge/Blender-4.x%20%7C%205.x-orange.svg)](https://www.blender.org/)
[![MCP](https://img.shields.io/badge/MCP-1.3+-purple.svg)](https://modelcontextprotocol.io/)
[![Fork status](https://img.shields.io/badge/fork-actively%20maintained-brightgreen.svg)](#about-this-fork)

---

## 🍴 About this fork

This is an **actively maintained community fork** of [`ahujasid/blender-mcp`](https://github.com/ahujasid/blender-mcp). The original project is excellent groundwork but has not merged a PR since 2026-01-23 (~3 months at time of writing), while high-quality community fixes for Blender 4.x compatibility, security, and credential persistence have been queued.

This fork ships those fixes plus design-workflow tools targeted at interior design, architectural visualization, and product viz. **No breaking changes** — drop-in replacement for the upstream package.

**Highlights vs. upstream:**

| Improvement | Source | What it fixes |
|---|---|---|
| Blender 4.0+ / 5.x compatibility | This fork | `set_texture` failing with `ShaderNodeSeparateRGB undefined` |
| Tool-docstring prompt-injection removal | This fork | Closes upstream issue #214 (security) |
| 4 design-workflow tools (v1.6) | This fork | `apply_material_color`, `place_on_ground`, `render_image`, `set_camera_view` |
| 6 generic archviz tools (v1.7) | This fork | `mesh_cleanup`, `boolean_cutout`, `frame_camera_to_objects`, `setup_lighting` (8 moods), `apply_archviz_material` (14 genres), `list_archviz_genres` |
| ambientCG integration (v1.7) | This fork | CC0 PBR library (~2000 materials) — fills PolyHaven fabric/leather/carpet gaps |
| Resilient downloads (v1.7) | This fork | Retry + Range-resume — Sketchfab IncompleteRead drops handled transparently |
| 5 geometry / IO tools (v1.8) | This fork | `scatter_on_surface`, `array_duplicate` (linear+radial), `curve_extrude_profile`, `quick_export` (GLB/FBX/OBJ/USD), `set_world_hdri_rotation` |
| Tripo3D + Meshy.ai integrations (v1.9) | This fork | 6 sync tools — text-to-3D and image-to-3D for both services, with auto-polling and auto-import |
| One-line installer + AI-driven setup (v1.9) | This fork | `curl ... \| bash` and an `INSTALL_AI.md` playbook for AI agents to install end-to-end |
| **Usage tracking + budget caps (v1.10)** | **This fork** | **Session counters + per-call cost estimates + refuse-before-burn for Tripo3D / Meshy / OpenAI** |
| **Smart routing for AI 3D (v1.10)** | **This fork** | **`generate_3d_smart(prompt, quality)` — picks the best of 4 providers based on quality target + configured services + remaining budget** |
| **OpenAI image gen (v1.10)** | **This fork** | **DALL-E 3 + gpt-image-1 for textures, mood boards, image-to-3D refs (separate API billing — not covered by ChatGPT Plus)** |
| API-credential persistence | [#235](https://github.com/ahujasid/blender-mcp/pull/235) | Sketchfab/Hyper3D tokens lost on Blender restart |
| Visual grounding verification | [#230](https://github.com/ahujasid/blender-mcp/pull/230) | "Is this furniture actually on the floor?" |
| Distinguish addon vs transport errors | [#228](https://github.com/ahujasid/blender-mcp/pull/228) | "Communication error" misdiagnosis |
| Expose Blender version in scene info | [#229](https://github.com/ahujasid/blender-mcp/pull/229) | Version-aware code generation |
| Hyper3D base64 + URL-validation fix | [#220](https://github.com/ahujasid/blender-mcp/pull/220) | Image upload to Rodin |

See the full [CHANGELOG](./CHANGELOG.md) for a per-commit breakdown.

---

## ✨ What it does

BlenderMCP exposes Blender as a set of MCP tools, so any AI client speaking the Model Context Protocol can:

- 🎨 **Create and edit scenes** — primitives, hierarchies, transforms, materials
- 🧱 **Apply PBR textures** from [PolyHaven](https://polyhaven.com/) — diffuse, normal, roughness, AO, displacement, all wired correctly
- 🪑 **Drop in 3D assets** from [Sketchfab](https://sketchfab.com/)'s 5M+ model library — search, preview, normalize-on-import
- 🌅 **Set up HDRI lighting** in one call — search and apply `belfast_sunset_puresky` and friends
- 🤖 **Generate 3D models from text/images** via [Hyper3D Rodin](https://hyper3d.ai/) and [Tencent Hunyuan3D](https://hunyuan3d.tencent.com/)
- 🎥 **Render with Cycles or EEVEE** — Filmic tone-mapping, GPU acceleration, one-line render
- 🔍 **Verify placement** — raycast samples to measure if an object is actually grounded
- 📐 **Compose cameras** — preset isometric/3-quarter/orthographic angles
- 🐍 **Run arbitrary Python** — `bpy` access for anything not covered by a dedicated tool

[Watch the original tutorial](https://www.youtube.com/watch?v=lCyQ717DuzQ) (covers upstream usage; commands work identically in this fork).

---

## 📦 Quick install

### 🪄 The one-liner (macOS / Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/MickeyBadBad/blender-mcp/develop/install.sh | bash
```

This installs `uv` if missing, clones the fork to `~/.blender-mcp-fork`, runs `uv sync`, registers the MCP server with Claude Code (or prints the JSON snippet for Cursor / Claude Desktop / VS Code), and copies `addon.py` to your Blender user-scripts directory if Blender's installed. You finish by enabling the addon inside Blender + clicking **Connect to Claude**.

> **Want your AI assistant to do it for you?** Just paste this into Claude Code / Cursor / Codex:
>
> > Help me install [blender-mcp](https://github.com/MickeyBadBad/blender-mcp). Follow the [INSTALL_AI.md](https://github.com/MickeyBadBad/blender-mcp/blob/develop/INSTALL_AI.md) playbook on the develop branch — run each step, diagnose failures, and report status before moving on. My OS is **macOS / Linux / Windows**. My AI client is **Claude Code / Cursor / Claude Desktop / VS Code Copilot / Codex**.
>
> The agent runs the diagnostic checklist, installs missing pieces, and tells you what manual steps remain. See [INSTALL_AI.md](./INSTALL_AI.md) for the full playbook.

### Manual install — 3 steps in order

> **Step 1.** Install [`uv`](https://docs.astral.sh/uv/) (Python package runner)
> **Step 2.** Configure your MCP client (Claude Code / Cursor / Claude Desktop / VS Code)
> **Step 3.** Install the Blender addon and click "Connect to Claude"

### Step 1 — Install uv

<details open>
<summary><b>macOS</b></summary>

```bash
brew install uv
```
</details>

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Then add uv to PATH (restart Claude Desktop / Cursor afterwards)
$localBin = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$localBin", "User")
```
</details>

<details>
<summary><b>Linux</b></summary>

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
</details>

> ⚠️ **Do not skip this** — every MCP client below shells out to `uv` to launch the server.

### Step 2 — Configure your MCP client

Pick one (or more — but **only run one at a time** to avoid port conflicts on `9876`).

> 🍴 **Using this fork?** Replace `uvx blender-mcp` with `uvx --from git+https://github.com/MickeyBadBad/blender-mcp@develop blender-mcp` in any of the snippets below to install directly from this repository instead of the upstream PyPI package. Once we publish the fork to PyPI as `blender-mcp-fork`, the snippets here will be updated.

<details open>
<summary><b>Claude Code (CLI)</b></summary>

```bash
# Project-scoped (creates .mcp.json in current dir)
claude mcp add -s project blender -- uvx blender-mcp

# Or user-scoped (available everywhere)
claude mcp add -s user blender -- uvx blender-mcp

# Verify
claude mcp list
```
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Settings → Developer → Edit Config → `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```
</details>

<details>
<summary><b>Cursor</b></summary>

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/link/mcp%2Finstall?name=blender&config=eyJjb21tYW5kIjoidXZ4IGJsZW5kZXItbWNwIn0%3D)

Or manually — **macOS/Linux**: Settings → MCP → Add new global MCP server, paste:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```

**Windows** (Settings → MCP → Add Server):

```json
{
  "mcpServers": {
    "blender": {
      "command": "cmd",
      "args": ["/c", "uvx", "blender-mcp"]
    }
  }
}
```

[Cursor setup video](https://www.youtube.com/watch?v=wgWsJshecac)
</details>

<details>
<summary><b>VS Code (Copilot Chat)</b></summary>

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_blender--mcp_server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=ffffff)](vscode:mcp/install?%7B%22name%22%3A%22blender-mcp%22%2C%22type%22%3A%22stdio%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22blender-mcp%22%5D%7D)

Click the badge above (requires VS Code 1.96+ with MCP support enabled).
</details>

<details>
<summary><b>OpenAI Codex / GitHub Copilot CLI</b></summary>

```bash
codex mcp add blender -- uvx blender-mcp
```
</details>

### Step 3 — Install the Blender addon

The MCP server (Step 2) is one half. The other half is a Blender addon that runs a socket server inside Blender on port 9876. **Both must be running** for the integration to work.

1. Download [`addon.py`](./addon.py) from this repo (or `git clone` the whole thing)
2. In Blender: **Edit → Preferences → Add-ons → Install...** → pick `addon.py`
3. Tick the checkbox next to **"Interface: Blender MCP"**
4. In a 3D viewport, press <kbd>N</kbd> to open the sidebar → find the **BlenderMCP** tab
5. (Optional but recommended) Tick **Use assets from Poly Haven** and **Use Hyper3D Rodin 3D model generation** — both have free trial keys built in
6. Click **Connect to Claude**

![BlenderMCP in the sidebar](assets/addon-instructions.png)

That's it — your AI client should now show a hammer 🔨 icon with `mcp__blender__*` tools available.

> 💡 **Existing user upgrading?** Replace your old `addon.py` with the latest one, then in Blender: Disable → Re-enable the addon → click Connect to Claude again.

---

## 🛠️ Tools reference

### Scene introspection
| Tool | What it does |
|---|---|
| `get_scene_info` | Lists scene objects, materials count, **Blender version** |
| `get_object_info` | Detailed info on one object — type, transform, dimensions, materials |
| `get_viewport_screenshot` | Capture the 3D viewport (or render an **orthographic diagnostic shot** of any object) |
| `verify_object_grounded` | Raycast-sample the gap between an object and a ground mesh; walks hierarchy |

### Materials & color
| Tool | What it does |
|---|---|
| **`apply_archviz_material`** | 🆕 v1.7 — pick a PBR material by generic genre keyword (`hardwood_floor`, `brick_wall`, `concrete_smooth`, `metal_industrial`, ...) — auto-downloads + applies via PolyHaven |
| **`list_archviz_genres`** | 🆕 v1.7 — discover all available genres + candidate asset IDs |
| `apply_material_color` | Apply a single Principled BSDF tinted to a hex color, with optional emission |
| `set_texture` | Apply a downloaded PolyHaven PBR texture to an object (Blender 5.x compatible) |

### Geometry helpers
| Tool | What it does |
|---|---|
| **`scatter_on_surface`** | 🆕 v1.8 — area-weighted random placement of objects on a surface (books, bottles, gravel, foliage) |
| **`array_duplicate`** | 🆕 v1.8 — linear or radial duplication via Array modifier (pendant rows, radial seating) |
| **`curve_extrude_profile`** | 🆕 v1.8 — Bezier curve + bevel for neon, pipes, railings, decorative trim |
| `mesh_cleanup` | v1.7 — merge dups + recalc normals + decimate + remove loose; LiDAR/scan preprocessing |
| `boolean_cutout` | v1.7 — windows / door cutouts / vent holes via primitive or mesh boolean |
| `place_on_ground` | Translate an object so its bbox bottom sits on a target z; walks hierarchy |

### Camera, lighting & render
| Tool | What it does |
|---|---|
| **`set_world_hdri_rotation`** | 🆕 v1.8 — rotate the world HDRI around Z + adjust strength (no re-download for time-of-day shifts) |
| `frame_camera_to_objects` | v1.7 — fit camera to objects with composition presets (thirds, center) and DOF; uses lens shift to keep verticals straight |
| `setup_lighting` | v1.7 — three-layer rig tuned to 8 generic moods (`warm_intimate`, `daylight_neutral`, `bright_workspace`, `dramatic_accent`, `golden_hour`, `cool_modern`, `studio_neutral`, `moody_lowkey`) |
| `set_camera_view` | Position the active camera using preset angles (front/back/left/right/top/3q/iso) |
| `render_image` | One-call Cycles/EEVEE render with Filmic tone-mapping |

### Asset libraries
| Tool | What it does |
|---|---|
| **`search_ambientcg_assets`** | 🆕 v1.7 — search [ambientCG](https://ambientcg.com/) (CC0, ~2000 materials, fills PolyHaven fabric/leather gaps) |
| **`download_ambientcg_asset`** | 🆕 v1.7 — download + extract + apply ambientCG material zip |
| **`get_ambientcg_status`** | 🆕 v1.7 — connectivity check |
| `search_polyhaven_assets` | Search PolyHaven HDRIs / textures / models by category |
| `download_polyhaven_asset` | Download and import a PolyHaven asset |
| `get_polyhaven_categories` | List PolyHaven categories for an asset type |
| `search_sketchfab_models` | Search Sketchfab's model catalog |
| `get_sketchfab_model_preview` | Get a preview thumbnail before downloading |
| `download_sketchfab_model` | Import a Sketchfab model, normalized to a target size |

### AI 3D generation
| Tool | What it does |
|---|---|
| **`generate_3d_smart`** | 🆕 v1.10 — auto-pick best provider by quality tier + budget. **Use this when you don't care which provider runs.** |
| **`get_usage_report`** | 🆕 v1.10 — current session credits/$ spent + caps + live Tripo3D balance |
| **`set_usage_budget`** | 🆕 v1.10 — adjust per-session cap for Tripo3D / Meshy / OpenAI |
| **`reset_usage_counters`** | 🆕 v1.10 — start a fresh sprint without re-registering addon |
| **`generate_image_openai`** | 🆕 v1.10 — DALL-E 3 / gpt-image-1 → PNG (refs, textures, mood boards) |
| **`get_openai_status`** | 🆕 v1.10 — check OpenAI API key + connectivity |
| `generate_tripo3d_text_to_3d` | v1.9 — text-to-3D via [Tripo3D](https://www.tripo3d.ai/) (sync, auto-polling, full PBR) |
| **`generate_tripo3d_image_to_3d`** | 🆕 v1.9 — image-to-3D via Tripo3D (image_url) |
| **`generate_meshy_text_to_3d`** | 🆕 v1.9 — text-to-3D via [Meshy.ai](https://www.meshy.ai/) (preview + refine, sync) |
| **`generate_meshy_image_to_3d`** | 🆕 v1.9 — image-to-3D via Meshy.ai (URL or base64 data URI) |
| **`get_tripo3d_status`** | 🆕 v1.9 — check Tripo3D credit balance |
| **`get_meshy_status`** | 🆕 v1.9 — check Meshy.ai connectivity |
| `generate_hyper3d_model_via_text` | Generate a 3D model from a text prompt (Hyper3D Rodin) |
| `generate_hyper3d_model_via_images` | Generate a 3D model from reference images (Hyper3D Rodin) |
| `generate_hunyuan3d_model` | Generate a 3D model via Tencent Hunyuan3D |

### Export & escape hatch
| Tool | What it does |
|---|---|
| **`quick_export`** | 🆕 v1.8 — single-call GLB / FBX / OBJ / USD / USDZ export with packed textures & Draco compression |
| `execute_blender_code` | Run arbitrary Python with `bpy` access (powerful — see [security](#-security)) |
| `get_*_status` | Status checks for each integration (PolyHaven / Sketchfab / Hyper3D / Hunyuan3D / ambientCG) |

> **All downloads are now resilient** — every asset library call goes through a retry-with-backoff layer (4 attempts, exponential delay) plus Range-based resume for partial transfers. Sketchfab CDN drops mid-stream are handled transparently as of v1.7.

---

## 💡 Use cases

The tools were designed against real workflows. Some examples that exercise the full kit:

### 🏠 Interior design / architectural visualization

> **"Build a speakeasy lounge interior — 4.8m wide × 10m deep × 3.8m ceiling — with deep emerald walls (#1a3a2e), retro purple accent door (#3d2449), brushed brass details, dark walnut SPC floor, amber 2400K lighting, and a black Chesterfield sofa from Sketchfab."**

This single prompt exercises: `apply_material_color` (walls, door), `set_texture` (PolyHaven brick + wood), `download_sketchfab_model` (sofa), `place_on_ground` (sofa positioning), `download_polyhaven_asset` (HDRI), `set_camera_view` (3q hero shot), `render_image` (Cycles + Filmic).

### 🪑 Product visualization

> "Take this Sketchfab chair, ground it on the floor, light it like a studio at 2700K, render front/left/iso/top orthographic shots for a spec sheet."

Exercises: `download_sketchfab_model`, `place_on_ground`, `set_camera_view` (4 angles), `render_image`, `get_viewport_screenshot(target_object=..., view=...)` for clean diagnostic shots.

### 🎮 Game dev / proxy scene

> "Block out a low-poly forest with 8 random pine trees, 12 rocks, dirt ground from PolyHaven, sunset HDRI."

Exercises: procedural placement via `execute_blender_code`, `download_sketchfab_model` (assets), `place_on_ground`, `download_polyhaven_asset` (HDRI + dirt texture).

### 🛠️ Verification

> "Did all the chairs in scene actually land on the floor or are they floating?"

Exercises: `verify_object_grounded` per chair, return median/max gap with `sampled_meshes` so you can see exactly which subassemblies were tested.

---

## 🔑 Persistent API credentials

Sketchfab requires a free API token; Hyper3D Rodin has a built-in trial key plus paid plans; Hunyuan3D needs Tencent Cloud credentials. **As of [#235](https://github.com/ahujasid/blender-mcp/pull/235), all credentials persist across Blender restarts** via Add-on Preferences:

`Edit → Preferences → Add-ons → Blender MCP`

Or via environment variables (useful for CI / headless setups):

```
BLENDERMCP_SKETCHFAB_API_KEY=...
BLENDERMCP_HYPER3D_API_KEY=...
BLENDERMCP_HUNYUAN3D_SECRET_ID=...
BLENDERMCP_HUNYUAN3D_SECRET_KEY=...
BLENDERMCP_HUNYUAN3D_API_URL=...
```

Lookup order: **Add-on Preferences → Scene properties → environment variable**. Existing scene-based setups still work.

---

## 🌐 Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `BLENDER_HOST` | `localhost` | Host for the in-Blender socket server |
| `BLENDER_PORT` | `9876` | Port for the in-Blender socket server |
| `DISABLE_TELEMETRY` | unset | Set to `true` to fully disable telemetry |
| `BLENDERMCP_SKETCHFAB_API_KEY` | unset | Sketchfab API token |
| `BLENDERMCP_HYPER3D_API_KEY` | unset | Hyper3D Rodin API key |
| `BLENDERMCP_HUNYUAN3D_SECRET_ID` | unset | Tencent Cloud SecretId |
| `BLENDERMCP_HUNYUAN3D_SECRET_KEY` | unset | Tencent Cloud SecretKey |
| `BLENDERMCP_HUNYUAN3D_API_URL` | `http://localhost:8081` | Hunyuan3D API endpoint |
| `BLENDERMCP_TRIPO3D_API_KEY` | unset | Tripo3D API key (`tsk_...`) |
| `BLENDERMCP_MESHY_API_KEY` | unset | Meshy.ai API key (`msy_...`) |

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---|---|
| **Could not connect to Blender** | The Blender addon's socket isn't running. In Blender N-panel → BlenderMCP → click **Connect to Claude**. Verify `lsof -i :9876` (macOS/Linux) shows Blender. |
| **`Node type ShaderNodeSeparateRGB undefined`** on `set_texture` | You're on stock upstream + Blender 4.x or 5.x. Switch to this fork (already patched), or wait for [#236](https://github.com/ahujasid/blender-mcp/pull/236) to merge. |
| **Sketchfab token lost after Blender restart** | You're on stock upstream. Switch to this fork ([#235](https://github.com/ahujasid/blender-mcp/pull/235) integrated). |
| **`Communication error: ...`** when really it's a code error | Switch to this fork ([#228](https://github.com/ahujasid/blender-mcp/pull/228) integrated — gives "Blender Python error: ..." instead). |
| **Hyper3D image upload fails** | Switch to this fork ([#220](https://github.com/ahujasid/blender-mcp/pull/220) integrated — base64 decode + real URL validation). |
| **MCP server initialization timeout** | Pre-cache deps once: `uvx blender-mcp --help`. Or `uv tool install blender-mcp` for a permanent install. |
| **Sketchfab download `IncompleteRead`** | CDN is flaky for some specific UIDs. Retry, or pick a smaller model from search results. |
| **Have you tried turning it off and on again?** | Disable the addon in Blender → re-enable → click Connect to Claude → restart your AI client. |

---

## 🔒 Security

- **`execute_blender_code` runs arbitrary Python.** It has full `bpy` and `__builtins__` access, including `os`, `subprocess`, file IO, and network. Treat the MCP server as a privileged process — don't expose it to untrusted networks. **Always save your `.blend` file before invoking it.**
- **Save your work before any session.** Bugs in generated code can corrupt the scene.
- **Tool docstrings as prompts.** MCP injects tool docstrings verbatim into the LLM prompt. The fork removed two upstream lines that contained hidden steering directives ([#214](https://github.com/ahujasid/blender-mcp/issues/214)). Audit any third-party MCP server's tool docstrings before trusting them.
- **API tokens.** Persistent credentials are stored in Blender's Add-on Preferences (per the OS user). Don't commit `.blend` files containing scene-property tokens.

---

## 📊 Telemetry

The fork inherits anonymous-by-default telemetry from upstream. Two ways to opt out:

1. **In Blender** — Edit → Preferences → Add-ons → Blender MCP → uncheck the consent box. Reduces collection to tool name / success / duration only.
2. **Fully disable** — set `DISABLE_TELEMETRY=true` in your MCP client config:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"],
      "env": { "DISABLE_TELEMETRY": "true" }
    }
  }
}
```

The fork's project-scope `.mcp.json` examples include `DISABLE_TELEMETRY=true` by default.

---

## 🧬 Architecture

```
┌──────────────────┐    stdio    ┌─────────────────┐    TCP 9876    ┌────────────────┐
│  AI client       │  ◄──────►   │  MCP server     │  ◄──────────►  │  Blender addon │
│  (Claude / etc.) │   JSON-RPC  │  (uvx-launched) │  JSON commands │  (socket srv)  │
└──────────────────┘             └─────────────────┘                └────────────────┘
                                  src/blender_mcp/                   addon.py
                                    server.py                        (runs in Blender)
```

- **MCP server** (`src/blender_mcp/server.py`) — speaks MCP to the AI client, forwards each tool call to the addon as a JSON command over a TCP socket. ~1200 lines.
- **Blender addon** (`addon.py`) — registers a Blender plugin that runs a socket server on port 9876. Receives JSON commands and dispatches to handler methods that touch `bpy`. ~2900 lines.
- **Communication** — newline-free JSON over TCP, with a chunk-aggregating receiver to handle large payloads (screenshots, scene info).

---

## 🤝 Contributing

PRs welcome. The fork's policy:

1. **Bug fixes and Blender-version compat patches**: merge fast.
2. **New tools**: open an issue first to discuss scope. We aim for tools that wrap a high-frequency operation (multiple chained `bpy` calls become 1 tool call).
3. **Cherry-picks from upstream**: very welcome — many upstream PRs sit unreviewed for months. If you tested one in Blender 4.x or 5.x, drop it here too.
4. **Style**: follow the existing dispatcher pattern in `addon.py` (`_execute_command_internal` handlers) and `@mcp.tool()` wrappers in `server.py`. Add docstrings — they're surfaced to LLMs.

For non-trivial changes, please run:

```bash
python -m py_compile addon.py src/blender_mcp/server.py
```

We don't yet have a test suite — please describe manual test steps in the PR.

---

## 📜 License & credits

MIT, see [LICENSE](./LICENSE).

- **Original work** © 2025 Siddharth Ahuja, [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)
- **Fork maintenance & new tools** © 2026 BlenderMCP Fork Maintainers
- **Community PRs integrated** — credits to @shangdi178, @obselate, @0xghXst (see [CHANGELOG](./CHANGELOG.md))

This is a third-party integration and is not made by or affiliated with Blender Foundation, Anthropic, Cursor, or any other named platform.

We have **no official website**. Any site claiming to be the official Blender MCP project is unaffiliated.
