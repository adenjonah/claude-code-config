# Home Directory Guide

This is `~/CLAUDE.md` — a per-project CLAUDE.md that lives at the root of your home directory. Claude Code loads it when the current working directory is `~` or one of its descendants that doesn't have its own CLAUDE.md.

## About Me

- **Experience**: <fill in>
- **Collaboration style**: <fill in>
- **Tech stacks**: <fill in>
- **Coding preferences**: <fill in>

## Directory Layout

- `~/dev/` — All code projects (git repos). Group into category subdirs (`personal/`, `clients/`, `school/`, etc.).
- `~/notes/` — Obsidian vault. Knowledge base, project notes, daily logs.
- `~/scripts/` — Standalone scripts and automation (referenced by Claude Code hooks).
- `~/.claude/agents/` — Custom agents for specialized tasks.
- Standard macOS dirs (Desktop, Documents, Downloads) are unused for work.

## Quick Navigation

| Need to… | Go to… |
|---|---|
| Work on a project | `~/dev/<category>/<project-name>` |
| Find project notes/decisions | `~/notes/projects/<project-name>` |
| Find a learning reference | `~/notes/reference/` |
| Run setup/utility scripts | `~/scripts/` |
| Check Claude agent definitions | `~/.claude/agents/` |

## Key Files

- `~/dev/CLAUDE.md` — Per-category dev rules (create this yourself)
- `~/notes/CLAUDE.md` — Knowledge base guide
- `~/.zshrc` — Shell config (PATH, env vars)
- `~/.gitconfig` — Git identity and credential config

## Environment

- macOS on Apple Silicon (arm64) <adjust>
- Homebrew at /opt/homebrew
- Node.js available via Homebrew
- Claude Code via Homebrew (`brew upgrade claude-code` to update)
- gh CLI for GitHub operations

## Permissions Hygiene

`~/.claude/settings.json` has the permanent, general-purpose permissions. `~/.claude/settings.local.json` accumulates session-specific permissions over time. To prevent bloat:

- **Before approving a permission**, check if `settings.json` already covers it with a broader pattern (e.g., `Bash(git:*)` covers `git status`, `git log`, etc.)
- **Don't approve one-off commands** — if it's a one-time thing, just run it; if it's recurring, add a clean pattern to `settings.json` instead
- If `settings.local.json` grows past ~30 lines, consolidate useful patterns into `settings.json` and reset `settings.local.json`

## Memory Ownership

Two persistence systems exist — each has a clear role:

- **Claude Code memory** (`~/.claude/projects/*/memory/`) = behavioral preferences, feedback corrections, how Claude should work with you
- **Obsidian vault** (`~/notes/`) = knowledge, history, decisions, project state, reference material

Do NOT duplicate facts across both systems. Setup details, agent lists, and vault structure are derivable from config files — don't store them in Claude Code memory.

## CRITICAL: Bookkeeper (Auto-Triggered — MANDATORY)

The Obsidian vault (`~/notes/`) is your **second brain**. The bookkeeper keeps it updated so any future Claude session can understand what's been done, why, and how everything connects.

**Claude's LAST action before ending ANY session MUST be invoking the bookkeeper agent with a full summary. This is non-negotiable — do it even if the session was short. The only exception is quick one-off questions that don't produce content worth remembering.**

### Always log:
- **Dev work** — features built, bugs fixed, refactors, config changes, files involved
- **Decisions** — architecture choices, library picks, trade-offs, and reasoning
- **How things connect** — file relationships, data flow, navigation, dependencies
- **Notes & writing** — anything to write down, remember, or think about
- **Deadlines** — due dates, commitments, timelines mentioned
- **Ideas** — feature ideas, project ideas, things to explore
- **Journal / reflections** — personal entries, session reflections
- **Learning** — concepts studied, course material, technical notes

### How to log:
- At the **end of every session**, call the bookkeeper with a summary of everything that happened
- For **major mid-session milestones**, log immediately
- Pass **rich context**: what happened, why, what's involved, how it relates to other things
- The bookkeeper handles file placement, formatting, linking, and tagging

## CRITICAL: Memory Retrieval (Before Dev Work)

**BEFORE starting dev work in any project, invoke the memory-retrieval agent** to load vault context for the project. This ensures Claude has past decisions, known issues, and project state before writing code.

## Agent Auto-Triggers

Same as `~/.claude/CLAUDE.md`. See that file for the full list.
