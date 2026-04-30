---
name: interior-video-research
description: Use when the user wants to learn from a YouTube tutorial about photorealistic interior design / Blender archviz / a specific style or technique. Trigger phrases include "analyze this video", "拆这个视频", "learn from this tutorial", a YouTube URL pasted with no other context, or "find videos about X and analyze them" where X is an interior design technique. The skill drives the full Atelier video-research pipeline — from URL or search keywords through Gemini analysis through synthesis-ready markdown — and refuses to fabricate analysis the AI cannot verify.
---

# interior-video-research

Atelier's craft-knowledge pipeline. Run this when the user wants you to extract production photoreal interior design technique from a YouTube tutorial and integrate it into the project's handbook / skills / quality gates.

## When to invoke

- User pastes a YouTube URL and asks "analyze this" / "拆这个" / "learn from this"
- User says "find me videos about X and analyze them" where X is an interior style / Blender technique / archviz topic
- User asks "improve <chapter>.md based on real-world tutorials"

## Required environment

- `GEMINI_API_KEY` env var must be set (Google AI Studio free tier is fine — get one at https://aistudio.google.com/apikey)
- Python venv `.venv/` at repo root (already exists)
- Optional: `yt-dlp` installed for transcript fallback (`brew install yt-dlp` or `pip install yt-dlp`)

If `GEMINI_API_KEY` is missing, **stop and ask the user to set it** rather than fabricating analysis from training memory.

## Single-URL flow

1. **Locate the analyzer**: `scripts/analyze_youtube.py` (in this repo).
2. **Run it**:
   ```bash
   GEMINI_API_KEY="$GEMINI_API_KEY" .venv/bin/python3 scripts/analyze_youtube.py \
     "<youtube-url>"
   ```
3. The script auto-derives the output filename from the video's oEmbed title + author, saves to `docs/dev/video-analysis/analyses/YYYY-MM-DD-<channel>-<topic>.md`.
4. **Read the resulting analysis file** to confirm Source / TL;DR / Project shape sections look correct (Gemini occasionally hallucinates channel name when video lacks branded intro — the script injects oEmbed metadata as ground truth to mitigate, but spot-check anyway).
5. Surface the analysis to the user. Highlight the **"Recommended Atelier project changes"** section — that's the actionable output.
6. **Do not auto-apply changes** unless the analysis is the 2nd+ on a coherent topic (per the workflow's cross-tutorial discipline). For first analyses on a topic, record findings in `docs/dev/video-analysis/synthesis-log.md` as "needs corroboration".

## Multi-URL / search flow

If the user gives multiple URLs or asks you to find videos about a topic:

1. If they gave URLs → loop over them, running the analyzer per URL.
2. If they gave keywords → use `WebSearch` to find candidate videos (use the keyword recommendations in `docs/dev/video-analysis/README.md` § "Tier 2/3/4" as guidance for what makes a good candidate).
3. Filter candidates: prefer 10-60 minute step-by-step tutorials with clear narration over silent timelapses.
4. Present 3-5 candidates to the user with one-line descriptions; let them pick which to actually analyze.
5. Analyze the picked URLs; save to `analyses/`.
6. Once ≥ 2 analyses on a coherent topic land, **propose synthesis** — read all relevant analyses, identify cross-tutorial agreement, and propose handbook deltas using the 4 directive verbs from the schema (`ADD-RULE`, `TUNE-GATE`, `EDIT-SKILL`, `ADD-TOOL`).

## Synthesis discipline (read this before applying any handbook change)

Per `docs/dev/video-analysis/README.md` § "Citation discipline", encoding a tutorial-derived rule into the handbook requires either:

- **Cross-tutorial agreement** — the same rule appears in 2+ analyses on the same topic, OR
- **Primary-source corroboration** — the rule has independent backing in Blender Manual / IES / GB standard / Disney BSDF / named publication

For single-source findings without primary corroboration, **record in `synthesis-log.md` only** — don't yet edit the handbook. The synthesis log is the staging area; rules graduate to handbook when corroboration arrives.

If the user explicitly directs apply-on-one-source (as they did in Round 1), comply but **find a primary source via `WebSearch` / `WebFetch` before editing the handbook**. Cite both the tutorial AND the primary in the inline citation. Never write a handbook rule cited only by a single tutorial.

## When the analyzer fails

| Failure mode | Diagnosis | Fix |
|---|---|---|
| Exit 3 — `GEMINI_API_KEY not set` | env var missing | `export GEMINI_API_KEY=AIza...` |
| Exit 4 — "all candidate models exhausted" | quota hit on all candidate models | wait for quota refresh (free tier resets daily); or upgrade to paid |
| Exit 5 — "prompt file not found" | repo state issue | verify `docs/dev/video-analysis/prompts/gemini-full-video.md` exists |
| Hangs > 10 minutes | very long video; or Gemini slow | kill + retry with `--model gemini-2.5-flash` (faster, slightly less accurate) |
| Output has wrong channel name | Gemini hallucinated | rerun — the oEmbed ground-truth injection should override; if persistent, fix manually in the file |
| Output is < 3000 chars | model bailed early | rerun, or try `--model gemini-3-flash-preview` explicitly |

## Don't do these

- **Don't fabricate analysis** from training memory if the analyzer fails. If you can't get genuine video content, say so — fall back to `scripts/yt-transcript.sh` for transcript-only path (with degraded numeric fields per the schema).
- **Don't apply handbook changes from a single tutorial** without primary-source corroboration. The whole project's defensibility rests on this.
- **Don't trust UI-numeric values blindly across runs.** The same video analyzed 3 times can yield different focal lengths / sample counts because the model partially hallucinates UI values when not narrated. Cross-tutorial agreement is the real signal.

## Relationship to other skills

- This skill produces `analyses/*.md` — those are CRAFT inputs.
- `interior-designer` agent reads handbook chapters at task start — when the synthesis step lands handbook updates, the agent automatically picks them up.
- `interior-render-direction` skill cites handbook chapters in gate-violation messages — handbook updates from this pipeline flow into those citations.
