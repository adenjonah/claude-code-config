#!/bin/bash
# PreCompact hook: Save a snapshot of current state before context compaction
# Logs what files are being worked on so context isn't lost

state_dir="$HOME/.claude/compact-state"
mkdir -p "$state_dir"

timestamp=$(date +%Y%m%d-%H%M%S)
state_file="$state_dir/pre-compact-$timestamp.txt"

{
  echo "=== Pre-Compact State Snapshot ==="
  echo "Time: $(date)"
  echo ""

  # Current directory
  git_root=$(git rev-parse --show-toplevel 2>/dev/null)
  if [ -n "$git_root" ]; then
    echo "Git root: $git_root"
    echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
    echo ""
    echo "Modified files:"
    git status --short 2>/dev/null
    echo ""
    echo "Recent commits:"
    git log --oneline -5 2>/dev/null
  fi
} > "$state_file" 2>/dev/null

# Keep only last 10 snapshots
ls -t "$state_dir"/pre-compact-*.txt 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null

exit 0
