# New Machine Setup Guide

Instructions for setting up a second machine to mirror this Claude Code environment. Run Claude Code on the new machine and point it at this file.

**Last verified**: 2026-04-01 (27 agents, 11 rules, 3 contexts, 11 plugins)

## Prerequisites

- macOS on Apple Silicon
- Homebrew installed (`/opt/homebrew`)
- GitHub authenticated (`gh auth login`)
- SSH key generated (`~/.ssh/id_ed25519`)

## 1. Install Tools

```bash
brew install node cocoapods gh
brew install --cask claude-code
```

## 2. Clone Repos

```bash
mkdir -p ~/dev ~/scripts
cd ~/dev
gh repo clone <your-org>/<your-repo>
# (additional repo)
# (additional repo)
gh repo clone <your-org>/notes ~/notes
# Clone any other active repos listed in ~/dev/CLAUDE.md
```

## 3. Copy Config from Primary Machine

**Important**: The source of truth is the desktop's `~/.claude/` directory, NOT the archived `_archive/Claude-Code/` repo.

### Path assumption

`settings.json` hardcodes `$HOME` in hook paths and permissions. If the macOS username on the new machine differs, run after copying:
```bash
sed -i '' "s|$HOME|$HOME|g" ~/.claude/settings.json
```

### Directories to sync (copy entire directory)

| Source (primary machine) | Destination (new machine) | Contents |
|---|---|---|
| `~/.claude/agents/` | `~/.claude/agents/` | 27 agent definitions (see full list below) |
| `~/.claude/rules/` | `~/.claude/rules/` | common/ (8 files) + typescript/ (3 files) |
| `~/.claude/contexts/` | `~/.claude/contexts/` | dev.md, research.md, review.md |
| `~/.claude/commands/` | `~/.claude/commands/` | nc.md (New Claude iTerm2 command) |
| `~/.claude/setup/` | `~/.claude/setup/` | This guide + sync checklist |
| `~/scripts/` | `~/scripts/` | Hook scripts + utilities (including hooks/ subdir) |

### Individual files to sync

| Source | Destination |
|---|---|
| `~/.claude/settings.json` | `~/.claude/settings.json` |
| `~/CLAUDE.md` | `~/CLAUDE.md` |
| `~/dev/CLAUDE.md` | `~/dev/CLAUDE.md` |

### Do NOT sync (machine-specific)

- `~/.claude/settings.local.json` — accumulated session permissions, machine-specific
- `~/.claude/projects/` — project memory built contextually per machine
- `~/.claude/plans/`, `tasks/`, `todos/` — session ephemera
- `~/.claude/history.jsonl`, `debug/`, `sessions/` — session data
- `~/.claude/plugins/cache/` — rebuilt automatically from `enabledPlugins` in settings.json
- `~/.gitconfig` signing key path — uses machine-specific SSH key

### Make scripts executable

```bash
chmod +x ~/scripts/*.sh ~/scripts/*.py
chmod +x ~/scripts/hooks/*.sh
```

## 4. Shell Config

Add to `~/.zshrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/scripts:$PATH"
export DEV="$HOME/dev"
export NOTES="$HOME/notes"
[ -f ~/.secrets ] && source ~/.secrets
```

## 5. Git Config

Set in `~/.gitconfig`:
- user.name = <Your Name>
- user.email = <your-username>@users.noreply.github.com
- credential helper = `gh auth git-credential` (for github.com and gist.github.com)

### SSH Commit Signing

Using the new machine's SSH key (NOT copied from primary machine):
```bash
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global gpg.format ssh
git config --global commit.gpgsign true
git config --global tag.gpgsign true
git config --global gpg.ssh.allowedSignersFile ~/.ssh/allowed_signers
```

Create `~/.ssh/allowed_signers`:
```
<your-username>@users.noreply.github.com <paste contents of ~/.ssh/id_ed25519.pub>
```

Upload the signing key to GitHub:
```bash
gh api user/ssh_signing_keys -f title="machine2-signing" -f key="$(cat ~/.ssh/id_ed25519.pub)"
```

If that 404s, first run:
```bash
gh auth refresh -h github.com -s admin:ssh_signing_key
```

## 6. Plugins

Plugins auto-install from the `enabledPlugins` key in `settings.json` on first launch. If any are missing, install manually:

**Official plugins** (should auto-install):
- commit-commands, security-guidance, code-review, feature-dev, frontend-design
- pr-review-toolkit, hookify
- typescript-lsp, pyright-lsp, swift-lsp

**Custom marketplace** (may need manual setup):
```bash
claude plugin marketplace add everything-claude-code --source git --url https://github.com/affaan-m/everything-claude-code.git
claude plugin install everything-claude-code
```

## 7. Obsidian Vault Sync

The vault repo is already cloned at `~/notes/`. Set up the auto-sync launchd job:

Create `~/Library/LaunchAgents/com.jonah.obsidian-sync.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jonah.obsidian-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/scripts/obsidian-sync.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/obsidian-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/obsidian-sync.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.jonah.obsidian-sync.plist
```

## 8. Project-Specific Setup (bettr-app)

```bash
cd ~/dev/bettr-app/Bettr && npm install
cd ~/dev/bettr-app/functions && npm install
cd ~/dev/bettr-app/Bettr/ios && pod install
```

## 9. Verify

- `cd ~/dev/bettr-app/Bettr && npm run typecheck` — should pass
- `git commit --allow-empty -m "test: verify signing"` — should create a signed commit
- `cat /tmp/obsidian-sync.log` — should show sync activity
- Open Obsidian -> Open folder as vault -> select `~/notes/`
- Start a Claude Code session — the SessionStart hook should run `git_session_check.sh`

---

## Quick Diff (compare machines)

Run these on the laptop to see what's different from the desktop:

```bash
# Compare settings
diff <(ssh desktop "cat ~/.claude/settings.json") ~/.claude/settings.json

# Compare agent list
diff <(ssh desktop "ls ~/.claude/agents/") <(ls ~/.claude/agents/)

# Compare rules
diff <(ssh desktop "find ~/.claude/rules -name '*.md' | sort") <(find ~/.claude/rules -name '*.md' | sort)

# Compare scripts
diff <(ssh desktop "find ~/scripts -type f | sort") <(find ~/scripts -type f | sort)
```

Or if machines aren't on the same network, compare against this inventory (see below).

---

## Full Inventory (as of 2026-04-01)

### Agents (27 files in `~/.claude/agents/`)

```
architect.md           homework-solver.md     question-refinement.md
bookkeeper.md          industry-standards.md  quote-finder.md
build-error-resolver.md ios-engineer.md       refactor-cleaner.md
codebase-research.md   latex-doc.md           security-reviewer.md
database-architect.md  memory-retrieval.md    source-researcher.md
deep-audit.md          plan-reviewer.md       stats-helper.md
deep-debug.md                                 study-guide.md
doc-updater.md                                tdd-guide.md
essay-planner.md                              test-writer.md
firebase-developer.md                         ui-dev-react-native.md
                                              ui-dev-web.md
```

### Rules (11 files in `~/.claude/rules/`)

**common/** (8):
agents.md, coding-style.md, development-workflow.md, git-workflow.md, hooks.md, performance.md, security.md, testing.md

**typescript/** (3):
coding-style.md, patterns.md, security.md

### Contexts (3 files in `~/.claude/contexts/`)

dev.md, research.md, review.md

### Commands (1 file in `~/.claude/commands/`)

nc.md

### Scripts (11 files in `~/scripts/`)

**Root** (5): auto_push_after_commit.sh, bash_command_validator.py, git_session_check.sh, obsidian-sync.sh, setup_remote.sh

**hooks/** (5): post-edit-console-warn.sh, post-edit-format.sh, post-edit-typecheck.sh, pre-compact-save.sh, stop-console-log-check.sh

### Hooks (configured in settings.json)

| Hook | Trigger | Script |
|---|---|---|
| SessionStart (startup) | startup | `git_session_check.sh` |
| SessionStart (resume) | resume | `git_session_check.sh` |
| PreToolUse | Bash | `bash_command_validator.py` |
| PostToolUse | Bash | `auto_push_after_commit.sh` |
| PostToolUse | Edit\|Write | `hooks/post-edit-format.sh` |
| PostToolUse | Edit\|Write | `hooks/post-edit-typecheck.sh` (30s timeout) |
| PostToolUse | Edit\|Write | `hooks/post-edit-console-warn.sh` |
| PreCompact | * | `hooks/pre-compact-save.sh` |
| Stop | * | `hooks/stop-console-log-check.sh` |

### Plugins (11 enabled)

10 official: commit-commands, security-guidance, code-review, feature-dev, frontend-design, pr-review-toolkit, hookify, typescript-lsp, pyright-lsp, swift-lsp

1 custom: everything-claude-code (from GitHub)

---

## When to Re-Sync

Re-run the relevant copy step when you:
- Add/edit/delete an agent definition
- Change rules or contexts
- Modify settings.json (hooks, permissions, plugins)
- Add or change hook scripts in ~/scripts/

See `~/.claude/setup/sync-checklist.md` for a quick reference.
