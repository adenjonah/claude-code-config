#!/bin/bash
# Git session check — runs on SessionStart to detect sync issues
# across multiple machines.

# Save original directory to return to for project check
ORIGINAL_DIR="$(pwd)"

# --- Vault sync (always, regardless of current directory) ---
VAULT="$HOME/notes"
if [ -d "$VAULT/.git" ]; then
  cd "$VAULT"
  git fetch --quiet 2>/dev/null
  VAULT_LOCAL=$(git rev-parse HEAD 2>/dev/null)
  VAULT_REMOTE=$(git rev-parse origin/main 2>/dev/null)
  if [ -n "$VAULT_LOCAL" ] && [ -n "$VAULT_REMOTE" ] && [ "$VAULT_LOCAL" != "$VAULT_REMOTE" ]; then
    VAULT_BASE=$(git merge-base HEAD origin/main 2>/dev/null)
    if [ "$VAULT_LOCAL" = "$VAULT_BASE" ]; then
      # Vault is behind — pull silently
      git pull --rebase --autostash --quiet 2>/dev/null
      echo "VAULT_SYNC: Pulled latest notes from remote."
    elif [ "$VAULT_REMOTE" = "$VAULT_BASE" ]; then
      echo "VAULT_SYNC: Vault has unpushed notes. Pushing now."
      git push --quiet 2>/dev/null
    else
      echo "VAULT_SYNC_WARNING: Vault has diverged from remote. Resolve manually in ~/notes/."
    fi
  fi
  # Commit any uncommitted vault changes (from bookkeeper or Obsidian edits)
  cd "$VAULT"
  git add -A 2>/dev/null
  if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "vault sync: $(date '+%Y-%m-%d %H:%M')" --quiet 2>/dev/null
    git push --quiet 2>/dev/null
    echo "VAULT_SYNC: Committed and pushed uncommitted vault changes."
  fi
fi

# --- Project repo sync (current working directory) ---
cd "$ORIGINAL_DIR" 2>/dev/null || cd "$HOME"

# Only run in git repos
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  exit 0
fi

BRANCH=$(git branch --show-current 2>/dev/null)
if [ -z "$BRANCH" ]; then
  exit 0
fi

# Fetch latest from remote (quiet, don't block on network issues)
git fetch --quiet 2>/dev/null

UPSTREAM="origin/$BRANCH"

# Check if upstream exists
if ! git rev-parse --verify "$UPSTREAM" &>/dev/null; then
  echo "GIT_SYNC: Branch '$BRANCH' has no upstream tracking branch."
  exit 0
fi

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base HEAD "$UPSTREAM" 2>/dev/null)

# Check for uncommitted changes
DIRTY=""
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  DIRTY="yes"
fi

if [ "$LOCAL" = "$REMOTE" ]; then
  if [ -n "$DIRTY" ]; then
    echo "GIT_SYNC: Up to date with remote, but there are uncommitted local changes."
    git status --short
  fi
elif [ "$LOCAL" = "$BASE" ]; then
  BEHIND=$(git rev-list --count HEAD.."$UPSTREAM")
  echo "GIT_SYNC_WARNING: Local branch '$BRANCH' is $BEHIND commit(s) BEHIND remote."
  echo "Remote has newer changes — likely pushed from another machine."
  echo "Ask the user before proceeding: pull changes with 'git pull', or continue working on the current state?"
  if [ -n "$DIRTY" ]; then
    echo ""
    echo "NOTE: There are also uncommitted local changes:"
    git status --short
  fi
elif [ "$REMOTE" = "$BASE" ]; then
  AHEAD=$(git rev-list --count "$UPSTREAM"..HEAD)
  echo "GIT_SYNC: Local branch '$BRANCH' is $AHEAD commit(s) ahead of remote (unpushed)."
  if [ -n "$DIRTY" ]; then
    echo "There are also uncommitted local changes."
  fi
else
  AHEAD=$(git rev-list --count "$UPSTREAM"..HEAD)
  BEHIND=$(git rev-list --count HEAD.."$UPSTREAM")
  echo "GIT_SYNC_WARNING: Branch '$BRANCH' has DIVERGED from remote."
  echo "Local is $AHEAD ahead and $BEHIND behind."
  echo "Ask the user how to resolve before doing any work."
fi
