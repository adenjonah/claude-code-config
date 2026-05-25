#!/usr/bin/env python3
"""
Trivial subagent blocker.

Blocks `Agent` (and `Task`) tool calls where the prompt is too short or matches
patterns that don't justify spawning a fresh agent. Suggests the direct tool
(Read/Grep/Glob) instead.
"""

from __future__ import annotations

import json
import re
import sys

MIN_PROMPT_LEN = 200

TRIVIAL_PROMPT_PATTERNS = [
    re.compile(r"^\s*memory\s*retrieval", re.IGNORECASE),
    re.compile(r"^\s*load\s+project\s+memory", re.IGNORECASE),
    re.compile(r"^\s*quick\s+check", re.IGNORECASE),
    re.compile(r"^\s*just\s+check", re.IGNORECASE),
    re.compile(r"^\s*what\s+is\s+\S+\??\s*$", re.IGNORECASE),
    re.compile(r"^\s*where\s+is\s+\S+\??\s*$", re.IGNORECASE),
    re.compile(r"^\s*find\s+\S+\??\s*$", re.IGNORECASE),
    re.compile(r"^\s*read\s+\S+\??\s*$", re.IGNORECASE),
    re.compile(r"^\s*list\s+\S+\??\s*$", re.IGNORECASE),
]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool = data.get("tool_name", "")
    if tool not in ("Agent", "Task"):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    prompt = (tool_input.get("prompt") or "").strip()
    if not prompt:
        sys.exit(0)

    # Memory-retrieval is mandated by ~/CLAUDE.md before dev work. Allow the
    # ones with the canonical subagent_type even if the prompt is short.
    if tool == "Agent" and tool_input.get("subagent_type") in (
        "memory-retrieval",
        "bookkeeper",
        "codebase-research",
        "industry-standards",
    ):
        sys.exit(0)

    issues: list[str] = []
    if len(prompt) < MIN_PROMPT_LEN:
        issues.append(f"prompt is only {len(prompt)} chars (min {MIN_PROMPT_LEN})")
    for pat in TRIVIAL_PROMPT_PATTERNS:
        if pat.search(prompt):
            issues.append(f"matches trivial pattern: /{pat.pattern}/i")
            break

    if not issues:
        sys.exit(0)

    print(
        "⛔ BLOCKED — subagent overkill for this task\n"
        f"  {chr(10).join('  • ' + s for s in issues)}\n"
        "  use Read / Grep / Glob directly instead. Subagents are for "
        "open-ended research, parallel work, or context-protection — "
        "not for a single file lookup or a quick grep.\n"
        "  if you truly need an agent, expand the prompt to explain the "
        f"task, context, and expected output (>= {MIN_PROMPT_LEN} chars).",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
