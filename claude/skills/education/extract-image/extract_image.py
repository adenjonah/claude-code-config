#!/usr/bin/env python3
"""Extract specific images/diagrams from a PDF by description.

Two-pass approach:
1. Rasterize page range at low res, ask Gemini Pro which pages have the targets + refine descriptions
2. Rasterize those pages at high res, ask Gemini Flash for bounding boxes, crop with PIL

Supports single extraction or batch mode (multiple descriptions, one Pro call).

Usage:
    # Single extraction
    extract_image.py --pdf INPUT.pdf --description "diagram" --output out.png --page-range 5-10

    # Batch extraction (one Pro call for all descriptions in the same range)
    extract_image.py --pdf INPUT.pdf --page-range 5-10 --batch manifest.json

    manifest.json format:
    [
      {"description": "first diagram...", "output": "/path/to/out1.png"},
      {"description": "second diagram...", "output": "/path/to/out2.png"}
    ]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


def get_client():
    from google import genai
    return genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


MODEL_FLASH = "gemini-2.0-flash"
MODEL_PRO = "gemini-1.5-pro"


def try_embedded_extraction(pdf_path: str, page: int | None, description: str, output: str) -> bool:
    """Try extracting embedded images with pdfimages. Return True if we found a match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ["pdfimages", "-png"]
        if page is not None:
            cmd += ["-f", str(page), "-l", str(page)]
        cmd += [pdf_path, os.path.join(tmpdir, "img")]

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            return False

        extracted = sorted(Path(tmpdir).glob("img-*.png"))
        if not extracted:
            return False

        if len(extracted) == 1:
            import shutil
            shutil.copy2(extracted[0], output)
            print(json.dumps({"status": "ok", "method": "embedded", "path": output}))
            return True

        from PIL import Image
        client = get_client()

        for img_path in extracted:
            img = Image.open(img_path)
            response = client.models.generate_content(
                model=MODEL_FLASH,
                contents=[
                    img,
                    f'Does this image match the description: "{description}"? '
                    'Reply with just {{"match": true}} or {{"match": false}}.'
                ],
                config={"response_mime_type": "application/json"},
            )
            try:
                r = json.loads(response.text)
                if r.get("match"):
                    import shutil
                    shutil.copy2(img_path, output)
                    print(json.dumps({"status": "ok", "method": "embedded", "path": output}))
                    return True
            except (json.JSONDecodeError, KeyError):
                continue

        return False


def rasterize_thumbnails(pdf_path: str, first_page: int, last_page: int, tmpdir: str) -> list[tuple[int, str]]:
    """Rasterize pages at low res. Returns [(page_num, path), ...]."""
    cmd = ["pdftoppm", "-png", "-r", "72",
           "-f", str(first_page), "-l", str(last_page),
           pdf_path, os.path.join(tmpdir, "thumb")]
    subprocess.run(cmd, capture_output=True, check=True)
    thumbs = sorted(Path(tmpdir).glob("thumb-*.png"))
    return [(first_page + i, str(p)) for i, p in enumerate(thumbs)]


def rasterize_page_hires(pdf_path: str, page: int, tmpdir: str) -> str | None:
    """Rasterize a single page at 300 DPI. Returns path to PNG."""
    prefix = os.path.join(tmpdir, f"hires-{page}")
    cmd = ["pdftoppm", "-png", "-r", "300",
           "-f", str(page), "-l", str(page),
           pdf_path, prefix]
    subprocess.run(cmd, capture_output=True, check=True)
    results = sorted(Path(tmpdir).glob(f"hires-{page}-*.png"))
    return str(results[0]) if results else None


def find_pages_batch(pdf_path: str, first_page: int, last_page: int,
                     descriptions: list[str]) -> list[tuple[int | None, str]]:
    """One Pro call: find pages + refine descriptions for ALL items.

    Returns list of (page_number, refined_description) in same order as descriptions.
    """
    from PIL import Image
    client = get_client()

    with tempfile.TemporaryDirectory() as tmpdir:
        pages = rasterize_thumbnails(pdf_path, first_page, last_page, tmpdir)
        if not pages:
            return [(None, d) for d in descriptions]

        contents = []
        for page_num, thumb_path in pages:
            contents.append(f"Page {page_num}:")
            contents.append(Image.open(thumb_path))

        # Build numbered description list
        desc_list = "\n".join(f"  {i}: \"{d}\"" for i, d in enumerate(descriptions))

        contents.append(
            f'I need to find these diagrams/images in the pages above:\n{desc_list}\n\n'
            'For EACH description (by index), return:\n'
            '- "page": the page number (integer) where it appears\n'
            '- "refined_description": a description that UNAMBIGUOUSLY identifies '
            'this specific diagram ON THAT PAGE. If there are multiple diagrams on '
            'the page, include position (e.g. "first/top diagram" or "second/bottom '
            'diagram") and unique visual details (specific values, labels, what is '
            'crossed out, etc). This will be used to crop the exact diagram.\n\n'
            'Return a JSON array with one object per description, in order:\n'
            '[{"index": 0, "page": N, "refined_description": "..."}, ...]\n\n'
            'If a description has no match, use {"index": N, "page": null, "refined_description": null}.'
        )

        response = client.models.generate_content(
            model=MODEL_PRO,
            contents=contents,
            config={"response_mime_type": "application/json"},
        )

        try:
            data = json.loads(response.text)
            if isinstance(data, dict):
                data = [data]

            # Build result indexed by position
            result_map = {}
            for item in data:
                idx = item.get("index", 0)
                page = item.get("page")
                refined = item.get("refined_description")
                result_map[idx] = (int(page) if page is not None else None,
                                   refined or descriptions[idx])

            return [result_map.get(i, (None, descriptions[i])) for i in range(len(descriptions))]

        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            return [(None, d) for d in descriptions]


def crop_from_page(hires_path: str, page: int, description: str, output: str) -> bool:
    """Crop a specific diagram from a high-res page image using Flash."""
    from google.genai import types
    from PIL import Image
    client = get_client()

    img = Image.open(hires_path)

    prompt = (
        f'Find the image/diagram matching this description: "{description}". '
        "Return the bounding box as box_2d: [ymin, xmin, ymax, xmax] normalized to 0-1000. "
        'If no match is found, return {"found": false}.'
    )

    response = client.models.generate_content(
        model=MODEL_PRO,
        contents=[img, prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "Failed to parse Gemini response"}))
        return False

    # Normalize nested lists/dicts from Gemini
    while isinstance(data, list):
        if len(data) == 0:
            print(json.dumps({"status": "not_found", "message": f"No match on page {page}"}))
            return False
        data = data[0]

    if not isinstance(data, dict):
        print(json.dumps({"status": "error", "message": f"Unexpected response type: {type(data).__name__}"}))
        return False

    if data.get("found") is False:
        print(json.dumps({"status": "not_found", "message": f"No match on page {page}"}))
        return False

    box = data.get("box_2d")
    if not box or len(box) != 4:
        print(json.dumps({"status": "error", "message": f"No valid bounding box: {data}"}))
        return False

    w, h = img.size
    y1 = int(box[0] / 1000 * h)
    x1 = int(box[1] / 1000 * w)
    y2 = int(box[2] / 1000 * h)
    x2 = int(box[3] / 1000 * w)

    pad_x = int(w * 0.02)
    pad_y = int(h * 0.02)
    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(w, x2 + pad_x)
    y2 = min(h, y2 + pad_y)

    cropped = img.crop((x1, y1, x2, y2))
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    cropped.save(output)
    print(json.dumps({"status": "ok", "method": "rasterize_crop", "path": output, "page": page, "box": box}))
    return True


def parse_page_range(s: str) -> tuple[int, int]:
    m = re.match(r'(\d+)-(\d+)', s)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"Invalid page range: {s}")


def run_batch(pdf_path: str, first_page: int, last_page: int, items: list[dict]):
    """Batch mode: one Pro call for all descriptions, then crop each."""
    descriptions = [it["description"] for it in items]
    outputs = [it["output"] for it in items]

    # One Pro call
    results = find_pages_batch(pdf_path, first_page, last_page, descriptions)

    # Group by page for efficient hi-res rasterization
    page_items = defaultdict(list)
    for i, (page, refined) in enumerate(results):
        if page is not None:
            page_items[page].append((i, refined, outputs[i]))
        else:
            print(json.dumps({"status": "not_found", "description": descriptions[i]}))

    # Rasterize each unique page once, crop all diagrams from it
    with tempfile.TemporaryDirectory() as tmpdir:
        for page, items_on_page in page_items.items():
            hires_path = rasterize_page_hires(pdf_path, page, tmpdir)
            if not hires_path:
                for _, _, output in items_on_page:
                    print(json.dumps({"status": "error", "message": f"Failed to rasterize page {page}"}))
                continue

            for idx, refined_desc, output in items_on_page:
                crop_from_page(hires_path, page, refined_desc, output)


def run_single(pdf_path: str, description: str, output: str,
               page: int | None, page_range: str | None):
    """Single extraction mode."""
    Path(output).parent.mkdir(parents=True, exist_ok=True)

    if try_embedded_extraction(pdf_path, page, description, output):
        return

    if page is not None:
        with tempfile.TemporaryDirectory() as tmpdir:
            hires_path = rasterize_page_hires(pdf_path, page, tmpdir)
            if hires_path:
                crop_from_page(hires_path, page, description, output)
            else:
                print(json.dumps({"status": "error", "message": f"Failed to rasterize page {page}"}))
                sys.exit(1)
        return

    if page_range:
        first_page, last_page = parse_page_range(page_range)
    else:
        result = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True)
        total = 20
        for line in result.stdout.splitlines():
            if line.startswith("Pages"):
                try:
                    total = int(line.split(":")[1].strip())
                except ValueError:
                    pass
        first_page, last_page = 1, total

    results = find_pages_batch(pdf_path, first_page, last_page, [description])
    found_page, refined_desc = results[0]

    if found_page is None:
        print(json.dumps({"status": "not_found", "message": f"No page found matching: {description}"}))
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        hires_path = rasterize_page_hires(pdf_path, found_page, tmpdir)
        if hires_path:
            if not crop_from_page(hires_path, found_page, refined_desc, output):
                sys.exit(1)
        else:
            print(json.dumps({"status": "error", "message": f"Failed to rasterize page {found_page}"}))
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Extract image(s) from PDF by description")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--description", help="Description of the image to extract (single mode)")
    parser.add_argument("--output", help="Output image path (single mode)")
    parser.add_argument("--page", type=int, default=None, help="Exact page number (skips page-finding)")
    parser.add_argument("--page-range", type=str, default=None, help="Page range to search, e.g. '5-10'")
    parser.add_argument("--batch", type=str, default=None,
                        help="Path to JSON manifest for batch extraction")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(json.dumps({"status": "error", "message": f"PDF not found: {args.pdf}"}))
        sys.exit(1)

    if args.batch:
        if not args.page_range:
            print(json.dumps({"status": "error", "message": "--page-range required for batch mode"}))
            sys.exit(1)
        with open(args.batch) as f:
            items = json.load(f)
        first_page, last_page = parse_page_range(args.page_range)
        run_batch(args.pdf, first_page, last_page, items)
    else:
        if not args.description or not args.output:
            print(json.dumps({"status": "error", "message": "--description and --output required for single mode"}))
            sys.exit(1)
        run_single(args.pdf, args.description, args.output, args.page, args.page_range)


if __name__ == "__main__":
    main()
