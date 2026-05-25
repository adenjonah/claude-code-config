# Claude Code Landscape — March 2026

Compiled from X/Twitter via Grok API + Exa web search. Last updated 2026-03-25.

---

## How Power Users Are Using Claude Code

### The 4-Layer System
CLAUDE.md → Skills → Hooks → Agents. This is the consensus architecture for serious Claude Code usage. Each layer adds structure without removing flexibility.

### Day-to-Day Patterns
- CLI for code review, PRs, deploys, refactoring via slash commands
- Config via `.claude/` (CLAUDE.md for architecture/rules, skills/agents for auto-triggers)
- `/clear` between tasks to reset context
- Memory files for compounding rules across sessions
- Reports saving 3-4 hours per project but requiring domain knowledge

### What People Love
- "Easily the best price-to-usage AI coding setup"
- Auto-spawns agents (reviewer/security), self-improves
- 1M token context fixes previous limits
- From experiment to "tool I cannot work without"

### What Frustrates Them
- "Shocking mistakes" — overly complex code, ignores style, breaks prod
- Needs 100% supervision; "confidently wrong"
- Slow TUI (10min no feedback), permission popups
- Mediocre without .claude/ config habit
- "Not sure delivering more value" vs manual for some users

---

## Multi-Agent Orchestrators

### Agent Teams (Built-in, Experimental)
- One lead coordinates, teammates communicate directly
- Shared task list with self-coordination
- 3-5 teammates, 5-6 tasks each recommended
- `--dangerously-skip-permissions` flows to all teammates
- Enable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

### Gas Town (Steve Yegge)
- Dominant third-party orchestrator, OSS
- Manages swarms of Claude Code agents
- Called "the new IDE for 2026"
- Powerful but overwhelming ("AI brain fry")
- Steve Yegge runs 3 concurrent Claude Max accounts to feed it
- `git clone https://github.com/steveyegge/gastown`

### Multiclaude
- Simpler than Gas Town
- Better for "give long prompt and walk away"
- Better for team usage/review

### OpenClaw (formerly Clawdbot)
- Always-on AI daemon, runs on your machine or VPS
- Full system access: files, email, calendar, web, apps, shell, sub-agents
- Connect via WhatsApp/Telegram/Discord/Signal
- Uses **API keys** (not your Claude subscription)
- Open source, `curl -fsSL https://get.openclaw.ai | bash`
- Created by Peter Steinberger (@steipete), now community-driven
- Renamed from Clawdbot after Anthropic trademark C&D
- Use cases: inbox management, trading bots ($50→$828 Polymarket), 550 UGC videos/day

### Other Orchestrators
- **Beads** — agent orchestrator, used alongside Gas Town
- **KERNEL** (Aria Han) — plugin that auto-classifies task complexity, routes to agent tiers, stores research/plans in shared DB
- **GStack / Overstory / Mission Control / DeerFlow** — various harnesses

---

## Memory & Persistent Context

### claude-subconscious (Letta)
- Background agent that watches all sessions, builds persistent memory
- Auto-injects relevant memories before each prompt
- First prompt: full memory block. Subsequent: diffs only (near-zero token cost)
- Runs on Letta's cloud (api.letta.com), default model is free (zai/glm-5)
- Install: `/plugin marketplace add https://github.com/letta-ai/claude-subconscious` then `/plugin install claude-subconscious`
- Needs `LETTA_API_KEY` from app.letta.com

### OpenMemory (Mem0)
- Portable memory across Claude Code/Desktop/Cursor/Copilot
- Hooks into session start/end/compaction
- Extracts decisions and anti-patterns into long-term memory
- Web dashboard at app.openmemory.ai
- Install: `/plugin add mem0ai/claude-code-plugin`

### Built-in Memory System
- MEMORY.md files in `.claude/projects/` directories
- Project-scoped, loaded automatically per working directory
- Manual but reliable

---

## Autonomous Execution Methods

### Auto Mode (Released March 2026)
- `Shift+Tab` or `claude --enable-auto-mode`
- Safeguards classifier auto-approves low-risk actions, prompts for high-risk
- Middle ground between manual approval and full skip

### `--dangerously-skip-permissions`
- Skips ALL prompts, no safety net
- Required for true unattended operation (ralph loop, overnight builds)
- Risk: prompt injection from malicious repo files (60k+ public repos vulnerable)

### Ralph Loop
- Plugin that restarts Claude Code when it exits
- `/ralph-loop` to start
- Combined with skip-permissions = true autonomy
- Reports of 27 hours / 84 tasks in one run

### Auto-Compact Configuration
- `CLAUDE_CODE_AUTO_COMPACT_WINDOW` — set context capacity for compaction (e.g., 200000 on 1M model)
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` — percentage trigger (e.g., 80 = compact at 80% of window)
- Prevents quality degradation on long sessions

### Remote Control
- `claude rc` — control your local session from phone/browser
- Session runs on your machine, phone is just a window
- Your CLAUDE.md, MCPs, local files all stay available
- Laptop must stay on (unlike cloud)
- Max plan (Pro coming)

### Claude Code on the Web (Cloud)
- Runs on Anthropic's sandboxed Linux VM at claude.ai/code
- No access to local files/MCPs/config
- Laptop can be off
- Pro or Max plan

---

## Key People to Follow
- **@steipete** — Peter Steinberger, OpenClaw creator
- **@steveyegge** — Steve Yegge, Gas Town creator
- **@bcherny** — Boris Cherny, Claude Code creator at Anthropic
- **@noahzweben** — Claude PM
- **@MatthewBerman** — AI tool reviews
- **@PrakashS720** — Claude Code power user tips
- **@trq212** — Claude Code workflows
- **@ariaxhan** — Aria Han, KERNEL plugin creator

---

## Viral Takes (March 2026)
1. Desktop control preview (123k likes) — Claude uses your apps/browser/spreadsheets
2. Channels release (25k likes) — message Claude from phone via Telegram/Discord
3. Pentagon hack (7k likes) — flagged $4.2B overpays, drafts bids
4. Matt Shumer "Something Big Is Happening" (86.1M views) — saved in Workspace

---

## Anthropic Harness Design (March 24, 2026)

Source: https://www.anthropic.com/engineering/harness-design

Three agents: **Planner → Generator → Evaluator**

Key findings:
- Self-evaluation doesn't work — separate the builder from the judge
- Opus 4.6 runs coherently for 2+ hours with auto-compaction
- Sprint decomposition was scaffolding for weaker models — unnecessary on Opus 4.6
- Communication via files, not messages
- "Find the simplest solution possible, only increase complexity when needed"

Full details in CLAUDE.md and `Autonomous Build Workflow.md`.
