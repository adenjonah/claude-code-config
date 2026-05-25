# Config Sync Quick Reference

When you change config on one machine, copy the relevant item to the other.

## What changed? -> What to copy

| I changed... | Copy this |
|---|---|
| An agent definition | `~/.claude/agents/<file>.md` (or the whole directory) |
| A rule file | `~/.claude/rules/<common or typescript>/<file>.md` |
| A context file | `~/.claude/contexts/<file>.md` |
| A command | `~/.claude/commands/<file>.md` |
| Hooks, permissions, or plugins | `~/.claude/settings.json` |
| A hook script | `~/scripts/hooks/<file>` |
| A utility script | `~/scripts/<file>` |
| Home CLAUDE.md | `~/CLAUDE.md` |
| Dev CLAUDE.md | `~/dev/CLAUDE.md` |
| The setup guide itself | `~/.claude/setup/` (both files) |

## Copying between machines

If both machines are on the same network (e.g., via Tailscale):
```bash
# From desktop to laptop (adjust hostname)
scp -r ~/.claude/agents/ laptop:~/.claude/agents/
scp ~/.claude/settings.json laptop:~/.claude/settings.json
scp -r ~/scripts/ laptop:~/scripts/
```

If not on the same network, use a USB drive, AirDrop, or manually copy the files.

## After copying

- Verify scripts are executable: `chmod +x ~/scripts/*.sh ~/scripts/*.py ~/scripts/hooks/*.sh`
- Start a Claude Code session to confirm hooks work
- If `settings.json` changed, restart any running Claude Code sessions

## Don't copy these

- `settings.local.json` — machine-specific permissions
- `projects/` — memory built per-machine
- `plugins/cache/` — auto-rebuilt
- Any session data (plans, tasks, history, debug)
