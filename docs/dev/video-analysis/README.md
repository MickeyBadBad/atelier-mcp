# Video Analysis Workflow — Learn from real photorealistic Blender interior tutorials

The Atelier handbook is grounded in standards (GB / IES / Neufert / Disney BSDF). But the *gap* between "rules that produce technically-defensible interiors" and "renders that look like the YouTube reference" lives in **craft knowledge** — specific sample counts, denoise settings, post-processing tricks, shader graph patterns, lighting recipes — that named tutorial creators on YouTube / Bilibili have already solved.

This workflow turns those tutorials into structured `.md` artifacts that Atelier can ingest as handbook updates, gate threshold tweaks, skill instructions, or new tools.

```text
YouTube URL
    │
    ▼
┌─────────────────────────────────┐
│ Gemini 2.0 / 2.5 (full video)   │  ← native YouTube URL support
│   OR                            │
│ yt-dlp transcript + Claude      │  ← fallback when no Gemini access
└─────────────────────────────────┘
    │
    ▼  (uses prompts/gemini-full-video.md)
analyses/<date>-<slug>.md          ← one per video, schema-conformant
    │
    ▼  (Claude consumes these)
synthesis-log.md                   ← running log of what we changed and why
    │
    ▼
Project files updated:
  - docs/handbook/<chapter>.md     (new rules, refined thresholds)
  - src/atelier/_gates.py          (gate default tweaks)
  - .claude/skills/interior-*.md   (skill instruction refinements)
  - src/atelier/_moodboard.py      (image-gen prompt patterns)
  - src/atelier/server.py          (new MCP tools when a recurring technique is missing)
```

---

## When to use

- You found a 10-60 minute Blender / Octane / Corona / Cycles interior tutorial that produces output noticeably better than what Atelier currently produces
- You want the technique encoded as Atelier rules (not just memorized by you)
- The video has clear narration of *why* — not just timelapse with music

## When NOT to use

- Pure speedpaint / timelapse with no narration → too little signal
- Generic "Blender beginners" tutorials → already in our handbook foundation
- Animation-focused tutorials → Atelier doesn't ship animation tools (out of scope)
- Walkthrough/photogrammetry-only tutorials → cover with `import_lidar_scan`, not handbook updates

## The 5 phases

### Phase 1 — Selection

Pick 3-5 videos at a time from a single coherent topic (e.g., "5 photorealistic kitchen tutorials" or "3 Cycles bedroom recipes"). Cross-tutorial agreement on a value is much more useful than a single-source claim — if 4/5 tutorials use 24mm lens at 1.5m, that's a defensible Atelier default.

### Phase 2 — Extraction

Two paths depending on tooling availability:

**Path A — Gemini (preferred, captures visual content)**

1. Open [Google AI Studio](https://aistudio.google.com/) (free Gemini access; works with personal account)
2. Pick model: **Gemini 2.5 Pro** (best video understanding) or **Gemini 2.0 Flash** (fastest, free tier-friendly)
3. New chat → attach the YouTube URL via the link icon (Gemini natively reads YouTube URLs up to ~3 hours)
4. Paste the prompt from [`prompts/gemini-full-video.md`](prompts/gemini-full-video.md) — replace `<URL>` placeholder
5. Wait 1-3 minutes for the analysis
6. Save the response as `analyses/YYYY-MM-DD-<channel-slug>-<topic-slug>.md`

**Path B — Transcript-only (fallback when no Gemini)**

```bash
./scripts/yt-transcript.sh "https://www.youtube.com/watch?v=..." > /tmp/transcript.txt
```

Then either:
- Hand the transcript + the prompt at [`prompts/transcript-only.md`](prompts/transcript-only.md) to Claude, or
- Tell Claude "analyze /tmp/transcript.txt using docs/dev/video-analysis/prompts/transcript-only.md"

Path B misses visual-only details (button-click sequences, slider values not narrated, color-picker positions). Use Path A whenever possible.

### Phase 3 — Save analysis

Drop the resulting `.md` under [`analyses/`](analyses/). Naming: `YYYY-MM-DD-<channel>-<short-topic>.md`. Examples:

```
analyses/2026-04-30-blender-guru-cycles-kitchen.md
analyses/2026-05-01-curtis-holt-octane-bedroom.md
analyses/2026-05-01-cgmatter-volumetric-cafe.md
```

The schema is enforced via [`schema/analysis-template.md`](schema/analysis-template.md). If an analysis doesn't match the schema, regenerate it — the synthesis step assumes structural fidelity.

### Phase 4 — Synthesis

After landing 3+ analyses on a coherent topic, ask Claude:

> Look at all `.md` files under `docs/dev/video-analysis/analyses/`. Synthesize the deltas vs Atelier. For each finding that appears in 2+ analyses (cross-tutorial agreement), propose the smallest project change that captures it: a one-line handbook addendum, a gate default tweak, a skill instruction edit, or a new MCP tool. Output a list with file path → diff to apply.

Claude reads the analyses + the project, proposes changes, and on approval applies them. Append the round of changes to [`synthesis-log.md`](synthesis-log.md) so we can audit "what did we change because of which video, when".

### Phase 5 — Apply + verify

After applying changes:

```bash
.venv/bin/pytest tests/                                # 250+ tests still green
.venv/bin/pytest tests/test_handbook_acceptance.py    # citation density holds
.venv/bin/atelier handbook <changed-chapter>           # human-read the change
```

If a new MCP tool was added: smoke test it via the live MCP server with a sample call.

---

## Schema discipline (why it matters)

Each video analysis MUST conform to [`schema/analysis-template.md`](schema/analysis-template.md). This is a structured-prompt-engineering trick: when Gemini outputs to a known schema, Claude can reliably consume it without bespoke parsing.

If Gemini's output drifts from the schema (e.g. it adds extra sections or skips ones), the failure mode is silent — the synthesis step misses content. The fix: regenerate with a tighter prompt, or fix the analysis manually.

## Citation discipline (carries over from the main project)

The Atelier project's hard rule — every numeric value in the handbook must trace to an authoritative source — applies here too. Tutorial videos are themselves authoritative *if and only if* the channel is named, established, and the technique is verifiable.

Acceptable citation form in the handbook for a tutorial-derived rule:

```markdown
For Cycles interior renders, set Light Tree to ON when using >5 lights
(per Blender Manual §"Light Tree", Cycles 4.0+; corroborated by
Blender Guru "Photorealistic Interior" tutorial 2025-08, who reports
~2× faster convergence with Light Tree on a 12-light kitchen scene).
```

Do NOT cite tutorials as the *only* source for a rule. Always cross-reference a documented standard or manual.

## Output products (per video)

Each analysis produces:

1. **The analysis `.md` itself** under `analyses/`
2. **Zero or more handbook deltas** in `docs/handbook/`
3. **Zero or more gate threshold tweaks** in `src/atelier/_gates.py`
4. **Zero or more skill instruction edits** under `.claude/skills/`
5. **Zero or more new tool stubs** in `src/atelier/server.py`
6. **A row in `synthesis-log.md`** documenting what changed and why

## Anti-patterns (don't do these)

- **One video = one rule.** A single tutorial's claim is not enough to override the handbook. Need cross-tutorial agreement (2+ analyses) or a primary source backing.
- **Copying values without citation.** "Mr. X uses 512 samples" is not a citation. Either cite the named tutorial AND a primary reference, or label it explicitly as "convention observed across N tutorials".
- **Adding tools speculatively.** A tutorial showing a niche technique used once doesn't justify a new MCP tool. Wait for 2+ recurrences.
- **Long-form copy from transcript.** Quote ≤ 3 lines verbatim. Synthesize the rest.

---

## See also

- [`prompts/gemini-full-video.md`](prompts/gemini-full-video.md) — the Gemini extraction prompt
- [`prompts/transcript-only.md`](prompts/transcript-only.md) — the fallback prompt for Claude on a transcript
- [`schema/analysis-template.md`](schema/analysis-template.md) — the output schema every analysis must follow
- [`synthesis-log.md`](synthesis-log.md) — running ledger of project changes
- [`scripts/yt-transcript.sh`](../../../scripts/yt-transcript.sh) — yt-dlp wrapper for transcript fallback
