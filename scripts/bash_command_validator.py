#!/usr/bin/env python3
"""
Claude Code Hook: Bash Command Validator
=========================================
PreToolUse hook for the Bash tool. Validates commands against safety
and best-practice rules before execution.

Two rule tiers:
  - "warn"  → print to stderr, exit 0 (Claude sees the warning but proceeds).
  - "block" → print to stderr, exit 2 (tool call is blocked).

The destructive_blocker.py hook handles approval-gated `rm -rf` separately,
so this validator only hard-blocks catastrophic patterns (rm -rf /, ~, .., etc.).
"""

import json
import re
import sys

# (level, regex, message). level ∈ {"warn", "block"}.
_VALIDATION_RULES = [
    # --- Best practices (advisory) ---
    (
        "warn",
        r"^grep\b(?!.*\|)",
        "Use 'rg' (ripgrep) instead of 'grep' for better performance and features",
    ),
    (
        "warn",
        r"^find\s+\S+\s+-name\b",
        "Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance",
    ),
    # --- Risky operations (advisory — pair with destructive_blocker for approval gate) ---
    (
        "warn",
        r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|--force\s+).*(/|~|\$HOME|\.\.|\.git)",
        "WARNING: rm -rf targeting a path with /, ~, .., or .git. Double-check the target.",
    ),
    (
        "warn",
        r"\bgit\s+reset\s+--hard\b",
        "WARNING: git reset --hard discards all uncommitted changes. Consider git stash first.",
    ),
    (
        "warn",
        r"\bgit\s+push\s+.*--force(?!-with-lease)\b|\bgit\s+push\s+-f\b",
        "WARNING: Force push will overwrite remote history. Use --force-with-lease for safety.",
    ),
    (
        "warn",
        r"\bgit\s+clean\s+(-[a-zA-Z]*f|--force)",
        "WARNING: git clean -f permanently deletes untracked files. Consider git clean -n (dry run) first.",
    ),
    (
        "warn",
        r"\bgit\s+checkout\s+\.\s*$",
        "WARNING: git checkout . discards all unstaged changes. Consider git stash first.",
    ),
    (
        "warn",
        r"\bgit\s+branch\s+(-[a-zA-Z]*D|--delete\s+--force)",
        "WARNING: git branch -D force-deletes a branch even if not merged.",
    ),
    # --- Catastrophic (hard block, no override) ---
    (
        "block",
        r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?[a-zA-Z]*\s+(/|~|\$HOME)(\s|$|/\*?\s*$)",
        "BLOCKED: rm -rf targeting filesystem root or $HOME. Refusing.",
    ),
    (
        "block",
        r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?[a-zA-Z]*\s+\.\.?(\s|$)",
        "BLOCKED: rm -rf on '.' or '..'. Too easy to misfire — name the path explicitly.",
    ),
]


def _validate_command(command: str) -> tuple[list[str], bool]:
    """Return (messages, should_block)."""
    messages = []
    should_block = False
    for level, pattern, message in _VALIDATION_RULES:
        if re.search(pattern, command):
            messages.append(message)
            if level == "block":
                should_block = True
    return messages, should_block


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    messages, should_block = _validate_command(command)
    if messages:
        for message in messages:
            print(f"• {message}", file=sys.stderr)
        if should_block:
            # Exit 2 blocks the tool call and shows stderr to Claude.
            sys.exit(2)
    # Warnings still print, but Claude proceeds.
    sys.exit(0)


if __name__ == "__main__":
    main()
