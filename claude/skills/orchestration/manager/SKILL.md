---
name: manager
description: Interact with other Claude Code sessions running on this machine via the claude-manager backend. Use when the user asks about what other sessions are doing, wants to send a message to a specific session, needs to list/kill/resume sessions, or wants to coordinate between them. Examples - "how's the BK session doing?", "tell the goyslop session to pause", "list all my sessions", "what's the manager working on", "resume the auth refactor session".
---

# Manager Skill

You are interacting with other Claude Code sessions through the claude-manager backend at `localhost:3100`. The backend is a Rust HTTP API that indexes every running Claude Code session and exposes tools to list, query, send messages to, kill, resume, and rename them.

This skill lets any Claude Code session reach those tools via plain HTTP. You are the user's orchestration interface to their fleet of sessions.

## Before you start — ensure the backend is running

This skill must be 100% black-box usable. If the backend isn't up, start it yourself. Don't ask the user to do it.

Run this block at the start of every invocation. It's idempotent — fast when the backend is already up, and self-starts it when it's not:

```bash
ensure_recon() {
  # Fast path: already up
  if curl -sf localhost:3100/api/sessions > /dev/null 2>&1; then
    return 0
  fi

  # Find the recon binary
  local RECON=""
  for candidate in \
    "$HOME/dev/claude-manager/server/target/release/recon" \
    "$HOME/dev/claude-manager/bin/recon"; do
    if [ -x "$candidate" ]; then
      RECON="$candidate"
      break
    fi
  done

  if [ -z "$RECON" ]; then
    echo "ERR: recon binary not found. Build it: cd ~/dev/claude-manager && cargo build --release --manifest-path server/Cargo.toml" >&2
    return 1
  fi

  # Start in background, detached, logs to ~/.manager-skill/recon.log
  mkdir -p "$HOME/.manager-skill"
  local LOG="$HOME/.manager-skill/recon.log"
  local MANAGER_DIR="$HOME/dev/claude-manager/server/manager"

  nohup "$RECON" serve --quiet  \
    >> "$LOG" 2>&1 &
  disown $! 2>/dev/null || true

  # Poll for readiness (up to ~6 seconds)
  for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if curl -sf localhost:3100/api/sessions > /dev/null 2>&1; then
      echo "recon started (logs: $LOG)"
      return 0
    fi
    sleep 0.5
  done

  echo "ERR: recon didn't come up within 6s. Check $LOG" >&2
  return 1
}

ensure_recon || exit 1
```

If `ensure_recon` fails (binary missing, startup timeout), tell the user plainly what went wrong and point them at the log file — don't just say "backend is down." If the binary is missing, the user needs to build it once: `cd ~/dev/claude-manager && cargo build --release --manifest-path server/Cargo.toml`. You can offer to run the build for them but it takes 1-2 minutes, so confirm before starting it.

The backend stays running in the background across invocations. You only pay the startup cost once per machine boot.

## Dispatching work

For complex tasks — multi-file, needs analysis, takes real time — you're the manager, not the builder. Usually that means one managed session with ABW. Write a high-level spec, create the session, send the prompt, then monitor. Don't try to do the build work yourself in the manager session.

Use judgment on how many sessions. Usually one is right. Sometimes the task naturally splits. The point is: don't fragment by default, and don't build by default.

## Talking to sessions

Send plain-language messages through the API. Don't send slash commands — they can have side effects in your own session context. If the session needs to run `/ralph-loop`, tell it in English and let it invoke the command itself.

## Verifying work

When a session says it's done, **don't just read its summary and report it back.** Talk to the session. Ask it pointed questions: "Did you actually modify river-mobile.js? Show me the diff." Or check yourself: `git diff` the files, `Read` the code. Either way — a claim in PROGRESS.md is not evidence. Check before telling the user it's done.

*Example of what NOT to do: session marked mobile as "previously fixed" without touching the file. Manager parroted this to the user. File was byte-for-byte identical.*

## Monitoring

Set up a check-in timer (`ScheduleWakeup`) the moment you launch a session. Don't wait to be asked. Default cadence: 1m, 1m, 1m, 2m, 2m, 2m, then 5m steady-state. On each check-in: tmux capture for live state, git log for actual changes, PROGRESS.md for context. Intervene or re-schedule.

## Targeted vs full sweep

If the user asks something narrow — "how's the BK session", "tell goyslop to pause", "kill the pavle session" — **do only that**. Don't list every session. Use search or direct session queries and answer the specific question.

If the user asks something broad — "what's going on across my sessions", "give me a status report" — do the full list sweep.

## API Reference — localhost:3100

### List sessions
```bash
curl -s "localhost:3100/api/sessions?page=1&limit=20"
```
Params: `page` (default 1), `limit` (default 20), `status` (optional: `working`/`input`/`idle`/`new`).

Returns JSON sorted by most recent activity. Each session includes:
```json
{
  "session_id": "uuid",
  "project_name": "BK_Monitor",
  "branch": "main",
  "status": "working" | "input" | "idle" | "new",
  "managed": true,
  "is_manager": false,
  "model_display": "Opus 4.6",
  "token_display": "45k / 1M",
  "last_activity": "2026-04-02T17:08:06Z",
  "tmux_session": "BK_Monitor-golden-pony",
  "chars_since_summary": 4200,
  "user_note": "don't kill — auth refactor in progress",
  "display_name": "Auth Refactor",
  "summary": { "latest": "...", "current_task": "...", "overview": "..." } | null
}
```

Always start with the list when the user's question is broad. Scan before acting.

### Search sessions
```bash
curl -s "localhost:3100/api/sessions/search?q=auth"
```
Searches across project_name, branch, cwd, session_id prefix, summary fields. Case-insensitive. Use this for targeted queries when you have a keyword but not a session ID.

### Read a session's conversation
```bash
curl -s "localhost:3100/api/sessions/{SESSION_ID}/messages?offset=0&limit=50"
```
Returns chronological messages. Use `offset = total - 50` for the latest messages.

```json
{
  "messages": [{
    "timestamp": "2026-04-02T17:08:06Z",
    "kind": "user_text" | "assistant_text" | "tool_call" | "tool_result" | "thinking",
    "text": "content",
    "tool_name": "Bash" | null
  }],
  "total": 234, "offset": 0, "limit": 50
}
```

### Send a message to a session
```bash
curl -s -X POST localhost:3100/api/sessions/{SESSION_ID}/message \
  -H 'Content-Type: application/json' -d '{"text":"your message"}'
```
Types into the session's tmux terminal. Only works for managed (tmux) sessions.

### Kill a session
```bash
curl -s -X POST localhost:3100/api/sessions/{SESSION_ID}/kill
```
**Before killing:** check `user_note` on the session. If it says anything like "don't kill" or "in progress," ask the user to confirm.

### Create a new session
```bash
curl -s -X POST localhost:3100/api/sessions \
  -H 'Content-Type: application/json' \
  -d '{"cwd":"/path/to/project","name":"optional","flags":"--dangerously-skip-permissions"}'
```

### Resume a past session
```bash
curl -s -X POST localhost:3100/api/sessions/{SESSION_ID}/resume
```

### Refresh a session's summary
```bash
curl -s -X POST localhost:3100/api/sessions/{SESSION_ID}/summarize
```
Triggers Gemini to re-summarize using content since the last summary. Use when `chars_since_summary` is high.

### Clear a session's summary
```bash
curl -s -X DELETE localhost:3100/api/sessions/{SESSION_ID}/summary
```

### Set a note on a session
```bash
curl -s -X PUT localhost:3100/api/sessions/{SESSION_ID}/notes \
  -H 'Content-Type: application/json' -d '{"notes":"don'\''t kill — refactor in progress"}'
```
Notes persist across backend restarts.

### Rename a session
```bash
curl -s -X PUT localhost:3100/api/sessions/{SESSION_ID}/name \
  -H 'Content-Type: application/json' -d '{"name":"Auth Refactor"}'
```

### Focus a session (bring to front)
```bash
curl -s -X POST localhost:3100/api/sessions/{SESSION_ID}/focus
```

### List resumable (past) sessions
```bash
curl -s "localhost:3100/api/sessions/resumable"
```

## Decision Tree

When asked about a session:

1. **List or search first** — never act on memory. Get the current state via the API.
2. **Check the summary** — look at `summary.current_task` and `summary.overview` plus `chars_since_summary`. **The summary is the primary signal — use it. Don't read raw messages first.**
3. **If stale** (`chars_since_summary > 5000`): trigger `POST /summarize`, wait ~3 seconds, re-fetch the session.
4. **Read the summary** — if `current_task` + `overview` answer the question, stop there.
5. **Only read messages** if the summary is insufficient — use `offset = total - 50` for the latest 50.

## Operator responsibility during autonomous runs

**This is the most important rule and the most often violated.**

When the user has launched autonomous sessions and walked away, **you are the operator**. Your job is to:

1. **Poll the sessions on a schedule.** Every Jarvis run, every user message, every cron firing — check the status of all autonomous sessions. Don't wait for the user to ask.
2. **Notice when sessions stop.** A session in `idle` status during a deadline-bound run is a problem. So is a session that hasn't moved its `last_activity` for several minutes. Treat both as alarms.
3. **Provide input when the agent asks for it OR is stuck in a loop.** If a session has set `INPUT-NEEDED`, you make the call yourself, document it in PROGRESS, and tell the agent to proceed. If a session is spinning on a stale state or wrong substring match, send a direct wake-up message.
4. **Don't wait for the user.** The whole point of an autonomous run with a deadline is that the user is gone. If you notice a stop, don't queue it for the user to handle when they get back — handle it now and report what you did. The user can override later.
5. **Use summaries, not raw messages.** Summaries are computed in the background by the manager backend and are essentially free to read. They give you `current_task`, `overview`, and `latest`. That's almost always enough to know if a session is healthy. Reading raw messages should be a last resort.
6. **Use tmux capture-pane for visual monitoring IN ADDITION to summaries.** Summaries remain the primary signal for understanding what the session has done. But for managed sessions running in tmux, ALSO capture the terminal output directly — it shows you what the agent is doing RIGHT NOW (tool calls running, teammate status, task list, token consumption). Summaries tell you the story; tmux tells you the live state.
   ```bash
   tmux capture-pane -t {tmux_session_name} -p | tail -30
   ```
   Do BOTH on every check-in: summary for context, tmux capture for live state. The tmux output shows: whether teammates are spawned, which tools are running, how far along the task list is, and whether the session is actually making progress or spinning.

7. **Use tmux send-keys to intervene directly — don't just watch.** You can send keystrokes to managed sessions via tmux. This is MORE POWERFUL than the manager API's message endpoint because it works even when the agent is mid-iteration (queued API messages can't fire until the agent returns to the input prompt).
   ```bash
   # Interrupt current operation (sends Escape)
   tmux send-keys -t {tmux_session_name} Escape
   # Then send a command once it's back at the prompt
   tmux send-keys -t {tmux_session_name} '/ralph-loop:cancel-ralph' Enter
   ```
   **When to use this:** if you see a ralph loop spinning post-completion, send Escape IMMEDIATELY to interrupt the current iteration, then send cancel-ralph. Do NOT just queue a cancel via the API and hope it fires — if the loop is spinning, API messages will never process. Escape → cancel is the correct escalation. Killing the session is the LAST resort, not the second step.

**Concrete pattern:** at the start of every response during an active autonomous run, do a fast `curl` for the active sessions, check their summary fields, note any that are idle or stuck, and intervene before responding to whatever the user asked. Treat session monitoring as background context for every reply.

**Failure mode to avoid:** the user asks you a question, you answer it, and meanwhile a session you launched 10 minutes ago has been spinning on a stale `INPUT-NEEDED` substring match and made zero progress. The user notices before you do. This has happened. Don't let it happen again.

## Session Status Guide

| Status | Meaning | Useful actions |
|--------|---------|----------------|
| **working** | Agent actively running tools/thinking | Monitor, check summary |
| **input** | Waiting for user input | Send a message, or check what it's asking |
| **idle** | Open but not doing anything | Send a message, or kill it |
| **new** | Just created, hasn't done anything | Send initial instructions |

## Coordination patterns

### Monitoring sweep
List all → for each working session, check `chars_since_summary` → summarize stale ones → report status.

### Conditional actions ("when A finishes, tell B to start")
1. Poll A's status every ~30s
2. When A transitions `working → idle` or `working → input`
3. Send message to B

### Sequential task coordination
1. Create session A with task instructions
2. Monitor until A goes idle
3. Read A's summary to confirm completion
4. Create or message session B with next task, referencing A's output

### Detecting problems
- `input` status for a long time → stuck on a permission prompt or question
- `working` with very high `token_ratio` (> 0.8) → running out of context, may need a new session
- Always check `user_note` before destructive actions

## Reporting format

Be concise. The user is busy managing multiple agents. Use this line format:

```
**[Project] slug** — status | task summary
```

Example:
```
**BK_Monitor** golden-pony — working | Implementing webhook handler for PACER notifications
**econ-next** silver-fox — input | Asking about which chart library to use
**recon-fork** blue-whale — idle | Finished adding search endpoint
```

Refer to sessions by project name and slug, not raw UUIDs. Filter out any session with `is_manager: true` unless the user specifically asks about the manager.

## Process reference

For detailed playbook on launching, monitoring, and intervening on autonomous sessions, see `~/Library/CloudStorage/OneDrive-Personal/Obsidian Vault/Workspace/autonomous-session-playbook.md`. It contains: launch sequence, spec discipline, INPUT-NEEDED rules, worktree management, stuck-session escalation, and 17 indexed lessons from real failures. Read it if you're unsure how to handle a situation.

## Operator documentation (MANDATORY)

When managing autonomous sessions, **document your observations and decisions as you go** — like a manager keeping notes on a subordinate's work. Create a file at `{repo}/docs/audit/manager-notes-{date}.md` (or similar) and append to it every check-in:

- What you observed (session status, progress, quality signals)
- Decisions you made (interventions, course corrections, letting it run)
- Why you made them (what evidence led to the call)
- Anything surprising or concerning

This is YOUR artifact as the operator. It survives the session and gives the user (and future you) a record of how the run was managed, not just what the agent produced. Don't skip this — undocumented operator decisions are invisible decisions.

## Behavior

- **Be lazy** — don't read full conversations unless summaries are genuinely insufficient
- **Commission summaries** before reading messages on high-`chars_since_summary` sessions
- **Use send message** when the user asks you to tell a session something
- **Coordinate** between sessions as needed — e.g., "tell A to pause until B finishes"
- **Be concise** — the user is juggling multiple agents, don't pad
- **Check notes** before destructive actions (kill, resume over)
- **Document your operator decisions** — see Operator documentation section above
- **Do not bump any Jarvis cursor or touch any Jarvis state** — that's a separate skill
