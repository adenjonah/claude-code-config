#!/bin/bash
# PostToolUse hook: TypeScript check after editing .ts/.tsx files
# Runs tsc --noEmit on the project containing the edited file

input=$(cat)
tool_name=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$tool_name" != "Edit" ] && [ "$tool_name" != "Write" ]; then
  exit 0
fi

file_path=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only check TypeScript files
case "$file_path" in
  *.ts|*.tsx) ;;
  *) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

# Find project root with tsconfig
dir=$(dirname "$file_path")
project_root=""
while [ "$dir" != "/" ]; do
  if [ -f "$dir/tsconfig.json" ]; then
    project_root="$dir"
    break
  fi
  dir=$(dirname "$dir")
done

[ -z "$project_root" ] && exit 0

# Run tsc --noEmit, show only errors (not warnings)
cd "$project_root"
errors=$(npx tsc --noEmit 2>&1 | grep -c "error TS" 2>/dev/null || echo "0")

if [ "$errors" -gt 0 ]; then
  echo "[Hook] TypeScript: $errors error(s) detected after edit" >&2
  npx tsc --noEmit 2>&1 | grep "error TS" | head -5 >&2
fi

exit 0
