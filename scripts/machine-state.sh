#!/bin/bash
# Writes current machine state to ~/notes/machines/<hostname>/state.md
# Called by: bookkeeper (before vault git commit), Jarvis (after cursor bump)
set -uo pipefail

HOSTNAME=$(hostname -s)
VAULT="$HOME/notes"
STATE_DIR="$VAULT/machines/$HOSTNAME"
STATE_FILE="$STATE_DIR/state.md"
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null | head -1 || echo "unknown")
NOW=$(date -u +%Y-%m-%dT%H:%M:%S)
JARVIS_CURSOR=$(stat -f %Sm -t %Y-%m-%dT%H:%M:%S ~/.jarvis/cursor 2>/dev/null || echo "never")

mkdir -p "$STATE_DIR"

# Sessions from recon (non-blocking, 3s max)
SESSIONS_TABLE=$(curl -s --max-time 3 "http://localhost:3100/api/sessions?limit=20" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    rows = []
    # recon API wraps sessions under 'rooms[].sessions[]'
    for room in data.get('rooms', data.get('sessions', [])):
        sessions = room.get('sessions', [room]) if isinstance(room, dict) and 'sessions' in room else [room]
        for s in sessions:
            project = s.get('display_name', room.get('room_id', '?') if isinstance(room, dict) else '?')
            last = (s.get('last_activity') or '')[:16]
            msgs = s.get('messages', [])
            last_msg = msgs[-1].get('text', '')[:60] if msgs else '—'
            rows.append(f'| {project} | active | {last} | {last_msg} |')
    print('\n'.join(rows) if rows else '| — | — | — | No active sessions |')
except:
    print('| — | — | — | recon unavailable |')
" 2>/dev/null || echo "| — | — | — | recon unavailable |")

# Recent commits since last Jarvis run
COMMITS=$(for repo in ~/dev/*/; do
    git -C "$repo" log --since="$JARVIS_CURSOR" --pretty=format:"- \`$(basename $repo)\` %h %s" --no-merges 2>/dev/null | head -3
done 2>/dev/null | head -20)
[ -z "$COMMITS" ] && COMMITS="- (none)"

# Vault changes since last Jarvis run
VAULT_FILES=$(git -C "$VAULT" diff "@{$JARVIS_CURSOR}..HEAD" --name-only -- '*.md' \
  ':(exclude).obsidian' ':(exclude)*.DS_Store' 2>/dev/null | sed 's/^/- /' | head -15)
[ -z "$VAULT_FILES" ] && VAULT_FILES="- (none)"

# Open tasks
OPEN_TASKS=$(grep "- \[ \]" "$VAULT/tasks.md" 2>/dev/null | head -20)
[ -z "$OPEN_TASKS" ] && OPEN_TASKS="- (none)"

cat > "$STATE_FILE" << STATEOF
# Machine State: $HOSTNAME

**Updated:** $NOW
**Hostname:** $HOSTNAME
**Tailscale IP:** $TAILSCALE_IP

## Active Sessions

| Project | Status | Last Activity | Task |
|---------|--------|---------------|------|
$SESSIONS_TABLE

## Recent Commits (since $JARVIS_CURSOR)

$COMMITS

## Vault Activity (since $JARVIS_CURSOR)

$VAULT_FILES

## Open Tasks

$OPEN_TASKS

## Jarvis Cursor

Last Jarvis run: $JARVIS_CURSOR
STATEOF

echo "machine-state: wrote $STATE_FILE"
