# Setup & Customization Guide

Step-by-step install + what to tweak + what each piece does. Read `README.md` first for the bird's-eye view.

---

## 0. Prerequisites

- macOS with Homebrew at `/opt/homebrew`. Linux works for most of it; you'll need to tweak the `osascript`/`pbcopy` permissions and the launchd plist if you want Obsidian auto-sync.
- `python3` on PATH (used by hooks and the MCP server).
- `gh` CLI authenticated (`gh auth login`) — the bookkeeper pushes to GitHub.
- A private GitHub repo for your Obsidian vault if you want multi-machine sync. Empty repo is fine.
- Claude Code installed (`brew install --cask claude-code`).

---

## 1. Run the installer

```bash
git clone <this-repo> ~/dev/claude/claude-code-config
cd ~/dev/claude/claude-code-config
./install.sh
```

What `install.sh` does:

1. Substitutes the `__HOME__` placeholder in `claude/settings.json` with your `$HOME`, writes to `~/.claude/settings.json`. Backs up any existing one.
2. Copies `claude/{agents,commands,skills,hooks,rules,docs,mcp,output-styles,setup}` into `~/.claude/`. Asks before overwriting if those dirs exist.
3. Copies `scripts/*` into `~/scripts/` and `scripts/hooks/*` into `~/scripts/hooks/`, making them executable.
4. If `~/notes/` doesn't exist, offers to seed it with the vault template.
5. If you keep `home-CLAUDE.md`, optionally installs it to `~/CLAUDE.md`.

Flags: `--dry-run` (print actions), `--force` (overwrite without asking).

---

## 2. Mandatory customizations

After install, **do these before starting a Claude Code session.**

### 2a. Fill in your profile in `~/.claude/CLAUDE.md`

Open `~/.claude/CLAUDE.md` and edit the **About Me** section at the top. Claude uses this to calibrate explanation depth, suggested approaches, and how much hand-holding to do. Fields:

- Experience level
- Collaboration style (collaborative vs. autonomous; ask vs. proceed)
- Tech stacks
- Coding preferences

There's also a **Project Context** section at the bottom — empty by default. As your dev projects grow, add per-project rules here (which repo owns what, which docs are sources of truth, cross-cutting conventions).

### 2b. Decide what to do with the personal-assistant MCP

`~/.claude/settings.json` has a `mcpServers.personal-assistant` block that points to a personal Heroku-hosted FastAPI assistant (tasks/events/inbox/semantic search). It's wired up via `~/.claude/mcp/personal_assistant_mcp.py`.

You have two options:

- **Delete it** — open `settings.json`, remove the `mcpServers` block entirely (or just the `personal-assistant` subkey). Done.
- **Keep it, point it at your own** — replace `PA_API_URL` with your own backend and `PA_API_TOKEN` with your own service token. The MCP server source is in `~/.claude/mcp/personal_assistant_mcp.py`; the expected API contract is `GET /api/v1/tasks`, `GET /api/v1/events`, `GET /api/v1/inbox`, `POST /api/v1/search`. Bearer auth.

### 2c. Initialize the Obsidian vault as a git repo

If you let the installer seed `~/notes/`, point it at a private GitHub repo:

```bash
cd ~/notes
git init
git add -A
git commit -m "initial vault"
gh repo create notes --private --source=. --remote=origin --push
```

Multi-machine sync works because:
- `git_session_check.sh` (a `SessionStart` hook) fetches and pulls the vault at session start
- The bookkeeper commits and pushes the vault at session end
- `obsidian-sync.sh` (run by a launchd job every 10 min) auto-commits and pushes inbetween

### 2d. (Optional) Set up the launchd job for Obsidian auto-sync

Create `~/Library/LaunchAgents/com.<your-user>.obsidian-sync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.<your-user>.obsidian-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/<your-user>/scripts/obsidian-sync.sh</string>
    </array>
    <key>StartInterval</key><integer>600</integer>
    <key>RunAtLoad</key><true/>
    <key>StandardOutPath</key><string>/tmp/obsidian-sync.log</string>
    <key>StandardErrorPath</key><string>/tmp/obsidian-sync.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

Load: `launchctl load ~/Library/LaunchAgents/com.<your-user>.obsidian-sync.plist`

### 2e. Restart Claude Code

Quit and relaunch (or `/reload-config`). On session start you should see `VAULT_SYNC: ...` if your vault is a git repo, or nothing if it's not. That confirms hooks are wired correctly.

---

## 3. Optional pieces — what to delete if you don't want it

Everything here is independently disable-able. Cut what you don't use.

| Feature | What it does | To disable |
|---|---|---|
| **personal-assistant MCP** | Hits your own task/inbox/calendar API | Delete `mcpServers.personal-assistant` from `settings.json` and `~/.claude/mcp/personal_assistant_mcp.py` |
| **/graphify** | Builds a NetworkX knowledge graph from any corpus, used by bookkeeper + memory-retrieval | Delete `~/.claude/skills/research/graphify/`. Then edit `bookkeeper.md` and `memory-retrieval.md` agent files to remove the "Graphify Integration" sections. |
| **/manager + /consult** | Cross-session orchestration via a local Rust "recon" server | Delete `~/.claude/skills/orchestration/{manager,consult}/`. These reference `~/dev/claude-manager/server/target/release/recon` which isn't included here. |
| **deploy_verifier.py hook** | Verifies deploys (Heroku, Vercel, Fly) actually succeeded | Remove from `settings.json` `PostToolUse.Bash` hooks |
| **bookkeeper_enforcer.py hook** | Blocks session-end if bookkeeper didn't run | Remove from `settings.json` `Stop` hooks. **You probably want this — it's the load-bearing piece that makes the second-brain work.** |
| **bash_as_read_blocker.py hook** | Blocks `cat`/`head`/`tail` when Claude should use the `Read` tool | Remove from `settings.json` `PreToolUse.Bash` hooks |
| **trivial_subagent_blocker.py hook** | Stops Claude from spawning agents for tiny tasks | Remove from `settings.json` `PreToolUse.Agent\|Task` hooks |
| **post-edit-{format,typecheck,console-warn}.sh** | Runs prettier/eslint/tsc/grep after every Edit/Write | Remove from `settings.json` `PostToolUse.Edit\|Write` hooks |
| **Vercel plugin** | Adds Vercel deploy/preview tools | Set `"vercel@claude-plugins-official": false` in `enabledPlugins` |
| **Linear plugin** | Linear issue tools (already disabled by default) | — |

---

## 4. The hook architecture (what runs when)

Everything wired up in `settings.json`:

| Event | Hook | What it does |
|---|---|---|
| `SessionStart` (startup, resume) | `git_session_check.sh` | Pull vault from remote; push any local changes; warn on divergence; also report status of the current project repo |
| `PreToolUse` Bash | `bash_command_validator.py` | Warn on non-ideal patterns (grep → rg, find → fd) |
| `PreToolUse` Bash | `destructive_blocker.py` | Hard-block dangerous patterns; require user OK for `rm -rf` |
| `PreToolUse` Bash | `bash_as_read_blocker.py` | Reject `cat`/`head`/`tail` on a file Claude should `Read` |
| `PreToolUse` Agent\|Task | `trivial_subagent_blocker.py` | Block tiny tasks from spawning sub-agents (cost control) |
| `PreToolUse` * | `compact_watchdog.py` | Detect long sessions, suggest a manual compact at logical phase boundaries |
| `PreToolUse` Grep\|Glob | `pre-search-memory-redirect.sh` | Redirect searches into the right scope when they'd hit too much |
| `PostToolUse` Bash | `auto_push_after_commit.sh` | Auto-`git push` after any committed change (multi-machine sync) |
| `PostToolUse` Bash | `deploy_verifier.py` | After a deploy command, verify it actually shipped |
| `PostToolUse` Edit\|Write | `post-edit-format.sh` | Run prettier/black/swiftformat |
| `PostToolUse` Edit\|Write | `post-edit-typecheck.sh` | Run tsc/mypy/swiftc check |
| `PostToolUse` Edit\|Write | `post-edit-console-warn.sh` | Warn if `console.log`/`print()` debug lines were left in |
| `PreCompact` * | `pre-compact-save.sh` | Save session state before context compaction |
| `PreCompact` * | `pre-compact-bookkeeper.sh` | Run a mini-bookkeeper before compaction |
| `Stop` * | `stop-console-log-check.sh` | Final sweep for stray debug logs |
| `Stop` * | `bookkeeper_enforcer.py` | Block stop unless bookkeeper ran (this is the load-bearing piece) |

---

## 5. The bookkeeper / memory-retrieval loop (the most important pattern)

This is the system worth understanding deeply. Everything else is decoration.

```
┌─ session start ────────────────────────────────────────────────────────┐
│                                                                        │
│  SessionStart hook → git_session_check.sh                              │
│    → fetches & pulls ~/notes/ from remote (multi-machine sync)         │
│                                                                        │
│  user: "let's keep working on bettr-app"                               │
│                                                                        │
│  Claude (per CLAUDE.md auto-trigger) → spawns memory-retrieval agent  │
│    → reads ~/notes/_atlas.md (vault entry point)                       │
│    → greps for project-relevant notes                                  │
│    → follows wikilinks 2-3 hops                                        │
│    → returns: past decisions, known bugs, structure, deadlines         │
│                                                                        │
│  Claude now has context from past sessions, not starting cold          │
│                                                                        │
├─ during session ──────────────────────────────────────────────────────┤
│                                                                        │
│  ... work happens ...                                                  │
│                                                                        │
├─ session end ─────────────────────────────────────────────────────────┤
│                                                                        │
│  Claude (per CLAUDE.md auto-trigger) → spawns bookkeeper agent         │
│    → appends to daily/YYYY-MM-DD.md (the hub)                         │
│    → updates projects/<name>/changelog.md                              │
│    → writes new projects/<name>/decisions/<name>.md if applicable      │
│    → adds wikilinks both ways                                          │
│    → commits & pushes ~/notes/ to remote                               │
│                                                                        │
│  Stop hook → bookkeeper_enforcer.py                                    │
│    → if bookkeeper didn't run, BLOCKS the stop and forces a re-call    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Why this matters:** without the bookkeeper, every session starts from zero. With it, the vault grows into a real knowledge base, and any future session — on any machine — can recover full context in one `memory-retrieval` call.

---

## 6. Customizing the agents and skills

All agents are markdown files in `~/.claude/agents/<name>.md` with YAML frontmatter:

```yaml
---
name: bookkeeper
description: <one-liner — used to decide when to invoke>
tools: Read, Write, Edit, Glob, Grep, Bash
model: sonnet  # or haiku, opus
---

<system prompt body>
```

Skills are in `~/.claude/skills/<category>/<name>/SKILL.md` with similar frontmatter. They're invoked as `/<name>` slash commands.

**To add a new agent**, drop a `.md` file in `~/.claude/agents/`. No subdirs — Claude Code requires the flat layout.

**To add a new skill**, create `~/.claude/skills/<category>/<name>/SKILL.md`. Then add a trigger rule to `~/.claude/CLAUDE.md` under "Mandatory Auto-Triggers" if it should fire automatically.

**To change the model** an agent uses, edit the `model:` line in its frontmatter. Recommended:
- `haiku` for utility agents called frequently (bookkeeper, memory-retrieval)
- `sonnet` for main dev work
- `opus` for architecture, research, LaTeX, deep analysis

---

## 7. Multi-machine sync

This config supports running across two or more macs with shared state.

**Three things sync via git:**

1. **The Obsidian vault** (`~/notes/`) — pushed by bookkeeper at session end + by the launchd job every 10 min; pulled by `git_session_check.sh` at session start.
2. **The config repo itself** (this repo) — when you change an agent, hook, or rule on machine A, commit + push, then `git pull && ./install.sh --force` on machine B.
3. **Project repos** (`~/dev/*/*`) — `auto_push_after_commit.sh` pushes after every commit, so the other machine just pulls.

**One thing does NOT sync (machine-local):**

- `~/.claude/settings.local.json` — accumulated session permissions
- `~/.claude/projects/` — per-machine context memory
- `~/.claude/sessions/`, `~/.claude/history.jsonl` — session logs

---

## 8. Troubleshooting

**Hooks aren't firing.** Check `~/.claude/settings.json` for stale `__HOME__` placeholders (re-run `install.sh`). Check scripts are executable (`chmod +x ~/scripts/*.sh ~/scripts/hooks/*.sh ~/.claude/hooks/*.py`).

**Bookkeeper is failing.** Most common cause: `~/notes/` isn't a git repo, or the remote isn't set. Run `cd ~/notes && git status` to check. The bookkeeper still writes notes locally even if the push fails — check `~/notes/daily/` for today's file.

**Memory-retrieval returns nothing.** Vault is probably empty or `_atlas.md` is empty. That's fine — it grows over time as the bookkeeper writes more.

**"permission denied" for some Bash command.** It's not in `settings.json` allow list. Add a clean glob pattern (e.g. `Bash(mytool:*)`), don't approve one-offs that bloat `settings.local.json`.

**MCP server fails to start.** Check `/opt/homebrew/bin/python3` exists. If not, edit the `command:` field in `settings.json.mcpServers.personal-assistant` to your Python path.

**Plugins won't install.** They auto-install from `enabledPlugins` on first launch. If `everything-claude-code` fails, install manually:
```bash
claude plugin marketplace add everything-claude-code --source git --url https://github.com/affaan-m/everything-claude-code.git
claude plugin install everything-claude-code
```

---

## 9. What's NOT in this repo (intentionally)

- **The Obsidian vault contents** (your daily notes, project notes, etc.) — only the empty template structure ships
- **Per-machine permission accumulations** (`settings.local.json` is shipped empty)
- **Session history** (`history.jsonl`, `sessions/`, `tasks/`, `plans/`, `debug/`)
- **Plugin caches** (`plugins/cache/` is rebuilt from `enabledPlugins`)
- **The `claude-manager` recon server** referenced by `/manager` and `/consult` — that's a separate Rust project at `~/dev/claude-manager/`
- **The graphify Python venv** referenced by the bookkeeper/memory-retrieval graph integration — install separately if you want graph features
- **Personal data**: API tokens, email address, project-specific identifiers are stripped or templated

---

## 10. License / sharing

This is personal config. Use it, fork it, strip what you don't need. The agents, skills, hooks, and rules are MIT'd by way of being personal preferences with no copyright claim that matters. Plugins (`everything-claude-code`, `vercel-plugin`, etc.) have their own licenses — check those repos.
