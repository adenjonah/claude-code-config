# New Claude - Open a new iTerm2 window with Claude Code (Remote Control by default)

Arguments: $ARGUMENTS

## Instructions

Parse the arguments and open one or more new iTerm2 windows running Claude Code. **Every spawned session starts with Remote Control enabled** so it can be driven from the Claude phone/web app — including when this command is invoked FROM an existing remote-controlled session.

### Argument parsing

Arguments are space-separated tokens. Any token that is a positive integer is treated as the **count** of terminals to spawn. Any other token is treated as the **target** (`pwd` or a repo name). The literal token `--local` disables remote control for the spawned session(s).

- **Count**: positive integer. Defaults to `1` if not provided. Cap at `10` for safety — if the user passes a higher number, ask before proceeding.
- **Target**:
  - **Empty / no target**: Target directory is the current working directory (`$CWD`). Gather context first.
  - **"pwd"**: Same as empty — current working directory with context. Kept as an explicit alias.
  - **"dev"**: Target directory is `~/dev/`. No context.
  - **Anything else** (non-numeric, not `--local`): Treat as a repo name. Find the best match under `~/dev/`.
- **`--local` flag** (optional): suppresses `--remote-control` on the spawned session. Use only when explicitly requested — remote control is the default.

Examples:
- `/nc` → 1 remote-controlled window in current directory with context
- `/nc 3` → 3 remote-controlled windows in current directory
- `/nc dev` → 1 remote-controlled window in `~/dev/`
- `/nc 2 dev` → 2 remote-controlled windows in `~/dev/`
- `/nc pwd` → same as `/nc`
- `/nc clubgg 4` → 4 remote-controlled windows in the resolved ClubGG repo
- `/nc --local` → 1 window in current directory, no remote control (escape hatch)

### Steps

1. **Determine count:** parse args; the first numeric token is the count. Default `1`.

2. **Determine remote-control mode:** ON by default. If any arg is `--local`, set to OFF and drop the token from further parsing.

3. **Determine target directory:**
   - If no non-numeric token (after removing `--local`), or token is "pwd": use the current working directory (gather context)
   - If "dev": use `~/dev/` (no context)
   - If repo name: run `find ~/dev -maxdepth 2 -type d -name "*<name>*" | head -1` to find the closest match. If no match, try case-insensitive. If still no match, tell the user and stop.

4. **Gather context (only for current-directory mode — empty/pwd):**
   - Run `git log --oneline -3` and `git diff --stat` in the current directory
   - Summarize into a brief one-line context snippet (e.g. "Working on auth flow - recent changes to login.tsx and api/auth.ts")

5. **Build the claude command:**
   - **Base:** `claude` plus, if remote-control is ON, the flags:
     `--remote-control --remote-control-session-name-prefix <PREFIX>`
     where `<PREFIX>` is the basename of the resolved target directory (e.g. `voices-of-history`, `dev`, `apartment-planner`). This makes the new session identifiable in the remote control session list rather than just showing the machine hostname.
   - **Display name:** also pass `--name <PREFIX>` so the iTerm2 window title and Claude prompt box show the repo, not just `claude`.
   - **Optional prompt:** if context was gathered, append the prompt as the last positional argument: `"Continuing work in this repo: <context>"`. Escape any double quotes in the context first, cap at 200 chars.

6. **Open N iTerm2 windows:** loop `count` times, invoking the osascript template below for each.

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

Replace:
- `<TARGET_DIR>` — resolved absolute path to the target directory
- `<CLAUDE_COMMAND>` — the assembled claude invocation from step 5

**Example final commands:**
- Remote-control + repo + no context:
  `claude --remote-control --remote-control-session-name-prefix voices-of-history --name voices-of-history`
- Remote-control + current dir + context:
  `claude --remote-control --remote-control-session-name-prefix voh --name voh "Continuing work: hooks landed, deploying to staging"`
- Local-only escape:
  `claude --name apartment-planner`

**Important:** Escape any double quotes in the context snippet before embedding in the command. Keep the context snippet under 200 characters.

### Why remote-control by default

The user runs this command from existing remote-controlled sessions (e.g. when driving from the Claude phone app). A spawned session without `--remote-control` is invisible from the phone — defeating the point. Default-on lets the user keep fanning out sessions across machines/contexts without needing to remember the flag. `--local` is the escape hatch for the rare case where you genuinely want a Mac-only session.
