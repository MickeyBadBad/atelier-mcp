#!/usr/bin/env bash
# yt-transcript.sh — fallback for Path B of the video-analysis workflow.
#
# Pulls auto-generated subtitles from a YouTube URL via yt-dlp, parses the
# VTT to plain text, and prints to stdout. Use when no Gemini access is
# available; pair with docs/dev/video-analysis/prompts/transcript-only.md.
#
# Requires: yt-dlp (`brew install yt-dlp` or `pip install yt-dlp`)
#
# Usage:
#   scripts/yt-transcript.sh "https://www.youtube.com/watch?v=..." > /tmp/transcript.txt
#
# Then hand /tmp/transcript.txt + the prompt to Claude:
#   "Analyze this transcript using docs/dev/video-analysis/prompts/transcript-only.md"

set -euo pipefail

URL="${1:-}"
if [[ -z "$URL" ]]; then
    echo "usage: $0 <youtube-url>" >&2
    exit 2
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
    echo "error: yt-dlp not installed. Try:" >&2
    echo "  brew install yt-dlp     # macOS" >&2
    echo "  pip install yt-dlp      # any platform" >&2
    exit 3
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Pull auto-generated subs (English first; fall back to whatever's there)
yt-dlp \
    --skip-download \
    --write-auto-subs \
    --sub-langs "en.*,zh.*,ja.*,fr.*,de.*,es.*" \
    --sub-format vtt \
    --convert-subs vtt \
    --output "$WORK/sub" \
    "$URL" >/dev/null 2>&1 || {
    echo "error: yt-dlp failed to fetch subs for $URL" >&2
    echo "(some videos disable auto-subs; try a different one or use Gemini)" >&2
    exit 4
}

VTT_FILE="$(ls "$WORK"/sub.* 2>/dev/null | head -1)"
if [[ -z "$VTT_FILE" || ! -f "$VTT_FILE" ]]; then
    echo "error: no subtitle file produced (subs may be unavailable)" >&2
    exit 5
fi

# Strip VTT timing lines and merge into plain text. Preserve timestamps as
# light annotations so the analyzer can quote with timecodes.
awk '
BEGIN { last = "" }
/^WEBVTT/ { next }
/^NOTE / { next }
/^Kind: / || /^Language: / { next }
/^[0-9]{2}:[0-9]{2}:[0-9]{2}/ {
    split($1, parts, ".")
    last = parts[1]
    next
}
/^[[:space:]]*$/ { next }
{
    gsub(/<[^>]*>/, "")
    line = $0
    if (line == prev) next
    if (last != "") {
        printf "[%s] %s\n", last, line
        last = ""
    } else {
        printf "         %s\n", line
    }
    prev = line
}
' "$VTT_FILE"
