#!/usr/bin/env python3
"""
Stop hook: hard-enforce bookkeeper invocation at session end.

Two failure modes this hook intercepts:

  (A) Claude finishes a non-trivial session without invoking bookkeeper.
  (B) Claude *asks* the user "want me to invoke the bookkeeper?" instead
      of just invoking it (user has explicitly told us never to ask).

Behavior:
  - Hard block via {"decision": "block", "reason": ...} so the turn cannot
    end. Claude re-enters the loop with stern instructions to invoke the
    bookkeeper silently — no questions, no announcements.
  - Caps blocks at MAX_BLOCKS per session so we can't infinite-loop if the
    model refuses to comply for some reason.
  - Logs to ~/.claude/logs/bookkeeper-enforcer.log for audit.

Hard threshold for case (A):
  - >= MIN_MESSAGES user/assistant messages, AND
  - >= MIN_EDITS Edit/Write/NotebookEdit tool calls

Case (B) (the ask) fires regardless of session size.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

MIN_MESSAGES = 10
MIN_EDITS = 1
MAX_BLOCKS = 3
BLOCK_DIR = Path.home() / ".claude" / "bookkeeper-block-counts"
LOG_PATH = Path.home() / ".claude" / "logs" / "bookkeeper-enforcer.log"

ASK_PATTERNS = [
    r"want me to.{0,80}bookkeeper",
    r"bookkeeper.{0,80}\?",
    r"should i.{0,80}bookkeeper",
    r"shall i.{0,80}bookkeeper",
    r"would you like.{0,80}bookkeeper",
    r"do you want.{0,80}bookkeeper",
    r"let me know.{0,80}bookkeeper",
    r"invoke the bookkeeper",
    r"call the bookkeeper",
    r"run the bookkeeper",
]
ASK_RE = re.compile("|".join(ASK_PATTERNS), re.IGNORECASE | re.DOTALL)


def _read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _scan_transcript(path: str) -> tuple[int, int, bool, str]:
    """Return (msg_count, edit_count, bookkeeper_invoked, last_assistant_text)."""
    if not path or not Path(path).exists():
        return (0, 0, False, "")
    msgs = 0
    edits = 0
    bk = False
    last_text = ""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = d.get("type")
                if t in ("user", "assistant"):
                    msgs += 1
                msg = d.get("message") or {}
                content = msg.get("content")
                if isinstance(content, list):
                    if t == "assistant":
                        parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                parts.append(block.get("text", ""))
                        if parts:
                            last_text = "\n".join(parts)
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") != "tool_use":
                            continue
                        name = block.get("name", "")
                        if name in ("Edit", "Write", "NotebookEdit"):
                            edits += 1
                        elif name in ("Agent", "Task"):
                            inp = block.get("input", {}) or {}
                            sub = inp.get("subagent_type", "")
                            if sub == "bookkeeper":
                                bk = True
    except OSError:
        return (msgs, edits, bk, last_text)
    return (msgs, edits, bk, last_text)


def _log(session_id: str, action: str, **fields: object) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    extras = " ".join(f"{k}={v}" for k, v in fields.items())
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(
            f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
            f"session={session_id or 'unknown'} action={action} {extras}\n"
        )


def _bump_block_count(session_id: str) -> int:
    BLOCK_DIR.mkdir(parents=True, exist_ok=True)
    f = BLOCK_DIR / (session_id or "unknown")
    n = 0
    if f.exists():
        try:
            n = int(f.read_text().strip() or "0")
        except (OSError, ValueError):
            n = 0
    n += 1
    try:
        f.write_text(str(n))
    except OSError:
        pass
    cutoff = time.time() - 7 * 86400
    for p in BLOCK_DIR.iterdir():
        try:
            if p.is_file() and p.stat().st_mtime < cutoff:
                p.unlink()
        except OSError:
            pass
    return n


def _block(reason: str) -> None:
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def main() -> None:
    data = _read_input()
    transcript = data.get("transcript_path", "") or os.environ.get(
        "CLAUDE_TRANSCRIPT_PATH", ""
    )
    session_id = data.get("session_id", "")

    msgs, edits, bk, last_text = _scan_transcript(transcript)

    if bk:
        _log(session_id, "ok-invoked", msgs=msgs, edits=edits)
        sys.exit(0)

    asking = bool(last_text and ASK_RE.search(last_text))
    threshold_met = msgs >= MIN_MESSAGES and edits >= MIN_EDITS

    if not asking and not threshold_met:
        sys.exit(0)

    block_n = _bump_block_count(session_id)
    if block_n > MAX_BLOCKS:
        _log(session_id, "give-up", msgs=msgs, edits=edits, blocks=block_n)
        print(
            "SYSTEM [bookkeeper]: max enforcement blocks reached this session. "
            "Bookkeeper was not invoked. This will be audited.",
            file=sys.stderr,
        )
        sys.exit(0)

    if asking:
        _log(session_id, "block-ask", msgs=msgs, edits=edits, blocks=block_n)
        reason = (
            "HARD STOP — you just asked the user about invoking the bookkeeper. "
            "The user has explicitly forbidden this. Per ~/CLAUDE.md and "
            "~/.claude/projects/-Users-jonah/memory/feedback_bookkeeper_auto.md, "
            "the bookkeeper is MANDATORY at session end and you must invoke it "
            "SILENTLY — no announcements, no confirmation, no 'want me to'. "
            "Right now, with no further user-facing prose, call:\n"
            "    Agent(subagent_type='bookkeeper', description='Log session', "
            "prompt='<full session summary: what was done, decisions, files, follow-ups>')\n"
            "Do not reply to the user first. Do not ask. Invoke the tool now."
        )
    else:
        _log(session_id, "block-missing", msgs=msgs, edits=edits, blocks=block_n)
        reason = (
            f"HARD STOP — this session has {msgs} messages and {edits} file edits "
            "but bookkeeper has not been invoked. Per ~/CLAUDE.md this is mandatory. "
            "Invoke it NOW, silently, without asking the user. Call:\n"
            "    Agent(subagent_type='bookkeeper', description='Log session', "
            "prompt='<full session summary: what was done, decisions, files, follow-ups>')\n"
            "Do not announce. Do not ask. Just invoke the tool."
        )

    _block(reason)


if __name__ == "__main__":
    main()
