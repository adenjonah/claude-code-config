#!/bin/bash
# bookkeeper-process.sh — Run the bookkeeper agent from a staged session file.
# Intended to run detached (nohup + disown) so it survives after CC closes.
# Usage: bookkeeper-process.sh <staged_file>

# Ensure PATH includes common install locations for claude CLI
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$HOME/.local/bin:/usr/local/bin:$PATH"

STAGED_FILE="${1:-}"
if [ -z "$STAGED_FILE" ]; then
    echo "Usage: bookkeeper-process.sh <staged_file>" >&2
    exit 1
fi

LOG_FILE="${STAGED_FILE%.md}.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

log "=== Bookkeeper process started for: $(basename "$STAGED_FILE") ==="

if [ ! -f "$STAGED_FILE" ]; then
    log "ERROR: staged file not found: $STAGED_FILE"
    exit 1
fi

CLAUDE_BIN=$(which claude 2>/dev/null || echo "$HOME/.local/bin/claude")
if [ ! -x "$CLAUDE_BIN" ]; then
    log "ERROR: claude CLI not found at $CLAUDE_BIN"
    exit 1
fi

log "Using claude at: $CLAUDE_BIN"
log "Running bookkeeper agent..."

# Run bookkeeper agent non-interactively.
# --print:          non-interactive mode (exits when done)
# --agent bookkeeper: loads ~/.claude/agents/bookkeeper.md as the agent
# Prompt is the full staged file content (session summary)
"$CLAUDE_BIN" --print --agent bookkeeper "$(cat "$STAGED_FILE")" >> "$LOG_FILE" 2>&1
EXIT=$?

if [ $EXIT -eq 0 ]; then
    log "=== Bookkeeper completed successfully ==="
    PROCESSED_DIR="$(dirname "$STAGED_FILE")/processed"
    mkdir -p "$PROCESSED_DIR"
    mv "$STAGED_FILE" "$PROCESSED_DIR/"
    log "Staged file moved to processed/"
else
    log "=== Bookkeeper FAILED (exit $EXIT) — staged file preserved for retry ==="
fi
