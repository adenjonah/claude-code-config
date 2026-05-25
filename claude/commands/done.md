# /done — Stage this session, then clear

Arguments: $ARGUMENTS

## What this does

Wraps `/bk` + `/clear` into one step. Stages a session summary asynchronously and clears the conversation. The bookkeeper runs detached — no need to wait.

## Step 1 — Compose the session summary in your head

Pull from the conversation transcript. Do NOT re-read files or re-investigate. Mentally compose markdown for these sections:

- **What was worked on** — features, bugs, refactors, research, planning, writing
- **Decisions made and why** — design choices, trade-offs, alternatives considered
- **Files touched** — with brief description of changes per file
- **Bugs found / fixed** — root cause and the fix
- **Notes, ideas, deadlines** — anything the user mentioned worth remembering
- **Caveats / deferred** — things that did not work or were left for later

If `$ARGUMENTS` is non-empty, treat it as additional framing.

## Step 2 — Stage and launch in a single Bash call

Output ONE Bash command using the template below. Replace each `<<<...>>>` placeholder with the markdown content you composed in Step 1 (literal markdown — no shell escaping needed; the body heredoc is single-quoted).

```bash
mkdir -p "$HOME/.claude/pending-sessions"
TS=$(date '+%Y-%m-%d-%H-%M-%S')
F="$HOME/.claude/pending-sessions/$TS.md"
{
  printf '# Bookkeeper Session — %s\n\n' "$(date '+%Y-%m-%d %H:%M')"
  printf 'Staged: %s\nProject: %s\nBranch: %s\nWorking dir: %s\n\n' \
    "$TS" "$(basename "$PWD")" "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo none)" "$PWD"
  cat <<'BK_BODY'
## Session Summary

### What was worked on
<<<WHAT was worked on>>>

### Decisions made
<<<DECISIONS made and why>>>

### Files touched
<<<FILES touched>>>

### Bugs found / fixed
<<<BUGS found and fixed>>>

### Notes, ideas, deadlines
<<<NOTES, ideas, deadlines>>>

### Caveats / deferred
<<<CAVEATS, deferred items>>>
BK_BODY
} > "$F"
nohup /Users/jonah/scripts/bookkeeper-process.sh "$F" >> "${F%.md}.log" 2>&1 &
PID=$!
echo "Session staged → $F | Background bookkeeper launched (PID: $PID). Clearing."
```

Notes:
- The `'BK_BODY'` heredoc is single-quoted — paste markdown verbatim, no escaping.
- Avoid putting a line that is exactly `BK_BODY` inside the body (vanishingly unlikely).
- One tool call total. No `Write` tool → no Write fact-forcing gate.

## Step 3 — Output the printed line, then clear

Output the line that the bash command printed. Then immediately invoke the SlashCommand tool with `command: "/clear"` to clear the conversation.

If SlashCommand is unavailable, end with: `Session staged. Background bookkeeper launched. Run /clear when ready.`

Do NOT wait for the bookkeeper to finish before clearing — it is detached.
