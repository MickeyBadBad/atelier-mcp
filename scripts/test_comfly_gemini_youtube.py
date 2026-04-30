#!/usr/bin/env python3
"""Test whether Comfly's OpenAI-compatible API can analyze YouTube videos via Gemini.

Tests 4 request shapes in order of likelihood-to-work:

  1. OpenAI chat-completions, YouTube URL as plain text + ask model to analyze
     → tests if model can fetch URLs itself (it cannot via OpenAI format —
     this confirms hallucination if it returns content)

  2. OpenAI chat-completions, YouTube URL in `image_url` content part
     → tests if Comfly transparently maps to Gemini's video input (unusual
     but some relays do extend the spec)

  3. Native Gemini /models/<model>:generateContent endpoint with file_data
     part containing the YouTube URL
     → the canonical Gemini format; works iff Comfly forwards native
     Gemini API (some relays expose both shapes)

  4. Same as 3 but via OpenAI base_url's /completions endpoint with a
     custom `youtube_url` field (some relays accept this)

For each test, prints: HTTP status, response shape, first 500 chars of
content, and a verdict on whether the model actually analyzed the video
(by checking for specific UI-visible details vs generic hallucinations).

Usage:
    export COMFLY_API_KEY=sk-...                # required
    export COMFLY_BASE_URL=https://ai.comfly.chat/v1   # optional, this is the default
    python3 scripts/test_comfly_gemini_youtube.py

Test video: the same one we already analyzed by hand (coral lab Japandi
tutorial, https://www.youtube.com/watch?v=Yf9jAlmxEYM). The expected
ground-truth includes specific UI values like Cycles 1024 samples,
HDRI strength 5.0, focal length 50mm, kloppenheim_06_puresky_8k.hdr.
If a test response cites these specifics, the model genuinely analyzed
the video. If it returns generic Japandi description without these
numbers, it hallucinated from the URL alone.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


YT_URL = "https://www.youtube.com/watch?v=Yf9jAlmxEYM"
EXPECTED_GROUND_TRUTH_TOKENS = (
    "1024",                          # Cycles samples
    "kloppenheim",                   # HDRI name
    "Magic UV",                      # tool referenced
    "calibration",                   # technique
    "Light Path",                    # node used
    "translucent",                   # paper lamp shader
)
GROUND_TRUTH_THRESHOLD = 2  # need 2+ specific tokens to be confident the model actually analyzed

DEFAULT_MODEL = "gemini-3.1-pro-preview-thinking-high"


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 240) -> tuple[int, dict | str]:
    """POST JSON; return (status_code, parsed_response or raw_text)."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = raw
        return e.code, parsed
    except urllib.error.URLError as e:
        return -1, f"URLError: {e.reason}"
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def _extract_text(resp) -> str:
    """Best-effort text extraction from OpenAI / Gemini-shaped responses."""
    if isinstance(resp, str):
        return resp
    if not isinstance(resp, dict):
        return repr(resp)
    if "choices" in resp:
        try:
            return resp["choices"][0]["message"]["content"]
        except Exception:
            pass
    if "candidates" in resp:
        try:
            parts = resp["candidates"][0]["content"]["parts"]
            return "\n".join(p.get("text", "") for p in parts if isinstance(p, dict))
        except Exception:
            pass
    if "error" in resp:
        return f"[error] {json.dumps(resp['error'], ensure_ascii=False)}"
    return json.dumps(resp, ensure_ascii=False)[:1500]


def _verdict(text: str) -> str:
    """Did the model actually analyze the video, or hallucinate from URL?"""
    if not text or text.startswith("[error]"):
        return "❌ ERROR (no text returned)"
    hits = [tok for tok in EXPECTED_GROUND_TRUTH_TOKENS if tok.lower() in text.lower()]
    if len(hits) >= GROUND_TRUTH_THRESHOLD:
        return f"✅ LIKELY ANALYZED (matched {len(hits)} ground-truth tokens: {hits})"
    if len(hits) == 1:
        return f"⚠️  WEAK SIGNAL (1 token match: {hits[0]} — could be coincidence)"
    return f"❌ LIKELY HALLUCINATED (0 of {len(EXPECTED_GROUND_TRUTH_TOKENS)} ground-truth tokens — generic Japandi-style content)"


def _print_result(label: str, status: int, response, model: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"TEST: {label}")
    print(f"  model: {model}")
    print(f"  HTTP status: {status}")
    if status == -1:
        print(f"  network/transport error: {response}")
        return
    text = _extract_text(response)
    print(f"  response (first 800 chars):")
    print(f"    {text[:800]!r}")
    print(f"  verdict: {_verdict(text)}")


# ============================================================================
# Test 1 — Plain text URL (control: confirms hallucination shape)
# ============================================================================

def test_plain_text(base_url: str, api_key: str, model: str) -> None:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Watch this YouTube video and tell me, with exact numeric "
                    f"values shown on screen: what samples count is set in "
                    f"Cycles, what HDRI file is used, what HDRI strength, "
                    f"what focal length, and what UV addon is mentioned.\n\n"
                    f"Video URL: {YT_URL}"
                ),
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = base_url.rstrip("/") + "/chat/completions"
    status, resp = _post_json(url, payload, headers)
    _print_result("1. OpenAI chat — URL in plain text", status, resp, model)


# ============================================================================
# Test 2 — image_url content part with YouTube URL
# ============================================================================

def test_image_url_field(base_url: str, api_key: str, model: str) -> None:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Watch this YouTube video and tell me: Cycles "
                            "samples count, HDRI filename, HDRI strength, "
                            "focal length, and any UV addon mentioned. "
                            "Numeric values must come from the on-screen UI."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": YT_URL},
                    },
                ],
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = base_url.rstrip("/") + "/chat/completions"
    status, resp = _post_json(url, payload, headers)
    _print_result("2. OpenAI chat — image_url part (YouTube URL)", status, resp, model)


# ============================================================================
# Test 3 — Gemini-native generateContent with file_data
# ============================================================================

def test_gemini_native(base_url: str, api_key: str, model: str) -> None:
    """Tries the native Gemini API shape. If Comfly forwards as Gemini-native,
    this is the canonical path."""
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "file_data": {
                            "file_uri": YT_URL,
                            "mime_type": "video/*",
                        },
                    },
                    {
                        "text": (
                            "Watch this video. List exact on-screen UI values: "
                            "Cycles samples, HDRI filename, HDRI strength, "
                            "focal length, UV addon mentioned, and one direct "
                            "quote ≤ 2 lines."
                        ),
                    },
                ],
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    base_no_v1 = base_url.rstrip("/")
    if base_no_v1.endswith("/v1"):
        base_no_v1 = base_no_v1[:-3]
    candidates = [
        # Comfly /v1 alongside OpenAI-style chat
        f"{base_url.rstrip('/')}/models/{model}:generateContent",
        # Native Gemini path (without /v1 prefix)
        f"{base_no_v1}/v1beta/models/{model}:generateContent",
    ]
    for url in candidates:
        status, resp = _post_json(url, payload, headers)
        _print_result(
            f"3. Gemini-native :generateContent at {url.split('/v')[-1] if '/v' in url else 'root'}",
            status, resp, model,
        )
        if status == 200:
            return  # don't try fallbacks if first works


# ============================================================================
# Test 4 — OpenAI chat with custom youtube_url field (Comfly extension probe)
# ============================================================================

def test_custom_youtube_url(base_url: str, api_key: str, model: str) -> None:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Watch this YouTube video and tell me: Cycles samples, "
                    "HDRI filename, HDRI strength, focal length, UV addon."
                ),
            }
        ],
        # Custom extensions some Gemini relays accept:
        "video_url": YT_URL,
        "youtube_url": YT_URL,
        "extra_body": {"video_url": YT_URL, "youtube_url": YT_URL},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = base_url.rstrip("/") + "/chat/completions"
    status, resp = _post_json(url, payload, headers)
    _print_result("4. OpenAI chat — custom youtube_url field", status, resp, model)


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    api_key = os.environ.get("COMFLY_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("COMFLY_BASE_URL", "https://ai.comfly.chat/v1")
    model = os.environ.get("COMFLY_MODEL", DEFAULT_MODEL)

    if not api_key:
        print("ERROR: COMFLY_API_KEY env var not set. Run:", file=sys.stderr)
        print("  export COMFLY_API_KEY=sk-...", file=sys.stderr)
        print("  python3 scripts/test_comfly_gemini_youtube.py", file=sys.stderr)
        return 2

    print(f"Comfly probe — model={model}, base_url={base_url}")
    print(f"Test video: {YT_URL}")
    print(f"Ground-truth tokens to match: {EXPECTED_GROUND_TRUTH_TOKENS}")
    print(f"Threshold for 'analyzed': {GROUND_TRUTH_THRESHOLD}+ tokens")

    test_plain_text(base_url, api_key, model)
    test_image_url_field(base_url, api_key, model)
    test_gemini_native(base_url, api_key, model)
    test_custom_youtube_url(base_url, api_key, model)

    print(f"\n{'=' * 72}")
    print("SUMMARY: any test marked '✅ LIKELY ANALYZED' is the request shape")
    print("we should use to build the YouTube-search skill.")
    print("If only test 1 passes (plain text), the model is hallucinating from")
    print("URL string alone and we cannot use Comfly for actual video content;")
    print("fall back to the yt-dlp transcript path (workflow Path B).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
