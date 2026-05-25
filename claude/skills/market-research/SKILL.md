---
name: market-research
description: Autonomous multi-agent market research pipeline. Scrapes Reddit, Hacker News, and forum URLs for a configured niche, fans out to ~20-30 parallel agents across 6 stages (collect → chunked sentiment → 4 synthesis specialists → adversarial critique → report/recommendations/competitive), produces structured outputs to ~/dev/voh/voh-market-research/niches/<slug>/runs/<timestamp>/. Trigger when the user wants to research a market niche, gauge sentiment in a community, find pain points/desires from public discussions, or generate product recommendations from organic feedback.
---

# /market-research — Autonomous Market Research Pipeline

The full pipeline lives at `~/dev/voh/voh-market-research/`. This skill is the entry point; the stage runbooks in `pipeline/stages/` are the source of truth for behavior at each step.

## Invocation

Two forms:

- `/market-research` — start fresh, wizard creates a new niche config
- `/market-research <niche-slug>` — load existing `niches/<slug>/config.yaml`, offer to edit, then run

## Repo location

```
REPO=~/dev/voh/voh-market-research
```

Always `cd $REPO` before running anything. The Python collectors expect to be invoked from the repo root with the venv activated:

```bash
cd ~/dev/voh/voh-market-research && source .venv/bin/activate && python -m pipeline.collectors.reddit ...
```

If `.venv` doesn't exist yet, create it and install deps:

```bash
cd ~/dev/voh/voh-market-research
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
```

## Run flow (read this once, then follow each stage runbook in order)

1. **Stage 1 — Wizard** → `pipeline/stages/01-wizard.md`
   Build or load `niches/<slug>/config.yaml`. Create `runs/<UTC-timestamp>/{raw,analysis}`. Seed `run-meta.json`.

2. **Stage 2 — Collect** → `pipeline/stages/02-collect.md`
   Run reddit/hackernews/forum collectors in **parallel Bash calls**. Outputs to `runs/<ts>/raw/`.

3. **Stage 3 — Analyze** → `pipeline/stages/03-analyze.md`
   Chunk items (~30 per chunk for `deep` depth). Fan out **one Agent per chunk in parallel** (Haiku 4.5 by default). Each writes `analysis/chunk-NN-sentiment.md`.

4. **Stage 4 — Synthesize** → `pipeline/stages/04-synthesize.md`
   **4 parallel Sonnet agents** — themes, personas, competitors, trends. Each reads all chunk files; each writes one analysis file.

5. **Stage 5 — Critique** → `pipeline/stages/05-critique.md`
   **1 Sonnet adversarial agent** reads the 4 synthesis files + chunk files; writes `analysis/critique.md`.

6. **Stage 6 — Final** → `pipeline/stages/06-recommend.md`
   **3 parallel Sonnet agents** — REPORT.md, RECOMMENDATIONS.md, COMPETITIVE.md. Each downgrades or removes claims the critic flagged as weak. Finalize `run-meta.json`.

## Hard rules

- **Parallel always means a single message with multiple Agent tool calls.** Sequential execution defeats the architecture.
- **Read the stage runbook before executing the stage.** Don't infer behavior from the filename.
- **Never overwrite a prior run.** Each invocation creates a fresh timestamped folder.
- **Always update `run-meta.json` as you go**, not at the end. If a stage fails you still want the partial trace.
- **Cost tracking is mandatory.** Log agent counts and rough token estimates per stage.

## Default models

| Stage | Model | Reason |
|---|---|---|
| Wizard | (no agent — main loop) | Just AskUserQuestion |
| Collect | (no agent — Bash) | Just Python scripts |
| Analyze | Haiku 4.5 | Many chunks, classification is easy |
| Synthesize | Sonnet 4.6 | Clustering + summarization benefits from better model |
| Critique | Sonnet 4.6 | Adversarial reasoning |
| Final | Sonnet 4.6 | Writing quality matters |

Upgrade analyze to Sonnet if depth is `extreme`. Upgrade critique to Opus 4.7 if depth is `extreme`.

## What "done" looks like

A run is complete when:

1. `niches/<slug>/runs/<ts>/REPORT.md` exists and is non-empty
2. `RECOMMENDATIONS.md` exists and is non-empty
3. `COMPETITIVE.md` exists and is non-empty
4. `run-meta.json.totals.completed_at` is set
5. You've told the user the path and surfaced critic confidence ratings

## On failure

If any stage fails partially (e.g., 1 of 10 chunk agents errored), continue with what you have and note the failure in `run-meta.json`. Only abort entirely if no items were collected or all synthesis specialists fail.
