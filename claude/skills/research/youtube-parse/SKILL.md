---
name: youtube-parse
description: Fetch and analyze a YouTube video's transcript. Drop in a URL and get a summary of what the video covers.
trigger: /youtube-parse
---

# /youtube-parse

Fetch a YouTube video's transcript and analyze what it covers — without writing a one-off script every time.

## Usage

```
/youtube-parse <url>                      # fetch transcript and summarize
/youtube-parse <url> --full               # print full transcript + summary
/youtube-parse <url> --topics             # bullet list of topics only, no prose
/youtube-parse <url> --quotes             # pull notable quotes/claims
```

## Steps

### 1. Extract Video ID

Parse the URL to get the video ID:
- `https://www.youtube.com/watch?v=VIDEO_ID` → `VIDEO_ID`
- `https://youtu.be/VIDEO_ID` → `VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID` → `VIDEO_ID`
- Bare ID passed directly → use as-is

### 2. Fetch the Transcript

Try Method A first. If it fails (private video, no captions, region-locked), try Method B.

**Method A — youtube-transcript-api (cleanest output)**

```bash
# Install if missing
pip3 install youtube-transcript-api -q 2>/dev/null || pip install youtube-transcript-api -q 2>/dev/null

python3 - <<'PYEOF'
import sys, json
from youtube_transcript_api import YouTubeTranscriptApi
video_id = "VIDEO_ID"
try:
    entries = YouTubeTranscriptApi.get_transcript(video_id)
    text = " ".join(e["text"] for e in entries)
    print(text)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
```

**Method B — yt-dlp auto-subtitles fallback**

```bash
TMPDIR=$(mktemp -d)
yt-dlp \
  --write-auto-sub \
  --sub-lang en \
  --sub-format vtt \
  --skip-download \
  --output "$TMPDIR/video" \
  "https://www.youtube.com/watch?v=VIDEO_ID" 2>&1

# Find the downloaded .vtt file and strip markup
VTT=$(ls "$TMPDIR"/*.vtt 2>/dev/null | head -1)
if [ -z "$VTT" ]; then
  echo "No subtitles found." >&2
  exit 1
fi

# Strip VTT headers, timestamps, tags, and deduplicate lines
python3 - "$VTT" <<'PYEOF'
import sys, re
with open(sys.argv[1]) as f:
    raw = f.read()
lines = raw.split("\n")
seen = set()
out = []
for line in lines:
    line = line.strip()
    if not line or line.startswith("WEBVTT") or re.match(r"^\d+:\d+", line) or "-->" in line:
        continue
    cleaned = re.sub(r"<[^>]+>", "", line)  # strip <c>, <00:00:00.000> tags
    if cleaned and cleaned not in seen:
        seen.add(cleaned)
        out.append(cleaned)
print(" ".join(out))
PYEOF

rm -rf "$TMPDIR"
```

### 3. Validate

If both methods fail:
- Tell the user why (no captions, private/age-gated video, unsupported URL)
- Suggest they enable captions on the video or try a different URL

### 4. Analyze the Transcript

With the full transcript text, produce:

**TL;DR** (2–3 sentences)
What is this video fundamentally about? What does the speaker want you to walk away knowing?

**Key Topics** (bullet list)
The 5–10 main subjects, concepts, or arguments covered — enough to reconstruct the structure.

**Notable Quotes or Claims** (if meaningful ones exist)
Direct lifts from the transcript that are memorable, controversial, or important. Format as blockquotes.

**Takeaways / So What?**
What's actionable, interesting, or worth remembering from this video? Skip this section if the content is purely informational with no clear takeaways.

If `--full` was passed, print the full cleaned transcript before the analysis.
If `--topics` was passed, skip prose and just give the bullet list.
If `--quotes` was passed, focus on extracting verbatim claims and skip the summary.

## Notes

- `yt-dlp` is required for Method B: `brew install yt-dlp` or `pip install yt-dlp`
- `youtube-transcript-api` is auto-installed if missing (Method A)
- Auto-generated captions (the default on most videos) are accurate enough for analysis; manually uploaded transcripts are better when available
- Non-English videos: Method A will try the video's primary language; pass `--sub-lang <code>` to yt-dlp for Method B
