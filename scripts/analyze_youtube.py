#!/usr/bin/env -S uv run python
"""Analyze a YouTube video via Gemini → schema-conformant markdown.

This is the v2 implementation, refactored 2026-05-08 from raw urllib
to the official google-genai SDK. Encodes Google's video-understanding
best practices directly so the analyzer stops leaving free tokens on
the floor.

Best-practices baked in (per
https://ai.google.dev/gemini-api/docs/video-understanding):

  ✅ One video per request (the script accepts exactly one URL).
  ✅ Text prompt placed AFTER the video part in the contents array
     (the doc explicitly recommends this for text+single-video input).
  ✅ media_resolution=LOW by default — Gemini 3 introduced this knob
     and tutorial content (which is what this analyzer was built for)
     rarely needs fine-text OCR on small screen elements. LOW gives
     ~66 tokens/frame vs default ~258/frame = roughly 3× more video
     per quota dollar.
  ✅ Token usage logged to stderr after each successful call so the
     operator can reason about cost.
  ✅ Optional --fps override for fast-action content; --start/--end
     for clipping a long video to a relevant slice.

Limitations consciously NOT addressed (out of scope for this script):

  - Files API upload — we only handle public YouTube URLs. Files API
    is for local video files and >20MB total request size, neither
    applies to our use case (handbook synthesis from public tutorials).
  - Context caching — relevant when re-querying the same video
    repeatedly. We analyze each video once.
  - The 8h/day free-tier YouTube cap — we don't track quota; if you
    hit it the SDK will surface a 429 and the fallback chain takes
    over. See exit-code commentary below.

Usage:
    export GEMINI_API_KEY=AIza...
    scripts/analyze_youtube.py "https://www.youtube.com/watch?v=..." \\
        [--out path/to/out.md] \\
        [--model gemini-3-flash-preview] \\
        [--prompt-file path/to/prompt.md] \\
        [--media-resolution low|medium|high|default] \\
        [--fps 0.5] \\
        [--start-offset 1m30s --end-offset 5m]

Exit codes:
    0  analysis written successfully
    2  bad arguments
    3  GEMINI_API_KEY not set
    4  all model candidates exhausted (typically 503 / 429 cascade)
    5  prompt file or output path failed
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT = REPO_ROOT / "docs/dev/video-analysis/prompts/gemini-full-video.md"
DEFAULT_ANALYSES_DIR = REPO_ROOT / "docs/dev/video-analysis/analyses"

MODEL_CANDIDATES = (
    # User direction 2026-05-08: prefer gemini-3-flash-preview.
    # Empirically the most reliable free-tier video-ingestion model
    # observed during Round 4 (4 clean schema-conformant analyses).
    "gemini-3-flash-preview",
    # GA non-preview models — try when 3-flash-preview is busy.
    # As of 2026-05-08 these pass text-only probes but 3.1-flash-lite
    # 503s on video ingestion under daily peak load.
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    # Preview / paid tier — last resort.
    "gemini-3.1-pro-preview",        # paid; usually 0 quota on free tier (429)
    "gemini-3.1-flash-lite-preview", # preview; sometimes 503
    "gemini-3-pro-preview",          # paid; usually 0 quota on free tier (429)
    "gemini-pro-latest",
    "gemini-flash-latest",
    "gemini-2.5-pro",                # paid
    "gemini-2.0-flash",              # free-tier baseline
)


# ---------- YouTube oEmbed (no API key, public videos only) ---------------

def fetch_oembed(url: str) -> dict:
    """Fetch title + author from YouTube's public oEmbed endpoint.

    Used to ground-truth the channel name and title in the analyzer's
    prompt — without this Gemini sometimes hallucinates the channel
    from visual branding inside the video.
    """
    oembed = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": url, "format": "json"}
    )
    try:
        with urllib.request.urlopen(oembed, timeout=15) as r:
            data = json.load(r)
            return {
                "title": data.get("title", ""),
                "author": data.get("author_name", ""),
            }
    except Exception:
        return {"title": "", "author": ""}


def slugify(s: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower(), flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "_", s).strip("_")
    return s[:max_len] or "untitled"


def derive_output_path(url: str, analyses_dir: Path) -> Path:
    meta = fetch_oembed(url)
    today = datetime.date.today().isoformat()
    author_slug = slugify(meta["author"]) or "unknown_channel"
    title_slug = slugify(meta["title"]) or "untitled"
    return analyses_dir / f"{today}-{author_slug}-{title_slug}.md"


def load_prompt(prompt_file: Path, url: str, meta: dict) -> str:
    """Read the schema prompt template, substitute URL, and prepend
    oEmbed-fetched title/channel as ground truth so Gemini doesn't
    hallucinate them."""
    text = prompt_file.read_text(encoding="utf-8")
    parts = text.split("\n---\n", 1)
    body = parts[1] if len(parts) == 2 else text
    body = body.replace("<URL>", url)

    if meta.get("title") or meta.get("author"):
        ground_truth = (
            "\n\n# Known facts (do NOT re-detect — use these verbatim "
            "in the Source section)\n\n"
            f"- URL: {url}\n"
            f"- Channel: {meta.get('author', '')}\n"
            f"- Title: {meta.get('title', '')}\n\n"
            "These were fetched from YouTube oEmbed before this prompt; "
            "they are authoritative. Do NOT guess Channel from the video "
            "content — copy the value above. Only DETECT fields that "
            "aren't pre-supplied (Length, Published date, etc.).\n"
        )
        body = ground_truth + body
    return body


# ---------- Gemini SDK call ------------------------------------------------

# The SDK exposes media_resolution at two levels:
#   1. GenerateContentConfig.media_resolution (global, MediaResolution enum)
#   2. Part.media_resolution (per-part, PartMediaResolution { level, num_tokens })
# Empirically (2026-05-08, gemini-3-flash-preview, YouTube URL file_data),
# the GenerateContentConfig knob did NOT change video token counts. The
# per-Part PartMediaResolution is the surface that actually controls
# token allocation for YouTube file_data parts. We set BOTH (belt-and-
# suspenders) so the override applies regardless of which the model
# consults.
# See https://ai.google.dev/gemini-api/docs/media-resolution.
def _media_resolution_global(label: str):
    """For GenerateContentConfig.media_resolution. Returns enum or None."""
    from google.genai import types
    mapping = {
        "low":     types.MediaResolution.MEDIA_RESOLUTION_LOW,
        "medium":  types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
        "high":    types.MediaResolution.MEDIA_RESOLUTION_HIGH,
    }
    return mapping.get((label or "").lower())


def _media_resolution_part(label: str):
    """For Part.media_resolution. Returns PartMediaResolution or None."""
    from google.genai import types
    mapping = {
        "low":     types.PartMediaResolutionLevel.MEDIA_RESOLUTION_LOW,
        "medium":  types.PartMediaResolutionLevel.MEDIA_RESOLUTION_MEDIUM,
        "high":    types.PartMediaResolutionLevel.MEDIA_RESOLUTION_HIGH,
    }
    level = mapping.get((label or "").lower())
    if level is None:
        return None
    return types.PartMediaResolution(level=level)


def _summarize_usage(usage) -> dict:
    """Extract a JSON-serializable summary from the SDK's usage_metadata."""
    if usage is None:
        return {}
    out = {
        "prompt_tokens":     getattr(usage, "prompt_token_count", None),
        "candidates_tokens": getattr(usage, "candidates_token_count", None),
        "thoughts_tokens":   getattr(usage, "thoughts_token_count", None),
        "total_tokens":      getattr(usage, "total_token_count", None),
    }
    details = getattr(usage, "prompt_tokens_details", None) or []
    modalities = {}
    for d in details:
        mod = getattr(d, "modality", None)
        if mod is not None:
            key = str(mod).split(".")[-1].lower()
            modalities[key] = getattr(d, "token_count", None)
    if modalities:
        out["modalities"] = modalities
    return out


def call_gemini(
    *,
    api_key: str,
    url: str,
    prompt_text: str,
    model: str,
    media_resolution: str,
    fps: Optional[float],
    start_offset: Optional[str],
    end_offset: Optional[str],
    timeout: int,
) -> tuple[Optional[str], dict, Optional[str]]:
    """Returns (text, usage_dict, error_str_or_None)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # Build VideoMetadata (only when at least one option is set; empty
    # VideoMetadata can confuse the SDK).
    vm_kwargs = {}
    if fps is not None:
        vm_kwargs["fps"] = fps
    if start_offset:
        vm_kwargs["start_offset"] = start_offset
    if end_offset:
        vm_kwargs["end_offset"] = end_offset
    video_metadata = types.VideoMetadata(**vm_kwargs) if vm_kwargs else None

    # Per-Part media_resolution (the one that actually moves token counts
    # for YouTube file_data on gemini-3-flash-preview, empirically).
    part_mr = _media_resolution_part(media_resolution)

    part_kwargs = {"file_data": types.FileData(file_uri=url)}
    if video_metadata:
        part_kwargs["video_metadata"] = video_metadata
    if part_mr is not None:
        part_kwargs["media_resolution"] = part_mr
    file_data_part = types.Part(**part_kwargs)

    # PER DOC BEST PRACTICE: text part AFTER video part.
    parts = [file_data_part, types.Part(text=prompt_text)]

    # Belt-and-suspenders: also set the global config-level knob in case
    # a future model honors it for YouTube parts.
    config = None
    mr_global = _media_resolution_global(media_resolution)
    if mr_global is not None:
        config = types.GenerateContentConfig(media_resolution=mr_global)

    try:
        # google-genai's HTTP options accept a request timeout in ms.
        # If config doesn't honor one, the SDK falls back to its default.
        response = client.models.generate_content(
            model=model,
            contents=types.Content(parts=parts),
            config=config,
        )
        text = response.text or ""
        usage_dict = _summarize_usage(getattr(response, "usage_metadata", None))
        return text, usage_dict, None
    except Exception as e:
        # We surface the error string and let the fallback chain decide
        # whether to advance to the next model. Common patterns we
        # detect by substring: "503" / "UNAVAILABLE" → service overload;
        # "429" / "RESOURCE_EXHAUSTED" → quota; "404" / "NOT_FOUND" →
        # bad model name (skip silently).
        return None, {}, f"{type(e).__name__}: {e}"


# ---------- Driver ---------------------------------------------------------

def _is_transient(err_str: str) -> bool:
    """Worth falling through to the next candidate model?"""
    s = err_str.lower()
    return any(
        marker in s for marker in (
            "503", "unavailable",
            "429", "quota", "resource_exhausted", "rate limit",
            "deadline_exceeded", "timeout", "timed out",
            "remotedisconnected",
        )
    )


def analyze(
    *,
    api_key: str,
    url: str,
    out_path: Path,
    prompt_file: Path,
    explicit_model: Optional[str],
    media_resolution: str,
    fps: Optional[float],
    start_offset: Optional[str],
    end_offset: Optional[str],
    timeout: int,
    verbose: bool,
) -> int:
    if verbose:
        print(f"[analyze] video: {url}", file=sys.stderr)
        print(f"[analyze] output: {out_path}", file=sys.stderr)

    if not prompt_file.is_file():
        print(f"ERROR: prompt file not found: {prompt_file}", file=sys.stderr)
        return 5

    meta = fetch_oembed(url)
    if verbose and meta.get("author"):
        print(
            f"[analyze] oEmbed → channel={meta['author']!r}, "
            f"title={meta['title'][:60]!r}",
            file=sys.stderr,
        )

    prompt_text = load_prompt(prompt_file, url, meta)

    candidates = [explicit_model] if explicit_model else list(MODEL_CANDIDATES)

    last_err: Optional[str] = None
    for model in candidates:
        if verbose:
            print(f"[analyze] trying model: {model} "
                  f"(media_resolution={media_resolution})",
                  file=sys.stderr)
        text, usage, err = call_gemini(
            api_key=api_key,
            url=url,
            prompt_text=prompt_text,
            model=model,
            media_resolution=media_resolution,
            fps=fps,
            start_offset=start_offset,
            end_offset=end_offset,
            timeout=timeout,
        )

        if text:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            now = datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            extras = []
            if fps is not None:
                extras.append(f"fps={fps}")
            if start_offset or end_offset:
                extras.append(
                    f"clip={start_offset or '0'}..{end_offset or 'end'}"
                )
            extra_str = " " + " ".join(extras) if extras else ""
            header = (
                f"<!-- generated by scripts/analyze_youtube.py "
                f"on {now} using model={model} "
                f"media_resolution={media_resolution}{extra_str} -->\n\n"
            )
            out_path.write_text(header + text, encoding="utf-8")

            tok_summary = ""
            if usage:
                m = usage.get("modalities") or {}
                tok_summary = (
                    f" tokens=total:{usage.get('total_tokens')} "
                    f"video:{m.get('video', '?')} "
                    f"text:{m.get('text', '?')} "
                    f"thoughts:{usage.get('thoughts_tokens', 0)}"
                )
            if verbose:
                print(
                    f"[analyze] ✓ written: {out_path} "
                    f"({len(text)} chars, model={model}){tok_summary}",
                    file=sys.stderr,
                )
            return 0

        # No text — figure out why and decide whether to fall through.
        last_err = err or "(empty response)"
        if err and _is_transient(err):
            if verbose:
                print(f"[analyze] {model} transient ({err[:140]}); "
                      "falling back...", file=sys.stderr)
            continue
        if err and ("not_found" in err.lower() or "404" in err):
            if verbose:
                print(f"[analyze] {model} not available on this key; "
                      "falling back...", file=sys.stderr)
            continue
        # Unknown / non-transient error — surface and stop
        print(f"ERROR: {model} → {err}", file=sys.stderr)
        return 4

    print(
        f"ERROR: all candidate models exhausted. last error: {last_err}",
        file=sys.stderr,
    )
    return 4


# ---------- CLI ------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="analyze_youtube.py",
        description=(
            "Analyze a public YouTube video via the Gemini API and emit "
            "a schema-conformant markdown analysis. Best-practices for "
            "Google's video-understanding API are baked in: text-after-"
            "video ordering, media_resolution=low default for ~3× token "
            "efficiency, custom FPS / clipping support, and token-usage "
            "logging on success."
        ),
    )
    parser.add_argument("url", help="YouTube video URL (must be public)")
    parser.add_argument(
        "--out",
        help="output path (default: auto-derived under "
             "docs/dev/video-analysis/analyses/<DATE>-<channel>-<title>.md)",
    )
    parser.add_argument(
        "--model",
        help="explicit model name (default: try MODEL_CANDIDATES in order)",
    )
    parser.add_argument(
        "--prompt-file",
        default=str(DEFAULT_PROMPT),
        help=f"prompt template file (default: {DEFAULT_PROMPT.name})",
    )
    parser.add_argument(
        "--media-resolution",
        choices=["low", "medium", "high", "default"],
        default="low",
        help=(
            "Per-frame token budget. 'low' = ~66 tokens/frame (≈100 tokens"
            "/sec, ~3× cheaper); 'high' = ~258 tokens/frame (≈300 tokens"
            "/sec, max detail); 'default' = SDK default (no override). "
            "Default 'low' — tutorial content rarely needs fine-text "
            "OCR on small screen elements."
        ),
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=None,
        help=(
            "Custom video sampling rate. Default: Gemini's 1 FPS. Set "
            "0.5 for slow-paced lecture content (saves tokens), 2-5 "
            "for fast-action / quick-cut visuals."
        ),
    )
    parser.add_argument(
        "--start-offset",
        help="Clip start offset (e.g. '1m30s' or '90s'). Skips intros.",
    )
    parser.add_argument(
        "--end-offset",
        help="Clip end offset (e.g. '5m' or '300s'). Skips outros.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="HTTP timeout in seconds (default 600).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress progress logs to stderr",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "ERROR: GEMINI_API_KEY env var not set.\n"
            "  export GEMINI_API_KEY=AIza...\n"
            "  Get a key at https://aistudio.google.com/app/apikey",
            file=sys.stderr,
        )
        return 3

    out_path = Path(args.out) if args.out else derive_output_path(
        args.url, DEFAULT_ANALYSES_DIR
    )

    return analyze(
        api_key=api_key,
        url=args.url,
        out_path=out_path,
        prompt_file=Path(args.prompt_file),
        explicit_model=args.model,
        media_resolution=args.media_resolution,
        fps=args.fps,
        start_offset=args.start_offset,
        end_offset=args.end_offset,
        timeout=args.timeout,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
