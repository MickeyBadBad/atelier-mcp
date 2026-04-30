# Transcript-only fallback prompt

When Gemini access isn't available, fall back to extracting from the transcript only. This loses visual-only data (UI clicks, panel values not narrated, color picker positions) but recovers the narrative content.

> Use this when running Claude on a `yt-dlp`-derived transcript.

---

You are analyzing the **transcript** of a Blender interior design tutorial video for the **Atelier** project. You do NOT have visual content — only the spoken narration. Adjust accordingly:

- For numeric values, prefer values the narrator stated explicitly. Mark anything you infer as `(inferred)` not `(visible)`.
- For UI sequences, you can only capture what was narrated. If the creator silently dragged a slider, you'll miss it. Note this gap in the analysis.
- For shader / compositor / color grading work, you'll typically miss the specific node connections unless they're narrated. Capture what's there.

The output schema is the same as `gemini-full-video.md` (refer to it). For every "(not visible)" placeholder in that schema where the answer can only be visual, write `(visual-only — transcript missed)`.

# Source

```
<paste transcript here, including timestamps if available>
```

# Specific transcript-mode adjustments

In the **Settings extracted** sections, where the schema says `(not visible)`, distinguish two cases:
- `(narrated but value missing)` — the creator talked about it but didn't say a number
- `(visual-only — transcript missed)` — the value was probably on screen, but transcripts don't capture UI

In **Workflow sequence**, infer stage boundaries from the narration cues ("now let's…", "next step…").

In **Photorealism techniques**, flag any technique you can only partially reconstruct from words (e.g. "they did something with the roughness" — say so rather than fabricating).

In **Recommended Atelier project changes**, be more conservative — transcript-only signal is weaker. Only recommend changes that would still make sense if the visual data confirmed.

The **Deltas vs Atelier** section is still the most important output. Spend the most effort there.
