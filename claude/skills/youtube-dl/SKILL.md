---
name: youtube-dl
description: Download MP3 or MP4 from a YouTube URL using yt-dlp. Saves to ~/Downloads by default.
trigger: /youtube-dl
---

# /youtube-dl

Download audio or video from a YouTube link — no flags needed, just drop in a URL.

## Usage

```
/youtube-dl <url>                   # download best MP4 (default)
/youtube-dl <url> --mp3             # extract audio as MP3
/youtube-dl <url> --mp4             # download best quality MP4 (explicit)
/youtube-dl <url> --720             # MP4 capped at 720p
/youtube-dl <url> --1080            # MP4 capped at 1080p
/youtube-dl <url> --out ~/Desktop   # save to a different directory
/youtube-dl <url> --mp3 --out ~/Music
```

## Steps

### 1. Parse Arguments

- Extract the YouTube URL from the input
- Default format: MP4 best quality
- Default output directory: `~/Downloads`
- If `--mp3` flag present: audio-only MP3
- If `--720` or `--1080`: cap video resolution accordingly
- If `--out <path>` present: use that directory instead

### 2. Run the Download

**MP3 (audio only):**
```bash
yt-dlp \
  --extract-audio \
  --audio-format mp3 \
  --audio-quality 0 \
  --output "~/Downloads/%(title)s.%(ext)s" \
  --no-playlist \
  "<url>"
```

**MP4 best quality (default):**
```bash
yt-dlp \
  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  --output "~/Downloads/%(title)s.%(ext)s" \
  --no-playlist \
  "<url>"
```

**MP4 capped at 720p:**
```bash
yt-dlp \
  -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best" \
  --merge-output-format mp4 \
  --output "~/Downloads/%(title)s.%(ext)s" \
  --no-playlist \
  "<url>"
```

**MP4 capped at 1080p:**
```bash
yt-dlp \
  -f "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best" \
  --merge-output-format mp4 \
  --output "~/Downloads/%(title)s.%(ext)s" \
  --no-playlist \
  "<url>"
```

Substitute the output path with `--out` value if provided. Always expand `~` to the full home path.

### 3. Report Result

After the download completes, tell the user:
- The filename that was saved
- The full path where it landed
- The file size (use `ls -lh <path>` to get it)

If yt-dlp exits non-zero, show the error output and suggest:
- Age-restricted / private video: may need cookies (`yt-dlp --cookies-from-browser chrome <url>`)
- ffmpeg missing for MP3 conversion: `brew install ffmpeg`
- Rate limited: try again in a moment

## Requirements

- `yt-dlp` — already installed at `/opt/homebrew/bin/yt-dlp`
- `ffmpeg` — required for MP3 extraction and for merging separate video+audio streams: `brew install ffmpeg`
