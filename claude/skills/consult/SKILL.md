---
name: consult
description: Use when the user wants to ask another running Claude Code session a question — pull context, facts, or decisions without re-reading source material. Triggers on "consult", "ask the X session", "check if any session knows about".
---

# Consult

**Find the session the user asked for. Send it the question. Bring back the answer.**

Do NOT pre-screen whether the session has the knowledge. Do NOT read its messages or summary to decide "this session probably doesn't know about that." Summaries help you identify WHICH session the user means — they do NOT tell you whether to ask. Even if the summary says nothing about the topic, ask anyway. The session's full context is far richer than its summary.

## Ensure backend is running

```bash
ensure_recon() {
  curl -sf localhost:3100/api/sessions > /dev/null 2>&1 && return 0
  local RECON=""
  for c in "$HOME/dev/claude-manager/server/target/release/recon" \
           "$HOME/dev/claude-manager/bin/recon"; do
    [ -x "$c" ] && RECON="$c" && break
  done
  [ -z "$RECON" ] && echo "ERR: recon not found. Build: cd ~/dev/claude-manager && cargo build --release --manifest-path server/Cargo.toml" >&2 && return 1
  mkdir -p "$HOME/.manager-skill"
  nohup "$RECON" serve --quiet --manager-dir "$HOME/dev/claude-manager/server/manager" >> "$HOME/.manager-skill/recon.log" 2>&1 & disown $! 2>/dev/null
  for i in $(seq 12); do curl -sf localhost:3100/api/sessions > /dev/null 2>&1 && return 0; sleep 0.5; done
  echo "ERR: recon didn't start. Check ~/.manager-skill/recon.log" >&2 && return 1
}
ensure_recon || exit 1
```

## Step 1: Find the session

Search `GET /api/sessions/search?q={description}`. Fall back to `GET /api/sessions` and scan `display_name`, `project_name`, `summary.current_task`, `cwd`.

- **Clear match** → proceed. Don't over-confirm.
- **Ambiguous** → show candidates, ask user.
- **No match** → list what's running, let user pick.

**Wrong session is never acceptable.** But obvious matches don't need confirmation.

## Step 2: Ask it

Send via `POST /api/sessions/{FULL_SESSION_ID}/message`:

```
[CONSULT from {your_session_id} ({your_project_name}) depth=0 correlation={uuid}]

{question}
```

Only `managed: true` sessions can receive messages (they run in tmux). If most sessions are unmanaged, suggest the user add a shell wrapper to always start claude in tmux:
```bash
# in ~/.zshrc or ~/.bashrc
claude() {
  local name=$(basename "$PWD" | tr ' .' '-')
  tmux new-session -s "$name-$$" "command claude --allow-dangerously-skip-permissions $*"
}
```
This makes all future sessions managed and consultable.
- **Managed** → message it directly.
- **Unmanaged but running** → read its conversation via the messages API. Tell the user you're extracting from its history since it's not in tmux.
- **Not running** → resume it via the **manager skill** (comes back managed), then message it.

Refuse depth > 1 (no consult chains). Detect self-consults.

## Step 3: Wait for the response

**Sending a message to a session WAKES IT UP.** Even idle sessions will process the message and respond. Do NOT give up after one poll — keep checking. The session needs time to think and generate its answer.

Poll `GET /api/sessions/{ID}/messages` for new `assistant_text` after your consult message. Also use `tmux capture-pane -t {tmux_session} -p | tail -30` to see if the session is actively working on your question. **REQUIRED:** Read the **manager skill** for details on how session messaging, tmux monitoring, and status detection work.

- **Session is working on it** (visible in tmux or status changes to `working`) → keep polling every 5-10s until it responds
- **Responds but answer is vague or incomplete** → send a follow-up message asking for specifics. Same correlation ID. You're having a conversation, not doing a single query.
- **Responds with a good answer** → relay answer with provenance: `**From [Name]** (live response)`
- **No response after 60s+ AND tmux shows it's not working** → then tell user, offer alternatives
- **Says it doesn't know** → tell user, search for other sessions that might, suggest them

## Edge cases

- **User doesn't name a session** → search all, confirm candidate before asking
- **Session is closed** → check `/api/sessions/resumable`, offer to read its history
- **Follow-up questions** → same session, same correlation ID
- **You RECEIVE a consult** → answer from your context, be specific, then resume your work
- **User wants to direct, not ask** → that's `/manager`, not `/consult`

## API quick reference

| Endpoint | Use |
|----------|-----|
| `GET /api/sessions/search?q=X` | Find session by description |
| `GET /api/sessions?limit=20` | List all with summaries |
| `POST /api/sessions/{ID}/message` | Send consult (managed only, needs full UUID) |
| `GET /api/sessions/{ID}/messages?offset=N&limit=50` | Poll for response |
| `POST /api/sessions/{ID}/summarize` + `{"query":"..."}` | Last-resort extraction (session truly unreachable) |
| `PUT /api/sessions/{ID}/name` + `{"name":"..."}` | Set alias for repeat lookups |
