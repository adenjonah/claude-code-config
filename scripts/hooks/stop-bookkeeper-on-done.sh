#!/bin/bash
# Stop hook: Remind Claude to invoke bookkeeper at session end.
# Fires once per session after a minimum activity threshold (8+ transcript entries)
# so trivial one-liner Q&A sessions are skipped.

INPUT=$(cat)
TRANSCRIPT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('transcript_path', ''))
except:
    print('')
" 2>/dev/null)
SESSION_ID=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('session_id', ''))
except:
    print('')
" 2>/dev/null)

[ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ] && exit 0

# Flag dir: one reminder per session
FLAG_DIR="$HOME/.claude/bookkeeper-done-flags"
mkdir -p "$FLAG_DIR"
FLAG_FILE="$FLAG_DIR/$SESSION_ID"

# Already reminded this session — skip
[ -f "$FLAG_FILE" ] && exit 0

# Count transcript entries — skip trivial sessions (< 8 lines of real activity)
ENTRY_COUNT=$(python3 -c "
import json
count = 0
with open('$TRANSCRIPT') as f:
    for line in f:
        try:
            d = json.loads(line)
            if d.get('type') in ('user', 'assistant'):
                count += 1
        except:
            pass
print(count)
" 2>/dev/null)

[ -z "$ENTRY_COUNT" ] && exit 0
[ "$ENTRY_COUNT" -lt 8 ] && exit 0

# Fire once
touch "$FLAG_FILE"
echo "SYSTEM [bookkeeper]: Session has real activity ($ENTRY_COUNT transcript entries). You MUST invoke the bookkeeper agent before this session ends — log what was done, decisions made, files changed, and anything worth remembering. This is non-negotiable per CLAUDE.md."

# Clean up flag files older than 7 days
find "$FLAG_DIR" -type f -mtime +7 -delete 2>/dev/null

exit 0
