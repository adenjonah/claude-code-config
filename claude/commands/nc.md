# New Claude - Open a new iTerm2 window with Claude Code

Arguments: $ARGUMENTS

## Instructions

Parse the arguments and open a new iTerm2 window running Claude Code.

### Argument parsing

- **Empty / no arguments**: Target directory is `~/dev/`. No context.
- **"pwd"**: Target directory is the current working directory (`$CWD`). Gather context first.
- **Anything else**: Treat as a repo name. Find the best match under `~/dev/`.

### Steps

1. **Determine target directory:**
   - If empty: use `~/dev/`
   - If "pwd": use the current working directory
   - If repo name: run `find ~/dev -maxdepth 2 -type d -name "*<name>*" | head -1` to find the closest match. If no match, try case-insensitive. If still no match, tell the user and stop.

2. **Gather context (only for "pwd" mode):**
   - Run `git log --oneline -3` and `git diff --stat` in the current directory
   - Summarize into a brief one-line context snippet (e.g. "Working on auth flow - recent changes to login.tsx and api/auth.ts")

3. **Open iTerm2 window:**
   - Use the osascript command below to open a new iTerm2 window
   - If context was gathered, start claude with it: `claude "Continuing work in this repo: <context>"`
   - Otherwise just start `claude` with no arguments

### osascript template

```bash
osascript <<'APPLESCRIPT'
tell application "iTerm"
    activate
    create window with default profile
    tell current session of current window
        write text "cd <TARGET_DIR> && <CLAUDE_COMMAND>"
    end tell
end tell
APPLESCRIPT
```

Replace `<TARGET_DIR>` with the resolved absolute path and `<CLAUDE_COMMAND>` with either `claude` or `claude "Continuing work: <context>"`.

**Important:** Escape any double quotes in the context snippet before embedding in the command. Keep the context snippet under 200 characters.
