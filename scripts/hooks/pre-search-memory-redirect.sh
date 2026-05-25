#!/bin/bash
# PreToolUse hook (Grep/Glob): Redirect exploratory codebase searches to
# memory-retrieval agent (which uses Graphify) on the first broad search in
# a project directory per session. Subsequent searches proceed normally.

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('session_id', ''))
except:
    print('')
" 2>/dev/null)

TOOL=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('tool_name', ''))
except:
    print('')
" 2>/dev/null)

TOOL_INPUT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(json.dumps(d.get('tool_input', {})))
except:
    print('{}')
" 2>/dev/null)

[ -z "$SESSION_ID" ] && exit 0

# Extract search path and pattern
SEARCH_PATH=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    # Grep uses 'path', Glob uses 'path' too
    print(d.get('path', ''))
except:
    print('')
" 2>/dev/null)

PATTERN=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    # Grep: 'pattern', Glob: 'pattern'
    print(d.get('pattern', ''))
except:
    print('')
" 2>/dev/null)

HOME_DIR="$HOME"
DEV_DIR="$HOME/dev"

# Only intercept searches inside ~/dev/ (not config, notes, scripts)
IS_DEV_SEARCH=$(python3 -c "
import sys, os
path = '$SEARCH_PATH'
dev = '$DEV_DIR'
home = '$HOME_DIR'

if not path:
    # No explicit path — could be cwd-based. Check if cwd is under dev/
    cwd = os.getcwd()
    print('1' if cwd.startswith(dev + '/') else '0')
else:
    abs_path = os.path.abspath(os.path.expanduser(path))
    print('1' if abs_path.startswith(dev + '/') or abs_path == dev else '0')
" 2>/dev/null)

[ "$IS_DEV_SEARCH" != "1" ] && exit 0

# Extract the project name (first path component under ~/dev/)
PROJECT=$(python3 -c "
import sys, os
path = '$SEARCH_PATH'
dev = '$DEV_DIR'

if not path:
    cwd = os.getcwd()
    rel = os.path.relpath(cwd, dev)
else:
    abs_path = os.path.abspath(os.path.expanduser(path))
    rel = os.path.relpath(abs_path, dev)

parts = rel.split(os.sep)
print(parts[0] if parts and parts[0] != '.' else '')
" 2>/dev/null)

[ -z "$PROJECT" ] || [ "$PROJECT" = "_archive" ] && exit 0

# Check if a Graphify graph exists for this project
GRAPH_PATH="$HOME/notes/projects/$PROJECT/graphify/graphify-out/graph.json"
[ ! -f "$GRAPH_PATH" ] && exit 0

# Per-session per-project flag: only suggest once
FLAG_DIR="$HOME/.claude/memory-redirect-flags"
mkdir -p "$FLAG_DIR"
FLAG_FILE="$FLAG_DIR/${SESSION_ID}_${PROJECT}"

[ -f "$FLAG_FILE" ] && exit 0

# Detect if this is a broad/exploratory search (not a targeted lookup)
IS_BROAD=$(python3 -c "
import sys, re
pattern = '$PATTERN'
tool = '$TOOL'
# Broad Glob: extension wildcards or deep wildcards
if tool == 'Glob':
    broad = bool(re.search(r'\*\*|\*\.\w+$|\*$', pattern))
    print('1' if broad else '0')
elif tool == 'Grep':
    # Broad Grep: searching across directories (path is a dir, not a specific file)
    import os
    path = '$SEARCH_PATH'
    if not path:
        print('1')  # no path = current dir = broad
    else:
        abs_path = os.path.abspath(os.path.expanduser(path))
        print('1' if os.path.isdir(abs_path) else '0')
else:
    print('1')
" 2>/dev/null)

[ "$IS_BROAD" != "1" ] && exit 0

# Mark as suggested so we don't repeat for this session+project
touch "$FLAG_FILE"

# Clean old flags (> 7 days)
find "$FLAG_DIR" -type f -mtime +7 -delete 2>/dev/null

echo "SYSTEM [pre-search-memory-redirect]: A Graphify knowledge graph exists for '$PROJECT' at $GRAPH_PATH. Before running broad file searches, use the memory-retrieval agent to query this graph — it surfaces cross-file relationships and past decisions that grep cannot find, and uses far less context. Run memory-retrieval first, then use Grep/Glob only for targeted lookups that the graph doesn't answer."

# Do NOT block (exit 0) — let the tool proceed if Claude still wants to
exit 0
