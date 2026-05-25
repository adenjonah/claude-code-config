---
name: log-session
description: Log the current session to .claude/sessions.json with git commits, timestamps, and resume info. Use when finishing significant work, when user says "log", "ending", "wrapping up", "done for now", or similar.
---

# Log Session Skill

Log the current agent session to a project-local JSON file so it can be found and resumed later.

---

## When to Trigger

- User says `/log-session`
- User says "log this", "ending", "wrapping up", "done for now", "save session", or similar wind-down language
- You've completed significant work (multiple commits, a feature, a major fix) and the conversation is naturally ending
- Before context compaction if substantial work was done

---

## Steps

### 1. Get the session ID

Find the current session ID by reading the first line of the most recently modified `.jsonl` file in the project's Claude directory:

```bash
PROJECT_DIR=$(echo "$PWD" | sed 's|/|−|g; s|^−||')
# The project dir in .claude/projects uses dashes, find the right one
ls -t ~/.claude/projects/*$(basename "$PWD")/*.jsonl 2>/dev/null | head -1
```

Parse the first line as JSON and extract `sessionId`.

If you cannot determine the session ID, use `"unknown"` and note it — the entry is still valuable for the timestamp, commits, and summary.

### 2. Get git commits from this session

```bash
git log --oneline --after="<session_start_timestamp>" --format="%h %s"
```

If the session start time isn't clear, use the last 24 hours or inspect the transcript's first entry timestamp.

Collect commit hashes and messages.

### 3. Determine the session summary

Write a 1-2 sentence summary of what was accomplished. Be specific — name the features, files, or systems touched. This is what a future agent (or the user) will read to decide whether to resume.

### 4. Note pending work

If there's unfinished work, blockers, or next steps, capture them in `pendingWork`. Be specific enough that a resumed session can pick up without re-reading the whole codebase.

### 5. Write to `.claude/sessions.json`

The file lives at `<project_root>/.claude/sessions.json`. Create it if it doesn't exist.

**Schema:**

```json
[
  {
    "sessionId": "uuid-string",
    "directory": "/absolute/path/to/project",
    "branch": "main",
    "startedAt": "ISO-8601 timestamp of first message",
    "loggedAt": "ISO-8601 timestamp of when this entry was written",
    "commits": [
      { "hash": "84408b7", "message": "Add API Keys tab to settings page" }
    ],
    "summary": "What was accomplished in 1-2 sentences",
    "status": "completed | paused | blocked",
    "pendingWork": "Optional: what's left to do, blockers, next steps",
    "resumeCommand": "claude --resume <sessionId>"
  }
]
```

**Status values:**
- `completed` — work is done, no pending tasks
- `paused` — work is in progress, can be resumed
- `blocked` — work hit a blocker that needs external resolution

**Important:**
- Read the existing file first, parse it, append the new entry, write it back
- If the file doesn't exist, create it with a single-entry array
- The file should be `.gitignore`d (it contains local paths and session IDs)
- Use `loggedAt` as the current time, `startedAt` from the transcript if available

### 6. Ensure `.claude/sessions.json` is gitignored

Check if `.claude/` or `.claude/sessions.json` is in `.gitignore`. If not, add `.claude/sessions.json` to `.gitignore`.

### 7. Confirm to the user

Print a brief confirmation:

```
Session logged to .claude/sessions.json
  ID: <sessionId>
  Commits: <N> commits on <branch>
  Status: <status>
  Resume: claude --resume <sessionId>
```

---

## Resuming a Session

When the user wants to resume a previous session, they can:

1. Read `.claude/sessions.json` to find the session
2. Run `claude --resume <sessionId>` from the same directory

If the user asks "what was I working on?" or "show me recent sessions", read `.claude/sessions.json` and present the entries.

---

## Notes

- This skill is about **logging**, not **checkpointing**. It doesn't save code state (that's what git is for). It saves the *conversation context* link so you can get back to the agent's understanding.
- One session can have multiple log entries if work spans multiple phases.
- Keep summaries scannable — a user should be able to skim 20 entries and find what they need.
