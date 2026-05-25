#!/bin/bash
# Auto-sync Obsidian vault via git
# Usage: obsidian-sync.sh [vault-path]
# Defaults to ~/notes

set -e

VAULT="${1:-$HOME/notes}"
LOG_TAG="obsidian-sync"

cd "$VAULT" || { echo "[$LOG_TAG] ERROR: Could not cd to $VAULT" >&2; exit 1; }

# Verify this is a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "[$LOG_TAG] ERROR: $VAULT is not a git repository" >&2
    exit 1
fi

# Pull remote changes first (rebase to keep history clean)
if ! git pull --rebase --autostash 2>&1; then
    echo "[$LOG_TAG] ERROR: git pull failed — vault may be out of sync" >&2
    exit 1
fi

# Check for bookkeeper lockfile — skip sync if mid-write
if [ -f "$VAULT/.bookkeeper-writing" ]; then
    echo "[$LOG_TAG] Bookkeeper is writing — skipping this sync cycle"
    exit 0
fi

# Stage all changes
git add -A

# Only commit if there are changes
if ! git diff --cached --quiet; then
    git commit -m "vault sync: $(date '+%Y-%m-%d %H:%M')"
fi

# Push if there are commits to push
if [ "$(git rev-list --count @{u}..HEAD 2>/dev/null)" -gt 0 ]; then
    if ! git push 2>&1; then
        echo "[$LOG_TAG] ERROR: git push failed — commits are unpushed" >&2
        exit 1
    fi
fi
