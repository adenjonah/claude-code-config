#!/bin/bash
# Stop hook: Check all modified files for console.log after each response
# Only checks files that have been modified in the current git working tree

# Find git root
git_root=$(git rev-parse --show-toplevel 2>/dev/null)
[ -z "$git_root" ] && exit 0

cd "$git_root"

# Get modified JS/TS files (staged + unstaged)
modified_files=$(git diff --name-only --diff-filter=ACMR HEAD 2>/dev/null; git diff --name-only --diff-filter=ACMR --cached 2>/dev/null)

if [ -z "$modified_files" ]; then
  exit 0
fi

# Filter to JS/TS files and check for console.log
files_with_logs=""
for file in $modified_files; do
  case "$file" in
    *.ts|*.tsx|*.js|*.jsx)
      if [ -f "$file" ] && grep -q "console\.log" "$file" 2>/dev/null; then
        count=$(grep -c "console\.log" "$file")
        files_with_logs="$files_with_logs\n  $file ($count)"
      fi
      ;;
  esac
done

if [ -n "$files_with_logs" ]; then
  echo "[Hook] console.log found in modified files:$files_with_logs" >&2
  echo "[Hook] Remove console.log before committing." >&2
fi

exit 0
