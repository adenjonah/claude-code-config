#!/bin/bash
# PostToolUse hook: auto-push after git commit succeeds
# Receives TOOL_INPUT as JSON with the bash command

# Only care about Bash tool
if [ "$TOOL_USE_NAME" != "Bash" ]; then
  exit 0
fi

# Check if the command was a git commit (not amend, not dry-run)
COMMAND=$(echo "$TOOL_USE_INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('command', ''))" 2>/dev/null)

if echo "$COMMAND" | grep -qE '^\s*git\s+commit\b'; then
  # Only push if the commit succeeded (exit code 0)
  if [ "$TOOL_USE_EXIT_CODE" = "0" ]; then
    if ! git push 2>&1; then
      echo "⚠️  AUTO_PUSH_FAILED: git push failed (exit $?). Changes are committed locally but NOT pushed." >&2
    fi
  fi
fi
