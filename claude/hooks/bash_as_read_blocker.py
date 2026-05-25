#!/usr/bin/env python3
"""
Bash-as-Read blocker.

Blocks `Bash(cat <file>)`, `Bash(head <file>)`, `Bash(tail <file>)`,
`Bash(less <file>)`, `Bash(more <file>)` against workspace files. Forces use
of the dedicated Read tool, which is cheaper to render and tracked by the
harness.

Allows reads against system paths (/etc, /var/log, /proc, /sys, /tmp) and
piped commands (which usually mean "extract from output", not "view file").
"""

from __future__ import annotations

import json
import re
import sys

# A single read-style command followed by a file path. Must be the only
# command on the line — piped or redirected commands are allowed (they're
# usually pulling data into another tool).
READ_STYLE = re.compile(
    r"^\s*(cat|head|tail|less|more|bat)\s+(?:-[a-zA-Z0-9]+\s+)*([^\s|;&><]+)\s*$"
)

SYSTEM_PATH_PREFIXES = (
    "/etc/",
    "/var/log/",
    "/var/run/",
    "/proc/",
    "/sys/",
    "/tmp/",
    "/private/tmp/",
    "/dev/",
    "/usr/share/",
    "/Library/Logs/",
    "$HOME/Library/Logs/",
    "$HOME/Library/Caches/",
)


def _is_workspace_file(path: str) -> bool:
    """Return True if the path is a file we'd rather read with the Read tool."""
    if path.startswith(SYSTEM_PATH_PREFIXES):
        return False
    # Allow stdin redirects like `cat - | jq`
    if path in ("-", "/dev/stdin", "/dev/stdout"):
        return False
    # Heredoc-y stuff
    if path.startswith("<<") or path.startswith("/dev/fd/"):
        return False
    return True


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = (data.get("tool_input", {}).get("command") or "").strip()
    if not command:
        sys.exit(0)

    # If there's a pipe, redirect, or semicolon, the read is part of a chain
    # — usually legitimate (e.g., `cat file | jq .key`).
    if any(ch in command for ch in ("|", ">", "<", ";", "&&", "||")):
        sys.exit(0)

    match = READ_STYLE.match(command)
    if not match:
        sys.exit(0)

    tool_name = match.group(1)
    path = match.group(2)
    if not _is_workspace_file(path):
        sys.exit(0)

    print(
        f"⛔ BLOCKED — `{tool_name} {path}` should use the Read tool\n"
        "  Read is faster, tracked by the harness (so the file shows up in "
        "session context), and avoids re-rendering the same content in the "
        "shell output later.\n"
        "  if you need to pipe into another command (jq, grep, etc.), include "
        "the pipe — that case is allowed.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
