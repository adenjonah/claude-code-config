---
name: condense-notes
description: Condense lecture notes, slides, or PDFs into concise documentation-style reference guides. Strips pedagogical fluff, preserves every technical fact. Output goes to ~/notes/. Use when the user wants to compress course materials into a study reference.
user-invocable: true
argument-hint: "<source file(s)> [output path]"
---

# Condense Notes

Transforms lecture notes, PDFs, or slides into tight, reference-style documentation. Man-page tone, not classroom presentation — same information, fewer words, but never at the cost of clarity.

## Directive

- Strip pedagogical scaffolding: remove "let's look at...", "as you can see...", motivation intros, repeated explanations
- Keep every technical fact, rule, definition, formula, code example, and edge case
- Keep concise but **clear** explanations of *why* things work — someone reading this without the lecture should still understand
- Use examples to illustrate, not just bare facts
- Format as reference: concise headers, bullet points, tables, annotated code blocks
- Preserve all gotchas — prime exam material
- Never sacrifice clarity for brevity

## Reading PDFs

Use `Read(pages: "N-M")` to read PDFs in chunks. The pages parameter is the only reliable page number source — don't trust page numbers in the PDF content itself.

## Diagrams

When source materials contain diagrams or figures worth preserving, use the `extract-image` skill:

```bash
python3 ~/.claude/skills/education/extract-image/extract_image.py \
  --pdf <SOURCE.pdf> \
  --page-range <N-M> \
  --description "<what the diagram shows>" \
  --output ~/notes/images/<output-name>.png
```

The `--page-range` must exactly match the `pages: "N-M"` from your `Read()` call.

Embed extracted images in the output with `![[filename.png]]`.

## Output

- Markdown file, Obsidian-compatible (`~/notes/` by default)
- If condensing course materials, save under `~/notes/courses/<course-name>/`
- Images go in `~/notes/images/` or a sibling `images/` directory
- Use `[[wikilinks]]` to link related notes if they exist in the vault

## Quality bar

Before finishing:
- [ ] Every technical term is defined precisely
- [ ] All formulas, rules, and edge cases are preserved
- [ ] Diagrams extracted for any figure that aids understanding
- [ ] Output reads as a reference, not a summary
- [ ] No filler phrases ("it is important to note", "let us consider")
