# Jarvis — Design Spec

A "Jarvis I'm home" command. Single invocation that orients Claude on what's been happening across the user's recent work — Claude Code sessions, vault changes, river tasks, repo commits — and proposes high-leverage next moves. Domain-agnostic: the user may use Claude Code for code, writing, research, planning, anything. Jarvis makes no assumptions about what kind of work it is.

## Architecture

Jarvis is a Claude Code **skill**, not a script. The skill file is loaded into the current Claude Code session when invoked. The "synthesis" is what the current session does after gathering context — there is no separate process, no orchestrator, no API call. The session you're in IS the LLM call.

Jarvis is **100% standalone**. It does NOT depend on claude-manager or any other long-running process. Every invocation gathers its own data from disk.

**Skill location:** `~/.claude/skills/jarvis/SKILL.md`
**Invocation:** `/jarvis` (or instructed to use the `jarvis` skill)

## Inputs (Data Sources)

The skill instructs the current Claude session to gather four streams of context, in any order, in parallel where possible.

### 1. Recent Claude Code sessions

Read session metadata from `~/.claude/sessions/*.json`. Each file has `pid`, `sessionId`, `cwd`, `startedAt`, `name`. For each relevant session, find its JSONL at `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl` and either read it or summarize it.

**Default range:** sessions with activity since `~/.jarvis/cursor`, capped at 10 to prevent runaway.
**First run / no cursor:** last 24h or 5 most recent, whichever is smaller.
**Always include:** sessions currently running (PID liveness check via `kill -0`).

**Summarization strategy:** the session running Jarvis decides at runtime — read JSONLs directly via `tail`, dispatch parallel subagents, or shell out to Gemini Flash Lite via Bash (cheap, ~$0.03/session). No persistent cache in v1.

### 2. Vault recent activity

Cumulative diff since cursor across the entire vault. **Do NOT restrict by directory.** The vault is the user's full workspace and content can live anywhere in it.

```bash
git -C "$VAULT" diff "$(stat -f %Sm -t %Y-%m-%dT%H:%M:%S ~/.jarvis/cursor)..HEAD" \
  -- '*.md' ':(exclude).obsidian' ':(exclude)*.DS_Store'
```

Read the actual diff content for `.md` files (not just file lists). The 30-min auto-commit hook means individual commits are tiny and meaningless — the cumulative diff since cursor is the right unit.

### 3. River state

Personal and CC tasks live in river. SQLite at `~/.river/river.db`. Read directly or via the river MCP if available. Captures current task landscape with energy/commitment scores.

### 4. Recent commits in relevant repos

The set of relevant repos is **discovered automatically from the union of session cwds** — anywhere recently used in Claude Code. No manual config.

```bash
cat ~/.claude/sessions/*.json \
  | jq -r '.cwd' \
  | sort -u \
  | while read cwd; do
      repo=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) && \
        echo "$repo"
    done \
  | sort -u
```

For each repo, run `git log --since=<cursor>` and `git diff --stat <last>..HEAD`. Filter auto-commit noise where present.

## Behavior

The skill instructs the executing session as follows:

> The commands above give you the summary view. **Use your judgment to dig deeper** when the situation calls for it. If a diff hints at something the summary doesn't fully capture, read the full file. If a session looks important or in the middle of something, read its full JSONL. Dispatch subagents for parallel deep dives. The summary is a starting point, not a constraint. Make no assumptions about what kind of content the user is working with — code, writing, research, planning, anything.

Claude is the executor. The skill is a prompt with affordances, not a rigid pipeline.

## Output

**Free-form.** No fixed template. The right shape of the response depends on what's actually happening that day. The session decides whether to lead with a status report, an alert, a question, or a proposed next move.

Loose guidance baked into the skill:
- Synthesize across all four streams — don't just dump them
- Identify what's actually blocking progress (Theory of Constraints applied at the daily level)
- Propose concrete next moves ranked by leverage
- End by asking which (if any) the user wants to act on

## State

A single directory at `~/.jarvis/`:

- `~/.jarvis/cursor` — empty file. Its `mtime` IS the last-invocation timestamp. Bumped via `touch ~/.jarvis/cursor` at the end of every successful run. All "since last invocation" queries use this file's mtime.

That's the only state. No JSON config, no databases, no caches in v1.

## Out of Scope (v1)

- **Persistent per-session summary cache** (`~/.jarvis/summaries/<sessionId>.md`). Optimization for later if Gemini costs become annoying or repeated invocations get slow.
- **Per-repo cursor JSON** for incremental diffs. v1 just uses the global Jarvis cursor for repo commits too — small accuracy loss, big simplicity win.
- **claude-manager integration.** Jarvis works whether or not the manager is running. They are independent products.
- **Scheduled / cron invocation.** v1 is manual only. The `loop` skill can wrap it later if needed.
- **Multi-view filtering** ("just personal," "just code"). v1 returns the full picture every time.
- **Output to non-terminal sinks** (Slack, email, push notification). v1 outputs in the current Claude session and that's it.

## Termination Criteria

v1 is done when:

1. `~/.claude/skills/jarvis/SKILL.md` exists with the data-gathering instructions and synthesis guidance.
2. Invoking `/jarvis` from a fresh Claude Code session produces a useful synthesis without any other process running.
3. Subsequent invocations correctly use the cursor to scope to "what's new."
4. The skill works regardless of whether claude-manager is running.

## Future Optimizations (Deferred)

Layer in only when actual friction shows up — not pre-built. Ranked by likely leverage:

1. **Persistent per-session summary cache** — saves Gemini calls on repeat invocations
2. **Per-repo cursor tracking** — more accurate "what's new" per repo
3. **Subagent dispatch defaults** — parallel deep dives when N sessions exceeds some threshold
4. **Output sinks** — push to Slack/phone for proactive briefings
5. **Jarvis-as-cron** — wrap with the `loop` skill for morning briefings
6. **Cross-session memory layer** — claude-subconscious or equivalent so Jarvis remembers prior briefings

## Reference

- Long-form planning context: `Workspace/jarvis-planning.md`
- Engineering principles applied (walking skeleton, find the bottleneck, match operation to tool): `Workspace/engineering-principles.md`
