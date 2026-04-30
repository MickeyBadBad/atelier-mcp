#!/usr/bin/env python3
"""Analyze a YouTube video via Google's native Gemini API → schema-conformant md.

Companion to docs/dev/video-analysis/ workflow. Replaces the manual
"open AI Studio, paste prompt, save output" loop with a one-shot
command.

Usage:
    export GEMINI_API_KEY=AIza...
    scripts/analyze_youtube.py "https://www.youtube.com/watch?v=..." \\
        [--out docs/dev/video-analysis/analyses/2026-05-01-channel-topic.md] \\
        [--model gemini-3-flash-preview] \\
        [--prompt-file docs/dev/video-analysis/prompts/gemini-full-video.md]

If --out is omitted, the script auto-derives a filename from the video's
title via YouTube's oEmbed endpoint (no auth needed).

If --prompt-file is omitted, uses the canonical schema prompt at
docs/dev/video-analysis/prompts/gemini-full-video.md.

Model fallback order (best-first; each can fail with 429/503 and the
next is tried automatically):

    gemini-3.1-pro-preview          (paid; usually 0 quota on free tier)
    gemini-3.1-flash-lite-preview   (preview; sometimes 503)
    gemini-3-pro-preview            (paid; usually 0 quota on free tier)
    gemini-3-flash-preview          (free tier ✓ as of 2026-05-01)
    gemini-pro-latest               (alias)
    gemini-flash-latest             (alias)
    gemini-2.5-flash                (free tier ✓ stable fallback)
    gemini-2.5-pro                  (paid)
    gemini-2.0-flash                (free tier)

Exit codes:
    0  analysis written successfully
    2  bad arguments
    3  GEMINI_API_KEY not set
    4  all model candidates exhausted
    5  prompt file or output path failed
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

MODEL_CANDIDATES = (
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-pro-latest",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT = (
    REPO_ROOT
    / "docs/dev/video-analysis/prompts/gemini-full-video.md"
)
DEFAULT_ANALYSES_DIR = REPO_ROOT / "docs/dev/video-analysis/analyses"


def _http(method: str, url: str, *, payload=None, timeout=600):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            return e.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return e.code, raw
    except urllib.error.URLError as e:
        return -1, f"URLError: {e.reason}"


def fetch_video_metadata(url: str) -> dict:
    """Use YouTube's oEmbed (no auth) to get title + author for the slug."""
    oembed = (
        "https://www.youtube.com/oembed?"
        + urllib.parse.urlencode({"url": url, "format": "json"})
    )
    status, resp = _http("GET", oembed)
    if status == 200 and isinstance(resp, dict):
        return {
            "title": resp.get("title", ""),
            "author": resp.get("author_name", ""),
        }
    return {"title": "", "author": ""}


def slugify(s: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower(), flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "_", s).strip("_")
    return s[:max_len] or "untitled"


def derive_output_path(url: str, analyses_dir: Path) -> Path:
    meta = fetch_video_metadata(url)
    today = datetime.date.today().isoformat()
    author_slug = slugify(meta["author"]) or "unknown_channel"
    title_slug = slugify(meta["title"]) or "untitled"
    return analyses_dir / f"{today}-{author_slug}-{title_slug}.md"


def load_prompt(
    prompt_file: Path,
    url: str,
    metadata: dict | None = None,
) -> str:
    """Load the prompt template, substitute the URL, and inject oEmbed
    metadata as ground-truth so Gemini doesn't hallucinate the channel /
    title (it sometimes guesses these from video content when the visual
    branding isn't shown).
    """
    text = prompt_file.read_text(encoding="utf-8")
    # Strip everything before the first ---  separator (the human preface)
    parts = text.split("\n---\n", 1)
    body = parts[1] if len(parts) == 2 else text
    body = body.replace("<URL>", url)

    if metadata and (metadata.get("title") or metadata.get("author")):
        ground_truth = (
            "\n\n# Known facts (do NOT re-detect — use these verbatim "
            "in the Source section)\n\n"
            f"- URL: {url}\n"
            f"- Channel: {metadata.get('author', '')}\n"
            f"- Title: {metadata.get('title', '')}\n\n"
            "These were fetched from YouTube oEmbed before this prompt; "
            "they are authoritative. Do NOT guess Channel from the video "
            "content — copy the value above. Only DETECT fields that "
            "aren't pre-supplied (Length, Published date, etc.).\n"
        )
        body = ground_truth + body
    return body


def call_gemini(
    api_key: str,
    model: str,
    youtube_url: str,
    prompt_text: str,
    timeout: int = 600,
) -> tuple[int, dict | str]:
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "file_data": {
                            "file_uri": youtube_url,
                        }
                    },
                    {"text": prompt_text},
                ]
            }
        ],
    }
    url = f"{GEMINI_BASE}/models/{model}:generateContent?key={api_key}"
    return _http("POST", url, payload=payload, timeout=timeout)


def extract_text(resp) -> str:
    if not isinstance(resp, dict):
        return str(resp)
    if "candidates" in resp:
        try:
            parts = resp["candidates"][0]["content"]["parts"]
            return "\n".join(
                p.get("text", "") for p in parts if isinstance(p, dict)
            )
        except Exception:
            pass
    if "error" in resp:
        return f"[error] {json.dumps(resp['error'], ensure_ascii=False)}"
    return json.dumps(resp, ensure_ascii=False)[:1500]


def list_models(api_key: str) -> set[str]:
    url = f"{GEMINI_BASE}/models?key={api_key}"
    status, resp = _http("GET", url)
    if status != 200 or not isinstance(resp, dict):
        return set()
    out = set()
    for m in resp.get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            out.add(m.get("name", "").replace("models/", ""))
    return out


def analyze(
    api_key: str,
    url: str,
    out_path: Path,
    prompt_file: Path,
    explicit_model: Optional[str] = None,
    verbose: bool = True,
) -> int:
    if verbose:
        print(f"[analyze] video: {url}", file=sys.stderr)
        print(f"[analyze] output: {out_path}", file=sys.stderr)

    if not prompt_file.is_file():
        print(f"ERROR: prompt file not found: {prompt_file}", file=sys.stderr)
        return 5

    metadata = fetch_video_metadata(url)
    if verbose and metadata.get("author"):
        print(
            f"[analyze] oEmbed → channel={metadata['author']!r}, "
            f"title={metadata['title'][:60]!r}",
            file=sys.stderr,
        )
    prompt_text = load_prompt(prompt_file, url, metadata=metadata)

    available = list_models(api_key)
    if not available:
        print(
            "ERROR: cannot list models (key invalid or rate-limited)",
            file=sys.stderr,
        )
        return 4

    if explicit_model:
        candidates = [explicit_model]
    else:
        candidates = [m for m in MODEL_CANDIDATES if m in available]

    if not candidates:
        print(
            f"ERROR: no candidate models available. Tried: "
            f"{list(MODEL_CANDIDATES)}; available: {sorted(available)[:10]}...",
            file=sys.stderr,
        )
        return 4

    last_err = None
    for model in candidates:
        if verbose:
            print(f"[analyze] trying model: {model}", file=sys.stderr)
        status, resp = call_gemini(api_key, model, url, prompt_text)
        if status == 200:
            text = extract_text(resp)
            if not text or text.startswith("[error]"):
                if verbose:
                    print(
                        f"[analyze] {model} returned empty/error body, "
                        f"trying next...",
                        file=sys.stderr,
                    )
                last_err = text
                continue

            out_path.parent.mkdir(parents=True, exist_ok=True)
            header = (
                f"<!-- generated by scripts/analyze_youtube.py "
                f"on {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} "
                f"using model={model} -->\n\n"
            )
            out_path.write_text(header + text, encoding="utf-8")
            if verbose:
                print(
                    f"[analyze] ✓ written: {out_path} "
                    f"({len(text)} chars, model={model})",
                    file=sys.stderr,
                )
            return 0
        if status in (429, 503):
            if verbose:
                reason = "quota" if status == 429 else "service unavailable"
                print(
                    f"[analyze] {model} {reason} ({status}), falling back...",
                    file=sys.stderr,
                )
            last_err = f"status {status}: {str(resp)[:200]}"
            continue
        # Other errors — surface and stop
        print(
            f"ERROR: {model} returned status {status}: {str(resp)[:1000]}",
            file=sys.stderr,
        )
        return 4

    print(
        f"ERROR: all candidate models exhausted. last error: {last_err}",
        file=sys.stderr,
    )
    return 4


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="analyze_youtube.py",
        description=(
            "Analyze a YouTube video via Google Gemini → schema-"
            "conformant markdown."
        ),
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--out",
        help="output path (default: auto-derived under docs/dev/"
        "video-analysis/analyses/)",
    )
    parser.add_argument(
        "--model",
        help="explicit model (default: try MODEL_CANDIDATES in order)",
    )
    parser.add_argument(
        "--prompt-file",
        default=str(DEFAULT_PROMPT),
        help=f"prompt template (default: {DEFAULT_PROMPT.name})",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="suppress progress logs",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "ERROR: GEMINI_API_KEY env var not set.\n"
            "  export GEMINI_API_KEY=AIza...",
            file=sys.stderr,
        )
        return 3

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = derive_output_path(args.url, DEFAULT_ANALYSES_DIR)

    return analyze(
        api_key=api_key,
        url=args.url,
        out_path=out_path,
        prompt_file=Path(args.prompt_file),
        explicit_model=args.model,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
