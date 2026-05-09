#!/usr/bin/env -S uv run python
"""Test the official `google-genai` SDK's video understanding paths.

Per https://ai.google.dev/gemini-api/docs/video-understanding the SDK
supports three input modes:

  1. YouTube URL passthrough (preview, no upload, public videos only)
  2. Files API upload (recommended for production; reusable file refs)
  3. Inline base64 data (<20MB total request size)

Our existing scripts/analyze_youtube.py uses raw urllib HTTP against
the REST endpoint with mode (1). This script tests the SAME mode via
the official SDK to validate it works end-to-end and to compare.

Usage:
    GEMINI_API_KEY=AIza... ./scripts/test_genai_sdk.py [YOUTUBE_URL]

Prints:
    - Smoke test: 3-sentence summary (cheap, validates SDK + key + path)
    - Side-by-side: response.text length / first 500 chars
    - Latency stamp

The full schema-conformant analysis (the one we use in synthesis-log)
isn't in scope here — we're only validating the SDK works. If this
passes, scripts/analyze_youtube.py can be optionally refactored to
the SDK for cleaner error handling + retry / streaming support.
"""
from __future__ import annotations
import argparse
import os
import sys
import time

DEFAULT_URL = "https://www.youtube.com/watch?v=dJFRExW0emA"  # CGi Jutsu, ~3 min, used Round 6


def smoke_test(url: str, model: str = "gemini-3-flash-preview") -> None:
    """Minimal SDK call: YouTube URL + 3-sentence summary."""
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY env var not set", file=sys.stderr)
        sys.exit(2)

    client = genai.Client(api_key=api_key)
    print(f"[sdk-test] model={model}  url={url}")
    print(f"[sdk-test] sending request...")

    t0 = time.monotonic()
    response = client.models.generate_content(
        model=model,
        contents=types.Content(
            parts=[
                types.Part(file_data=types.FileData(file_uri=url)),
                types.Part(text="Summarize this video in 3 sentences. "
                                "Then list the 3 most concrete numeric "
                                "values mentioned (e.g. 'Dispersion 0.02')."),
            ]
        ),
    )
    elapsed = time.monotonic() - t0

    text = response.text or "(empty)"
    print(f"[sdk-test] HTTP/SDK ok   elapsed={elapsed:.1f}s   "
          f"response_chars={len(text)}")
    print(f"[sdk-test] usage_metadata={getattr(response, 'usage_metadata', None)!r}")
    print()
    print("=" * 70)
    print("RESPONSE TEXT")
    print("=" * 70)
    print(text)
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", default=DEFAULT_URL,
                        help=f"YouTube URL (default: {DEFAULT_URL})")
    parser.add_argument("--model", default="gemini-3-flash-preview",
                        help="Gemini model name (default: gemini-3-flash-preview)")
    args = parser.parse_args()
    smoke_test(args.url, args.model)


if __name__ == "__main__":
    main()
