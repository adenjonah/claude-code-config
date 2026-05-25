#!/bin/bash
# PostToolUse hook: Auto-format JS/TS files after edits
# Detects Biome or Prettier and formats the edited file

input=$(cat)
tool_name=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$tool_name" != "Edit" ] && [ "$tool_name" != "Write" ]; then
  exit 0
fi

file_path=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only format JS/TS files
case "$file_path" in
  *.ts|*.tsx|*.js|*.jsx|*.json) ;;
  *) exit 0 ;;
esac

# Check if file exists
[ -f "$file_path" ] || exit 0

# Find project root (nearest package.json)
dir=$(dirname "$file_path")
project_root=""
while [ "$dir" != "/" ]; do
  if [ -f "$dir/package.json" ]; then
    project_root="$dir"
    break
  fi
  dir=$(dirname "$dir")
done

[ -z "$project_root" ] && exit 0

# Try Biome first, then Prettier
if [ -f "$project_root/biome.json" ] || [ -f "$project_root/biome.jsonc" ]; then
  npx --yes @biomejs/biome format --write "$file_path" 2>/dev/null
elif command -v prettier &>/dev/null || [ -f "$project_root/node_modules/.bin/prettier" ]; then
  npx prettier --write "$file_path" 2>/dev/null
fi

exit 0
