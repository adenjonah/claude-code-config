---
name: extract-image
description: Extract specific diagrams or figures from a PDF by describing what you're looking for. Two-pass approach — finds the page, then crops the exact image. Outputs to ~/notes/ images directory by default.
user-invocable: true
argument-hint: "<pdf-path> --description <what to find> [--output <path>] [--page-range N-M]"
---

# Extract Image

Pull a specific diagram, figure, or chart out of a PDF by describing it. Uses Gemini to find the page and crop the exact region.

## Usage

```
/extract-image path/to/file.pdf --description "the supply and demand diagram" --output ~/notes/images/supply-demand.png
/extract-image path/to/slides.pdf --description "the NATO expansion map" --page-range 5-15
```

## How to Execute

```bash
# Single extraction
python3 ~/.claude/skills/education/extract-image/extract_image.py \
  --pdf <PDF_PATH> \
  --description "<what the image shows>" \
  --output <OUTPUT_PATH> \
  [--page-range N-M]

# Batch extraction (multiple images from the same range)
python3 ~/.claude/skills/education/extract-image/extract_image.py \
  --pdf <PDF_PATH> \
  --page-range N-M \
  --batch manifest.json
```

**Batch manifest format:**
```json
[
  {"description": "first diagram", "output": "~/notes/images/diagram1.png"},
  {"description": "second diagram", "output": "~/notes/images/diagram2.png"}
]
```

## Default output location

If no `--output` is specified, save to `~/notes/images/<pdf-basename>-<slug>.png`.

## How it works

1. Rasterizes pages at low res, sends to Gemini Pro to find which page has the target
2. Rasterizes that page at 300 DPI, asks Gemini to return a bounding box
3. Crops the image with PIL and saves it

## Embed in Obsidian notes

After extracting, embed with: `![[filename.png]]`

## Requirements (all installed)

- `poppler` — `pdftoppm`, `pdfimages`, `pdfinfo` CLIs
- `Pillow` — Python image cropping
- `google-genai` — Gemini API client
- `GEMINI_API_KEY` env var (already set in ~/.zshrc)

## Page range tip

When used alongside `condense-notes`, the `--page-range` must exactly match the `pages` parameter from the `Read()` call on the same PDF section.
