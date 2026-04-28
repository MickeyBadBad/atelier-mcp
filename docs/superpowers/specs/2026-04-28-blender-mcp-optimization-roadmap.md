# blender-mcp fork — optimization roadmap (post-v1.10.2 audit)

**Date:** 2026-04-28
**Audit scope:** v1.10.2+fork.1, 56 `@mcp.tool()` definitions, 6428-line addon.py, 8 service integrations
**Audit method:** 6 parallel research agents, one per dimension (A/B/E/C/F/D), 50 findings synthesized
**Decision authority:** project owner (MickeyBadBad)

## Goal

Take the fork from "feature-rich but rough around the edges" to "a tool an LLM agent can drive with confidence and a designer can ship pro-quality renders from on day one." Optimize across six dimensions in this priority order: **A** LLM-driveability → **F** discoverability/UX → **B** output quality → **C** cost efficiency → **D** performance → **E** maintainability.

The audit produced 50 findings. ~70% cluster into 5 cross-cutting themes; the rest are independent quick wins.

## Cross-cutting clusters

Each cluster is a single coherent change that resolves multiple findings.

### C1. Error envelope unification (A5 + E3 + F6)

Every `@mcp.tool()` returns the same JSON shape:

```json
{"ok": true,  "data": {...}}
{"ok": false, "error": {"code": "NO_API_KEY", "hint": "...", "detail": "..."}}
```

Error `code` is a closed enum: `NO_API_KEY`, `RATE_LIMITED`, `NETWORK`, `BAD_INPUT`, `STATE_REQUIRED`, `NOT_FOUND`, `INTERNAL`. The LLM client can branch on `code` for retry/recovery; humans get an actionable `hint`.

A `_tool_response()` helper plus a small decorator (`@tool_envelope`) applies the shape uniformly. **BC-break: option B** — every legacy `Error: ...` string return migrates in one pass.

### C2. Service registry abstraction (E1 + E2 + F4)

Replace ~500 lines of copy-paste boilerplate (one `get_*_status` per integration, etc.) with a declarative service spec:

```python
SERVICES = [
    Service(name="ambientcg", needs_key=False,
            tools=["status", "search", "download"]),
    Service(name="tripo3d", needs_key=True, key_pref="tripo3d_api_key",
            tools=["status", "generate_text_to_3d", "generate_image_to_3d"]),
    ...
]
```

The N-panel auto-renders sections from `SERVICES` (grouped by `needs_key` tier), the dispatcher auto-registers handlers, and adding service #11 becomes a 10-line config entry. The 6428-line god-class `BlenderMCPServer` splits into `addon/__init__.py` shim + `addon/_server.py` (socket/dispatch, ~600 lines) + `addon/services/<name>.py` per integration.

**Constraint:** the user-facing install path stays "drop one zip into Blender's addon installer." Single-file install.py becomes a stub that imports modules from a zip-bundled package.

### C3. Smart router 2.0 (A2 + A4 + A7 + B5 + B8 + C2)

Fix five bugs and add one feature in `generate_3d_smart`:

1. Hyper3D / Hunyuan3D no longer silently bails — actually invokes the legacy create-poll-import flow internally.
2. Cost estimates calibrated to median observed cost (Tripo3D `best` 6 not 10; Meshy refined 40 not "fast=20"). Selection respects `max_credits` accurately.
3. Provider-mode discriminators (Rodin `MAIN_SITE` vs `FAL_AI`, Hunyuan `OFFICIAL` vs `LOCAL`) hide inside the addon — the LLM gets one opaque `job_handle`, never sees mode strings.
4. Adds `reference_image_path` parameter; routes to provider's image-to-3D variant when set.
5. Model version discovery: queries Tripo3D / Meshy at session start for current model list; quality-tier mapping picks highest-quality available, no hardcoded date strings.
6. Prompt-hash deduplication: identical generation request within last 10 minutes returns cached result with `cache_hit: true` flag, doesn't re-burn credits.

### C4. Render quality overhaul (B1 + B2 + B3 + B6 + B7 + B9 + B10)

Seven render-quality bugs that compound in every hero shot today:

| Fix | Before | After |
|---|---|---|
| UV scale actually applies | `uv_scale_hint` returned but ignored — every brick wall is one giant brick | `apply_archviz_material` writes `Mapping.Scale` from `spec["uv_scale"]` |
| Light energy formula | Treats Blender Watts as lux (off by ~100×) | Real conversion via `lux × 0.0146 × area_m²` |
| Kelvin → RGB | Hand-rolled linear lerp (warm light reads too red) | `ShaderNodeBlackbody` driving light color |
| Normal map DX/GL | Random which gets picked, no green-channel flip | Always prefer `nor_gl`; if only `nor_dx`, invert green via Color node |
| Render presets | One-size-fits-all (64 spp, Filmic, Medium-High) | `'preview' / 'hero' / 'elevation' / 'detail'` presets bundled with `render_image` |
| Lighting moods | Lux values disagree with IES/WELL | Cross-checked against IES Lighting Handbook §13 / WELL v2 §L1 |
| White balance | Always 6500K (warm-light scenes look orange) | `render_image(white_balance_kelvin=2700)` exposes Blender 4.4's `view_settings.white_balance_temperature` |

### C5. Async + cache layer (D1 + D4 + D7 + D8 + C1 + C5 + C6)

Three changes that compound into a much faster, cheaper toolkit:

1. **Content-addressed asset cache** at `~/.blender-mcp-cache/<source>/<asset_id>_<res>_<format>/` — every PolyHaven / ambientCG / Sketchfab download checks-then-fetches; second use is instant. Multi-zone scene re-downloads drop from ~600 MB → 0.
2. **Parallel multi-asset download** — `apply_archviz_material` uses `ThreadPoolExecutor` to fan out candidate downloads; 10 textures stop being 90 s serial.
3. **Async render-job pattern** — `render_image` returns `{"job_id": ...}` immediately and starts via `bpy.app.timers.register`; the existing `poll_*_job_status` pattern (already in the codebase for Hyper3D/Hunyuan) extends to renders. Cycles renders >180 s no longer time out at the socket layer.
4. **Polling backoff** — Tripo3D / Meshy switch from fixed 2.5/3.0 s to exponential (2.5s → 5s → 10s after 30s).
5. **Resolution tier** — single `quality_tier='preview'|'final'|'hero'` parameter on download tools maps to 1k/2k/4k uniformly.

## Sprint plan

Each sprint produces a tagged GitHub release. Order matches user priority A → F → B → C → D → E.

### Sprint 5 — LLM ergonomics (A) + folded-in items
**Estimate:** 4–5 days
**Deliverable:** v2.0.0+fork.1 (BC-break)

14 items:

1. Error envelope unification (C1) — hard migration, no legacy fallback.
2. Error messages rewritten to actionable fixes; `_format_error()` helper pattern-matches common exceptions to user-facing text.
3. `generate_3d_smart` Hyper3D / Hunyuan3D bail bug fixed.
4. `generate_3d_smart` cost estimates calibrated.
5. State-leakage fail-fast: `set_world_hdri_rotation` without HDRI, `apply_archviz_material(genre='painted_wall')` without `custom_hex`, etc. → `STATE_REQUIRED` error.
6. `execute_blender_code` docstring rewritten: "use only when no purpose-built tool fits" + list of alternatives.
7. `set_camera_view` and `frame_camera_to_objects` docstrings cross-reference each other.
8. `download_polyhaven_asset` accepts optional `target_size` (None = native).
9. `get_*_status` return structured envelopes.
10. **Mass naming pass (folded in)**: `import_generated_asset` → `import_hyper3d_asset` (hard rename, no alias per BC=B); `poll_rodin_job_status` → `poll_hyper3d_job_status`; `generate_hyper3d_model_via_text` → `generate_hyper3d_text_to_3d`; siblings same way. ~8 renames total.
11. `generate_3d_smart` accepts `reference_image_path` parameter (just routing — auto-feeding from Codex/OpenAI is Sprint 7).
12. **Service descriptor seed (folded in)**: minimal declarative dict that the envelope decorator reads from. Designed as the seed for Sprint 10's full registry refactor.
13. **OpenAI integration generalized to OpenAI-compatible (new requirement)**: adds `openai_base_url` to AddonPreferences/scene/env (default `https://api.openai.com/v1`), unlocks Comfly / OpenRouter / vLLM / any OpenAI-shape endpoint. Pre-set provider templates in N-panel: `openai_official` / `comfly_chat` / `openrouter` / `custom`. Per-call cost estimate falls back to `cost_unknown=True` for non-official endpoints; `set_usage_budget("openai", $X)` provides the safety net.
14. **Telemetry default → opt-in (D3 decision)**: `telemetry_consent` AddonPreferences default flips from `True` to `False`. Migration note in CHANGELOG.

### Sprint 6 — Discoverability (F)
**Estimate:** 2–3 days
**Deliverable:** v2.1.0+fork.1

- `check_services` surfaced as the documented "first call in any session" — top of README tools table, replaces `get_scene_info` in INSTALL_AI.md Step 7.
- README tool reference reorganized: `🚀 Most-used tools` 5-row table at top (`check_services`, `apply_archviz_material`, `setup_lighting`, `generate_3d_smart`, `render_image`); within AI 3D, FREE/Codex paths above paid.
- 🆓 badge for free tools (Codex, ChatGPT-quota path, ambientCG, PolyHaven).
- N-panel collapse-by-default: services group by tier (Free, Free trial, Paid). Sub-boxes only render when checkbox enabled (already partial; tighten).
- `install.sh` failure-path hardening: precheck `git`/`python3`, pin `uv sync --python 3.12` to escape conda capture, summarize warnings instead of always claiming "Done."
- `AGENTS.md` at fork root for AI agents working ON the fork (tool-naming rule, dispatcher pattern, docstring rule, telemetry default = off, where to add UI rows, manual-test checklist).
- Tool-count claim drift: `scripts/gen_tool_table.py` auto-generates README `Tools reference` from `mcp.list_tools()`; CI asserts no drift.

### Sprint 7 — Output quality (B)
**Estimate:** 3–4 days
**Deliverable:** v2.2.0+fork.1

- Render quality overhaul (C4) — all seven items.
- Asset-search relevance ranking: PolyHaven sort by download_count desc + tags filter; Sketchfab `sort_by=-likeCount`, `license=cc0,by`, `min_face_count=2000`, `pbr=true`; ambientCG sorted, tags surfaced.
- Image-to-3D pipeline complete: `generate_3d_from_concept(prompt, ...)` chains Codex/OpenAI image gen → Tripo3D / Meshy image-to-3D → import + ground.
- Tripo3D / Meshy version auto-discovery at session start (replaces hardcoded date strings).

### Sprint 8 — Cost (C)
**Estimate:** 2–3 days
**Deliverable:** v2.3.0+fork.1

- Async + cache layer parts 1–2: content-addressed asset cache + AI-generation prompt-hash dedup (cluster C5 partial).
- `quality_tier='preview'|'final'|'hero'` toggle on all download tools.
- Image-gen file-name dedup: default filename = `<sha8(prompt+model+size+quality)>.png`; existing file → cache hit, skip API.
- Codex CLI vs OpenAI API breakeven hint: when `n>3` or recent codex >5 in last hour, response includes `"suggestion": "consider generate_image_openai for batch"`.
- Polling backoff (C5 part 4).

### Sprint 9 — Performance (D)
**Estimate:** 3–4 days
**Deliverable:** v2.4.0+fork.1

- Async render-job pattern (C5 part 3): `render_image` returns `job_id` immediately; `poll_render_status(job_id)` mirrors existing pollers.
- Parallel multi-asset download (C5 part 2).
- `scatter_on_surface` numpy/`foreach_get` vectorization (60 s → 1–2 s on 500k-face surfaces).
- `get_viewport_screenshot` socket protocol: 4-byte length prefix on the addon side, eliminate the O(n²) JSON probe.
- `mesh_cleanup` size-aware guardrail (warn + estimate when faces > 200k).

### Sprint 10 — Architecture (E)
**Estimate:** 5–7 days (largest)
**Deliverable:** v2.5.0+fork.1

- Service registry abstraction (C2) — full god-class split into `addon/__init__.py` + per-service modules.
- Test scaffold: `tests/test_pure_helpers.py` for `_hex_to_rgba`, `_kelvin_to_rgb`, `_resilient_*`, `_world_bbox`, `_usage_*`. `tests/test_status_smoke.py` mocks socket and asserts envelope shape per tool. `pytest` in `pyproject.toml`, GitHub Actions 1-job CI.
- Blender headless smoke test (D4 decision part b): `bpy --python tests/smoke.py` runs `check_services` + 3 core tools end-to-end.
- CHANGELOG re-format: short summary per release, long postmortems moved to `docs/postmortems/`.
- Sidecar credentials path → `~/.config/blendermcp/credentials-v1.json` with schema field + numbered backups for multi-Blender safety.

## Open decisions (resolved)

| ID | Decision | Resolved |
|---|---|---|
| D1 | PyPI publish timing | Defer until post-Sprint-10 v2.5 (after refactor stabilizes) |
| D2 | Upstream PR strategy | Submit 3–4 universal patches: `nor_dx` flip, kelvin blackbody, telemetry opt-in, `import_generated_asset` rename |
| D3 | Telemetry default | Opt-in (default False) starting Sprint 5 |
| D4 | Test strategy | Combined: pytest for pure helpers (no Blender), `bpy --python` headless for smoke tests |
| D5 | Documentation language | Top: English. Bottom: Chinese quickstart block. CHANGELOG English, CLAUDE.md / project docs bilingual |

## Risks (accepted)

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Sprint 5 BC-break invalidates running cafe-modeling sessions | Schedule Sprint 5 between cafe sessions, not during. Add migration cheat sheet to CLAUDE.md so the next AI session auto-adapts |
| R2 | Sprint 7 lighting fix changes look of every existing render | Re-render hero shots per mood, lock visual targets in CHANGELOG |
| R3 | Sprint 10 registry refactor regresses 56 tools at once | Test scaffold from Sprint 10 itself runs first; one-commit-per-service refactor for fine-grained rollback |
| R4 | Sprint 5 service descriptor + Sprint 10 registry = double-touch | Sprint 5 descriptor designed as Sprint 10 seed (same interface name, expand-not-redo) |
| R5 | Codex CLI batching depends on daemon mode that doesn't exist | Use "batch-as-single-prompt" workaround (one Codex run generates N images), pay cold-start once |

## Non-goals

- Changing the socket protocol (newline-free JSON over TCP — keeps upstream compat)
- GUI installer (.pkg / .msi) — `curl ... | bash` is sufficient
- Local model inference (SDXL / Flux running on user GPU) — separate sprint outside this roadmap
- Rewriting upstream-inherited code paths (Hunyuan3D internals) unless they directly block other work
- Adding more AI 3D providers beyond the 4 already wired (Hyper3D / Hunyuan / Tripo3D / Meshy) — saturated for now

## Verification

### Per-sprint exit criteria

Every sprint must pass before tagging:

1. `pytest` (≤ 5 s) — pure helpers + envelope shape on mocks
2. `bpy --python tests/smoke.py` — `check_services` + 3 core tools end-to-end
3. Manual hero-render comparison vs previous sprint's hero — visual quality non-regression

### Sprint 5 specific test matrix

| Category | Test | Tool |
|---|---|---|
| Pure helpers | `_tool_response`, `_format_error`, `_persist_credentials` | pytest |
| Envelope shape | All 56 tools return `{ok, data?, error?}`, error has `code` | pytest + mock socket |
| Naming migration | `grep` confirms zero stale-name usages | bash + ripgrep |
| Smart router | 6 quality × 4 provider matrix dry-run; `reference_image_path` routes to image-to-3D variants | mock provider stubs |
| OpenAI-compat | Comfly endpoint `gpt-image-2` and `gemini-3.1-flash-image-preview-2k` produce PNG; `dall-e-3` via official endpoint still works | live API |
| State leakage | `set_world_hdri_rotation` without HDRI returns `code=STATE_REQUIRED`, no silent success | smoke in Blender |
| Telemetry default | Fresh install: `addon.preferences.telemetry_consent` is False | smoke |

## Out of scope for this spec

The implementation plan for Sprint 5 (the actual step-by-step task list) is produced by the `writing-plans` skill in a separate document. This roadmap stops at "what's in scope per sprint and how we verify it."

---

**Authors / approval log**

- 2026-04-28: roadmap drafted from 6 parallel audit reports + user direction.
- Decisions D1–D5 confirmed by project owner.
- Risks R1–R5 accepted, mitigations approved.
- Sprint 5 scope (14 deliverables, 4–5 days) approved as first sub-project.

Next step: invoke `writing-plans` skill to produce the Sprint 5 implementation plan.
