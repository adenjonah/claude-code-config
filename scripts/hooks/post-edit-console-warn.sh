#!/bin/bash
# PostToolUse hook: Warn about console.log in edited JS/TS files

input=$(cat)
tool_name=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$tool_name" != "Edit" ] && [ "$tool_name" != "Write" ]; then
  exit 0
fi

file_path=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only check JS/TS files
case "$file_path" in
  *.ts|*.tsx|*.js|*.jsx) ;;
  *) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

# Check for console.log
count=$(grep -c "console\.log" "$file_path" 2>/dev/null || echo "0")

if [ "$count" -gt 0 ]; then
  echo "[Hook] Warning: $count console.log statement(s) found in $(basename "$file_path"). Remove before committing." >&2
fi

exit 0
