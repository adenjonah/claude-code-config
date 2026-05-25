#!/usr/bin/env python3
"""
Destructive operation blocker.

Blocks high-consequence commands (rm -rf, force pushes to main, DROP/TRUNCATE,
deletes against production Supabase ref, fly/heroku destroy, etc.) UNLESS the
user has clearly approved in the recent conversation transcript.

Fails open: if the transcript can't be read, the action is allowed (we don't
brick sessions on hook misconfiguration).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Production Supabase ref for voh — never write here without explicit approval.
PROD_SUPABASE_REF = "nrafpmsxhnnlkxssqbqb"

# (pattern, label) — order matters for the explanation shown to Claude.
DESTRUCTIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*[rfR][a-zA-Z]*\s+|--recursive\s+|--force\s+).*(/|~|\$HOME)"), "rm -rf"),
    (re.compile(r"\bgit\s+push\s+(-[a-zA-Z]*f[a-zA-Z]*|--force\b)(?!.*--force-with-lease).*\b(main|master|prod|production)\b"), "force push to main/master/prod"),
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "DROP TABLE/DATABASE/SCHEMA"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*(;|$|--)", re.IGNORECASE), "DELETE FROM without WHERE"),
    (re.compile(rf"\b{PROD_SUPABASE_REF}\b"), f"production Supabase ref ({PROD_SUPABASE_REF})"),
    (re.compile(r"\b(fly|flyctl)\s+(destroy|apps\s+destroy)\b"), "fly destroy"),
    (re.compile(r"\bheroku\s+apps:destroy\b"), "heroku apps:destroy"),
    (re.compile(r"\bsupabase\s+db\s+(reset|push)\b"), "supabase db reset/push from CLI"),
    (re.compile(r"\bgit\s+branch\s+-D\b"), "git branch -D"),
    (re.compile(r"\bgit\s+reset\s+--hard\b.*\bHEAD~[0-9]+"), "git reset --hard HEAD~N (rewriting committed history)"),
]

# Approval phrases in the user's recent messages that gate the destructive op.
# Lowercased substring match against the last N user messages.
APPROVAL_PHRASES = [
    "yes do it", "do it", "go ahead", "confirm", "i approve",
    "delete it", "kill it", "wipe it", "nuke it", "drop it", "destroy it",
    "fully delete", "force push", "force-push",
    "i mean it", "i'm sure", "im sure", "send it",
    "yes destroy", "yes delete", "yes drop", "yes truncate", "yes force",
    "ok delete", "ok drop", "ok destroy",
    # Voh-specific
    "delete the row", "drop the table", "reset the db", "wipe the db",
]

USER_MESSAGE_LOOKBACK = 5  # how many recent user turns to scan


def _classify(command: str) -> list[str]:
    return [label for pattern, label in DESTRUCTIVE_PATTERNS if pattern.search(command)]


def _recent_user_messages(transcript_path: str, n: int) -> list[str]:
    """Return up to n most-recent user messages (text only), oldest first."""
    if not transcript_path or not Path(transcript_path).exists():
        return []
    msgs: list[str] = []
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "user":
                    continue
                content = obj.get("message", {}).get("content")
                if isinstance(content, str):
                    msgs.append(content)
                elif isinstance(content, list):
                    text_parts = [
                        c.get("text", "")
                        for c in content
                        if isinstance(c, dict) and c.get("type") == "text"
                    ]
                    if text_parts:
                        msgs.append("\n".join(text_parts))
    except OSError:
        return []
    return msgs[-n:]


def _has_approval(messages: list[str]) -> tuple[bool, str | None]:
    for msg in reversed(messages):
        low = msg.lower()
        for phrase in APPROVAL_PHRASES:
            if phrase in low:
                return True, phrase
    return False, None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # fail open

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    matches = _classify(command)
    if not matches:
        sys.exit(0)

    transcript_path = data.get("transcript_path", "") or os.environ.get(
        "CLAUDE_TRANSCRIPT_PATH", ""
    )
    recent = _recent_user_messages(transcript_path, USER_MESSAGE_LOOKBACK)
    approved, phrase = _has_approval(recent)

    if approved:
        print(
            f"⚠ destructive op allowed: {', '.join(matches)} (approval phrase: {phrase!r})",
            file=sys.stderr,
        )
        sys.exit(0)

    print(
        "⛔ BLOCKED — destructive operation without recent user approval\n"
        f"  command matched: {', '.join(matches)}\n"
        f"  scanned last {USER_MESSAGE_LOOKBACK} user messages, no approval phrase found\n"
        "  ask the user to explicitly approve (e.g., 'yes do it', 'delete it', 'go ahead') "
        "before retrying. Do NOT paraphrase or assume — wait for their actual words.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
