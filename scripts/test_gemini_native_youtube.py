#!/usr/bin/env python3
"""Test native Google Gemini API with YouTube URL.

Two probes:

  1. List available models for the API key (so we know what to call).
  2. Submit the test YouTube URL via file_data.file_uri to the most
     capable model that the key has access to. Native Gemini supports
     YouTube URLs directly — should return a real video analysis.

Test video is the same coral lab Japandi tutorial we already analyzed
by hand. Ground-truth tokens (1024 / kloppenheim / Magic UV / Light
Path / translucent / calibration) confirm whether the model genuinely
analyzed the video.

Usage:
    export GEMINI_API_KEY=AIza...
    python3 scripts/test_gemini_native_youtube.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


YT_URL = "https://www.youtube.com/watch?v=Yf9jAlmxEYM"
EXPECTED_TOKENS = (
    "1024", "kloppenheim", "Magic UV", "calibration",
    "Light Path", "translucent",
)
THRESHOLD = 2

# Models to try in order of preference. Gemini 3.x is current as of
# 2026-05; some 3.x previews are free-tier-eligible while top pro
# variants are usually paid. We try strongest-first and fall back on
# 429 quota errors.
MODEL_CANDIDATES = (
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-pro-latest",      # alias — usually resolves to current pro
    "gemini-flash-latest",    # alias — usually resolves to current flash
    "gemini-2.5-flash",       # confirmed working free-tier
    "gemini-2.5-pro",         # likely paid-only (limit 0 on free)
    "gemini-2.0-flash",
)

BASE = "https://generativelanguage.googleapis.com/v1beta"


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


def list_models(api_key: str) -> list[str]:
    """Return list of model names the key has access to."""
    url = f"{BASE}/models?key={api_key}"
    status, resp = _http("GET", url)
    if status != 200 or not isinstance(resp, dict):
        print(f"  [ERROR] list_models: status={status}, resp={str(resp)[:300]}", file=sys.stderr)
        return []
    out = []
    for m in resp.get("models", []):
        name = m.get("name", "").replace("models/", "")
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            out.append(name)
    return out


def pick_model(available: list[str]) -> str | None:
    """Pick the best available model from our preference list."""
    avail_set = set(available)
    for cand in MODEL_CANDIDATES:
        if cand in avail_set:
            return cand
    # fallback: pick first 2.5 / 2.0 model
    for m in available:
        if "2.5" in m or "2.0" in m:
            return m
    if available:
        return available[0]
    return None


def analyze_video(api_key: str, model: str) -> dict:
    """Submit the YouTube URL with file_data.file_uri."""
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "file_data": {
                            "file_uri": YT_URL,
                            # Don't set mime_type — Gemini infers
                        }
                    },
                    {
                        "text": (
                            "Watch this entire YouTube video carefully. "
                            "Extract these specific UI-visible values and "
                            "tools the creator uses:\n\n"
                            "1. Cycles samples count (the number in Render "
                            "Properties → Sampling → Render → Max Samples)\n"
                            "2. The HDRI filename (e.g. kloppenheim_06_*.hdr)\n"
                            "3. HDRI strength value\n"
                            "4. Camera focal length in mm\n"
                            "5. Any UV addon mentioned (e.g. 'Magic UV')\n"
                            "6. The technique used to disable curtain shadow "
                            "casting (Light Path node? which output?)\n"
                            "7. The calibration spheres technique — list how "
                            "many spheres and what colors/properties\n"
                            "8. The translucent material setup for the "
                            "pendant lamp\n\n"
                            "Be specific with numbers. Do not generalize."
                        )
                    }
                ]
            }
        ],
    }
    url = f"{BASE}/models/{model}:generateContent?key={api_key}"
    return _http("POST", url, payload=payload)


def extract_text(resp) -> str:
    if not isinstance(resp, dict):
        return str(resp)
    if "candidates" in resp:
        try:
            parts = resp["candidates"][0]["content"]["parts"]
            return "\n".join(p.get("text", "") for p in parts if isinstance(p, dict))
        except Exception:
            return json.dumps(resp, ensure_ascii=False)[:1500]
    if "error" in resp:
        return f"[error] {json.dumps(resp['error'], ensure_ascii=False)}"
    return json.dumps(resp, ensure_ascii=False)[:1500]


def verdict(text: str) -> tuple[str, list[str]]:
    if not text or text.startswith("[error]"):
        return "❌ ERROR", []
    hits = [t for t in EXPECTED_TOKENS if t.lower() in text.lower()]
    if len(hits) >= THRESHOLD:
        return f"✅ ANALYZED ({len(hits)}/{len(EXPECTED_TOKENS)} tokens matched)", hits
    if len(hits) == 1:
        return "⚠️  WEAK SIGNAL", hits
    return "❌ HALLUCINATED", hits


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: set GEMINI_API_KEY env var.", file=sys.stderr)
        return 2

    print(f"Native Gemini probe — endpoint={BASE}")
    print(f"Test video: {YT_URL}\n")

    print("Step 1 — list models the key has access to...")
    available = list_models(api_key)
    print(f"  found {len(available)} models with generateContent support")
    if available:
        print(f"  first 10: {available[:10]}")

    if not available:
        print("\n❌ No models accessible — key invalid or restricted.")
        return 3

    # Try each candidate in priority order; fall back on quota / 429
    avail_set = set(available)
    tried = []
    status = -1
    resp = None
    model = None
    for cand in MODEL_CANDIDATES:
        if cand not in avail_set:
            continue
        tried.append(cand)
        print(f"\nStep 2 — trying model: {cand}")
        print(f"Submitting YouTube URL via file_data.file_uri...")
        print(f"(can take 1-3 minutes for a 12-min video)\n")
        status, resp = analyze_video(api_key, cand)
        print(f"  HTTP status: {status}")
        if status == 200:
            model = cand
            break
        if status in (429, 503):
            reason = "quota exceeded" if status == 429 else "service unavailable"
            print(f"  {reason} for {cand}, falling back...")
            continue
        # other error — surface and stop
        print(f"  error response: {str(resp)[:1500]}")
        return 4

    if status != 200:
        print(f"\n❌ All candidates exhausted. Tried: {tried}")
        print(f"  last response: {str(resp)[:800]}")
        return 4
    print(f"  ✓ used model: {model}")

    text = extract_text(resp)
    v, hits = verdict(text)
    print(f"\n  verdict: {v}")
    print(f"  matched tokens: {hits}")

    print(f"\n--- Response (first 2500 chars) ---")
    print(text[:2500])

    if "✅" in v:
        print(f"\n{'=' * 72}")
        print("SUCCESS — native Gemini reads YouTube URLs correctly.")
        print(f"Use model '{model}' for the production skill.")
        print(f"This is the path: ai.google.dev directly, no Comfly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
