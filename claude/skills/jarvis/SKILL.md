---
name: jarvis
description: Orient on what's been happening — recent Claude Code sessions, vault changes, git commits in active repos, and what to do next. Use when the user invokes /jarvis, asks "what's going on", "catch me up", "what should I work on", or "I just sat down, where am I."
---

# Jarvis

You are Jonah's orientation layer. He sat down and wants to know what's been happening and what to do next.

**Make no assumptions about which project he cares about.** Read the data, synthesize across all of it, and propose the most leveraged next moves.

## If the request is narrow, do only that

If he asks something specific ("what changed in voices-of-history?", "what sessions are running?", "what did I do in the vault today?"), run only the relevant section below. The full sweep is for the unbounded "catch me up" case.

---

## Step 1 — Establish the cursor

The cursor tracks the last successful Jarvis run. All "since last time" queries use it.

```bash
mkdir -p ~/.jarvis
if [ ! -f ~/.jarvis/cursor ]; then
  touch -t $(date -v-24H +%Y%m%d%H%M.%S) ~/.jarvis/cursor 2>/dev/null || \
  touch -d "24 hours ago" ~/.jarvis/cursor 2>/dev/null
fi
CURSOR_ISO=$(stat -f %Sm -t %Y-%m-%dT%H:%M:%S ~/.jarvis/cursor 2>/dev/null || \
             stat -c %y ~/.jarvis/cursor 2>/dev/null | cut -d. -f1 | tr ' ' 'T')
echo "Cursor: $CURSOR_ISO"
```

Do NOT bump the cursor yet — only after a successful synthesis.

---

## Step 2 — Gather context (run in parallel where possible)

### A. Recent Claude Code sessions (via recon API)

```bash
# Use the recon backend — much faster than parsing JSONL files
curl -s "localhost:3100/api/sessions?limit=20" 2>/dev/null
```

If recon is not responding, start it:
```bash
nohup ~/dev/claude-manager/server/target/release/recon serve --quiet \
  >> ~/.manager-skill/recon.log 2>&1 &
sleep 2 && curl -s "localhost:3100/api/sessions?limit=20"
```

For each session, note:
- `display_name` / `project_name` — what project
- `status` — working / idle / input
- `summary.current_task` and `summary.overview` — what it's doing
- `last_activity` — how recent
- `managed` — whether it's in a tmux session (true = can receive messages)

For sessions with `chars_since_summary > 3000`, trigger a fresh summary:
```bash
curl -s -X POST "localhost:3100/api/sessions/<ID>/summarize"
```

If you need to understand what a session actually did in detail, read its JSONL:
```bash
# Find the JSONL for a session
PROJECT_ENCODED=$(echo "<cwd>" | sed 's|^/||; s|/|-|g')
ls ~/.claude/projects/-${PROJECT_ENCODED}/*.jsonl 2>/dev/null | head -3
tail -n 100 <jsonl_path> | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        if d.get('type') == 'assistant' and 'message' in d:
            for block in d['message'].get('content', []):
                if block.get('type') == 'text':
                    print('ASSISTANT:', block['text'][:200])
        elif d.get('type') == 'user':
            for block in d.get('message', {}).get('content', []):
                if isinstance(block, dict) and block.get('type') == 'text':
                    print('USER:', block['text'][:200])
    except: pass
"
```

### B. Obsidian vault recent activity

Vault is at `~/notes/`. Get the cumulative diff since the cursor — do not restrict by subdirectory, the user writes everywhere.

```bash
VAULT="$HOME/notes"
git -C "$VAULT" log --since="$CURSOR_ISO" --name-status \
  --pretty=format:"=== %h %s ===" \
  -- ':(exclude).obsidian' ':(exclude)*.DS_Store' 2>/dev/null

git -C "$VAULT" diff "@{$CURSOR_ISO}..HEAD" -- '*.md' \
  ':(exclude).obsidian' ':(exclude)*.DS_Store' 2>/dev/null | head -200
```

Read the diffs to see what *content* changed, not just file names. If a file's diff looks substantive, read it in full.

### C. Recent commits in active repos

Discover repos from session cwds — whatever Jonah has been working in recently is automatically tracked.

```bash
# Get unique cwds from recent sessions via recon
curl -s "localhost:3100/api/sessions?limit=20" 2>/dev/null | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
cwds = set()
for room in data.get('rooms', []):
    for s in room.get('sessions', []):
        if s.get('cwd'):
            cwds.add(s['cwd'])
for c in cwds:
    print(c)
" | while read cwd; do
    repo=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)
    [ -n "$repo" ] && echo "$repo"
done | sort -u | while read repo; do
    echo "=== $repo ==="
    git -C "$repo" log --since="$CURSOR_ISO" --pretty=format:"%h %s" --no-merges 2>/dev/null
    echo
done
```

Also scan `~/dev/` for any repos with recent activity not captured above:
```bash
for repo in ~/dev/*/; do
    recent=$(git -C "$repo" log --since="$CURSOR_ISO" --oneline 2>/dev/null | head -1)
    [ -n "$recent" ] && echo "$(basename $repo): $recent"
done
```

### D. Open tasks

Read `~/notes/tasks.md` — this is Jonah's persistent task queue across sessions.

```bash
grep -n "- \[ \]" ~/notes/tasks.md 2>/dev/null || echo "(no open tasks)"
```

Parse out open items (`- [ ]`), their project tags (`@project`), and priority markers (`::high`, `::med`, `::low`). These represent things he has explicitly decided to do but hasn't started yet — surface them in the synthesis alongside what sessions and commits show.

If the file doesn't exist or is empty, skip this section without comment.

### E. Remote machine state

Check what the other machine has been doing. Try live first, fall back to vault.

**Live query (if reachable):**
```bash
bash ~/scripts/remote-recon.sh mac-mini 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for s in data.get('sessions', []):
        print(f\"{s.get('display_name','?')} | {s.get('status','?')} | {(s.get('summary',{}).get('current_task') or '—')[:60]}\")
except:
    print('(parse error)')
"
```

**Vault fallback (always available, may be stale):**
```bash
cat ~/notes/machines/mac-mini-3/state.md 2>/dev/null || echo "(no remote state file yet)"
```

Check the `**Updated:**` line — if older than 4 hours, note it as potentially stale in the synthesis. Surface: what the remote was working on, whether it's currently active, any commits not in the local scan.

---

## Step 3 — Dig deeper if needed

The commands above give a summary view. Use judgment to go deeper:

- If a session summary hints at something unfinished → read its JSONL or ask it directly via `/consult`
- If a vault diff shows significant writing → read the full file
- If a repo shows commits but no session → investigate what was done
- If something looks like a deadline or blocker → surface it immediately

You have all of Claude Code's tools. Use them.

---

## Step 4 — Synthesize and respond

**There is no template.** The right response depends on what's actually happening.

Loose guidance:
- **Connect the streams** — don't dump four separate lists. Show how the session work relates to the vault writing and the git history. Jonah context-switches across 5+ projects daily; the synthesis is what's valuable.
- **Name the bottleneck** — what is actually blocking the next thing? If three projects have open threads but one is blocking something else, say that.
- **Propose next moves ranked by leverage** — three is a good default. Ask which (if any) he wants to act on; he may have arrived with a specific intent.
- **Be direct** — no preamble, no "I have analyzed your context." Just the synthesis and the proposed moves.

---

## Step 5 — Bump the cursor

Only after a successful synthesis:

```bash
touch ~/.jarvis/cursor
bash ~/scripts/machine-state.sh
```

If anything failed or the synthesis was incomplete, **do not bump** — the next invocation should see the same window.

---

## Notes

- Jarvis is standalone — do not assume any other process is running except recon (which it starts itself if needed)
- The cursor is the only persistent state — no cache, no config file
- If recon is down and sessions aren't available, proceed with vault + git data and note the gap
- If the vault git log fails (vault not a git repo), read the most recently modified files instead:
  ```bash
  find ~/notes -name "*.md" -newer ~/.jarvis/cursor -not -path "*/.obsidian/*" 2>/dev/null | head -20
  ```
- If something is broken, say so plainly rather than working around it silently
