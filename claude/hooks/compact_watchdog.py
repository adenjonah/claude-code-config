#!/usr/bin/env python3
"""
PreToolUse hook: block non-essential tool calls when context is near full.

Triggers when:
  - context window remaining < 15%, AND
  - session has > 150 user/assistant messages, AND
  - the tool being called is NOT in the essential allowlist (Read, Grep, Glob,
    TodoWrite, AskUserQuestion — things you'd still need to be able to do
    while investigating "should I compact?")

When triggered: blocks the tool call with a clear message telling Claude to
`/compact` first or start a new session.

The context-remaining value comes from the hook input payload's
`context_window` field (Claude Code passes this for PreToolUse hooks).
Falls back to message-count heuristic if the field is missing.

Fails open: any error path allows the tool call.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REMAINING_PCT_THRESHOLD = 15
MIN_MESSAGE_COUNT = 150
ESSENTIAL_TOOLS = {
    "Read",
    "Grep",
    "Glob",
    "TodoWrite",
    "AskUserQuestion",
    "TaskUpdate",
    "TaskList",
    "TaskGet",
    "TaskStop",
}


def _read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _count_messages(transcript_path: str) -> int:
    if not transcript_path or not Path(transcript_path).exists():
        return 0
    n = 0
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("type") in ("user", "assistant"):
                    n += 1
    except OSError:
        return n
    return n


def main() -> None:
    data = _read_input()
    tool = data.get("tool_name", "")
    if tool in ESSENTIAL_TOOLS:
        sys.exit(0)

    # Try to read context-window remaining from the hook payload first.
    ctx = data.get("context_window") or {}
    remaining = ctx.get("remaining_percentage")
    if remaining is None:
        # Fallback: harmless skip — without ctx info we can't make a call.
        sys.exit(0)
    try:
        remaining_pct = float(remaining)
    except (TypeError, ValueError):
        sys.exit(0)
    if remaining_pct >= REMAINING_PCT_THRESHOLD:
        sys.exit(0)

    transcript = data.get("transcript_path", "") or os.environ.get(
        "CLAUDE_TRANSCRIPT_PATH", ""
    )
    msgs = _count_messages(transcript)
    if msgs < MIN_MESSAGE_COUNT:
        sys.exit(0)

    print(
        "⛔ BLOCKED — context budget exhausted\n"
        f"  context remaining: {remaining_pct:.1f}% (threshold {REMAINING_PCT_THRESHOLD}%)\n"
        f"  session messages: {msgs} (threshold {MIN_MESSAGE_COUNT})\n"
        "  do NOT spend the last sliver on more tool calls — context will roll "
        "and output quality drops. Run `/compact` to summarize and free space, "
        "OR if you're at a natural breakpoint, tell the user to start a new "
        "session.\n"
        "  Read / Grep / Glob / TodoWrite / AskUserQuestion still pass through "
        "so you can investigate before deciding.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
