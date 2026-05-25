# Claude Code Config

A complete, opinionated Claude Code setup — agents, skills, hooks, rules, MCP servers, scripts, and an Obsidian-vault-as-second-brain workflow. Cloned from Jonah's personal config and sanitized for sharing.

> **Status:** working snapshot, not a polished product. Some agents reference tools or paths (graphify Python venv, `~/dev/claude-manager/` recon server) that you won't have. Anything you don't need, just delete — none of it is load-bearing for the core flow.

---

## What you get

| Layer | What it is | Where it goes |
|---|---|---|
| **`~/.claude/CLAUDE.md`** | Global behavioral directives + auto-trigger map | Loaded into every session |
| **`~/.claude/settings.json`** | Permissions, hooks, status line, enabled plugins, MCP servers | Read at startup |
| **`~/.claude/agents/`** | 35 custom agents (bookkeeper, memory-retrieval, latex-doc, stats-helper, etc.) | Spawned via the `Agent` tool |
| **`~/.claude/commands/`** | 12 user-defined slash commands (`/build`, `/test`, `/nc`, etc.) | Invoked as `/<name>` |
| **`~/.claude/skills/`** | 18 skills across 6 categories (corrections, research, mobile, orchestration, education, market-research) | Invoked via the `Skill` tool |
| **`~/.claude/hooks/`** | 6 Python hooks (destructive blocker, bash-as-read blocker, bookkeeper enforcer, compact watchdog, deploy verifier, trivial-subagent blocker) | Run automatically on tool calls |
| **`~/.claude/rules/`** | Auto-loaded coding standards (common + typescript) | Loaded into every session |
| **`~/.claude/docs/`** | Engineering principles, autonomous-build playbook, ecosystem survey | Referenced from CLAUDE.md |
| **`~/.claude/mcp/`** | Custom MCP server (personal-assistant) | Stdio MCP started by Claude Code |
| **`~/scripts/`** | Hook scripts referenced by `settings.json` (git_session_check, auto_push_after_commit, post-edit-format/typecheck/console-warn, pre-compact-save, etc.) | Run by hooks; some run on a schedule via launchd |
| **`~/notes/`** | Obsidian vault — the bookkeeper's storage, the second brain | Synced across machines via private git remote |

---

## Repo layout

```
claude-code-config/
├── README.md               # this file
├── SETUP.md                # install + customize guide
├── install.sh              # bootstrap script (sed-replaces __HOME__, copies into ~/.claude and ~/scripts)
├── home-CLAUDE.md          # template ~/CLAUDE.md (per-home-dir guide)
├── claude/                 # → installs to ~/.claude/
│   ├── CLAUDE.md           # global behavioral file (template — fill in "About Me")
│   ├── settings.json       # template — install.sh substitutes __HOME__ → $HOME
│   ├── settings.local.json # empty (machine-local overrides)
│   ├── INTERNAL_README.md  # the original ~/.claude/README.md — directory map
│   ├── agents/             # 35 .md files
│   ├── commands/           # 12 .md files
│   ├── skills/             # 6 category dirs, 18 skills
│   ├── hooks/              # 6 .py files
│   ├── rules/              # common/ (9) + typescript/ (3)
│   ├── docs/               # 4 reference docs
│   ├── mcp/                # personal_assistant_mcp.py
│   ├── output-styles/      # ios-mentor.md
│   └── setup/              # original new-machine-setup notes
├── scripts/                # → installs to ~/scripts/
│   ├── bash_command_validator.py
│   ├── git_session_check.sh
│   ├── auto_push_after_commit.sh
│   ├── machine-state.sh
│   ├── obsidian-sync.sh
│   └── hooks/
│       ├── post-edit-{format,typecheck,console-warn}.sh
│       ├── pre-compact-{save,bookkeeper}.sh
│       ├── pre-search-memory-redirect.sh
│       └── stop-{bookkeeper-on-done,console-log-check}.sh
└── notes-template/         # → seeds ~/notes/ if it doesn't exist
    ├── CLAUDE.md           # vault-level instructions
    ├── _atlas.md           # entry-point template
    ├── .gitignore
    └── templates/
        ├── daily-note.md
        ├── learning-note.md
        └── project-decision.md
```

---

## The core idea

This config is built around **three interlocking systems**:

### 1. Behavioral guardrails (CLAUDE.md + rules + hooks)

A short list of behavioral rules in `~/.claude/CLAUDE.md` ("Verify Before Claiming", "Walking Skeleton First", "Don't Re-Read Files in the Same Session"). Auto-loaded coding standards in `~/.claude/rules/common/` and `~/.claude/rules/typescript/`. **Hooks** in `~/.claude/hooks/` enforce the rules that need teeth — e.g. `bash_as_read_blocker.py` actually rejects `cat` on a file that should be `Read`, `destructive_blocker.py` requires confirmation for `rm -rf`, `bookkeeper_enforcer.py` ensures the bookkeeper runs at session end.

### 2. Second brain (Obsidian vault + bookkeeper + memory-retrieval)

`~/notes/` is an Obsidian vault organized into `daily/`, `projects/<name>/`, `learning/`, `reference/`, `personal/`, `deadlines/`, `ideas/`, `templates/`.

- **`bookkeeper` agent** runs at the end of every session. It writes to today's `daily/YYYY-MM-DD.md`, updates project changelogs and decisions, creates wikilinks between notes, and commits + pushes the vault to a private git remote. There's a `Stop` hook (`bookkeeper_enforcer.py`) that blocks session-end if the bookkeeper didn't run.
- **`memory-retrieval` agent** runs at the start of dev work. It greps the vault for relevant context, follows wikilinks, and returns past decisions / known bugs / project state so Claude doesn't restart cold.
- The vault is its own git repo, separate from this config. It syncs across machines via a private GitHub repo.

Two persistence systems live side by side:
- **Claude Code memory** (`~/.claude/projects/*/memory/`) holds *behavioral* preferences ("when this user says X, do Y").
- **Obsidian vault** holds *knowledge* (project state, decisions, learning notes).

Never duplicate between them.

### 3. Slash skills (corrections + orchestration + research)

Skills are slash-commands the user types directly (`/vent`, `/jarvis`, `/manager`, `/consult`, `/log-session`, `/graphify`, `/human-writing`, `/therapy`, etc.) that load specialized prompts and tools. They cover:

- **corrections/** — `/vent` logs a gripe, `/therapy` reviews the gripe log and proposes structural fixes (new hooks, rules, or agent edits), `/human-writing` rewrites AI-ish prose in the user's voice, `/second-opinion` pings GPT/Gemini/Grok.
- **orchestration/** — `/jarvis` orients you cold ("what was I doing?"), `/log-session` snapshots the session, `/manager` lists/messages/kills other running Claude sessions via a local recon server, `/consult` asks another running session a question.
- **research/** — `/graphify` builds a knowledge graph from any corpus, `/youtube-parse` and `/youtube-dl` for YouTube content.
- **education/** — `/study-guide`, `/condense-notes`, `/extract-image`.
- **mobile/** — iOS testing, SwiftUI components, code analyzer.
- **market-research/** — autonomous multi-agent market research pipeline.

---

## Quick install

```bash
git clone <this-repo> ~/dev/claude/claude-code-config
cd ~/dev/claude/claude-code-config
./install.sh
```

Then read `SETUP.md` for what to customize, what's optional, and how to remove the parts you don't want.
