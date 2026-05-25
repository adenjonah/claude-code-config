# Autonomous Build Workflow

A spec for building big features with Claude Code — maximally autonomous, minimal human intervention.

Source: Anthropic's harness design post (March 24, 2026), X research on Claude Code power usage, and personal experience.

---

## The Setup

### Environment

```bash
# Auto-compact at ~160K tokens (not 950K) to keep quality high
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=80

# Start with full permissions and agent teams
claude --dangerously-skip-permissions
```

Agent teams must be enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings — already configured).

### The Ralph Loop

Start `/ralph-loop` so the lead agent restarts if it crashes or exits. The lead's job is to keep going until the work is done.

---

## The Pattern

### One Lead Agent, Self-Directed

The lead agent gets:
1. The design doc / feature spec
2. A directive to work autonomously
3. Permission to spawn teammates as it sees fit
4. A progress file to maintain for continuity

**Do NOT pre-assign teammates or roles.** The lead reads the spec, reads the codebase, and decides how to decompose the work. It might spawn 2 teammates for a small feature or 5 for a big one. It might restructure the team mid-build as the work evolves. Let it decide.

### The Prompt Template

> **CRITICAL RULE:** The spec IS the spec. The ralph loop prompt should be a TINY POINTER to the spec, not a rewrite of it. If a good spec already exists at a known path, the ralph prompt is 2-4 sentences. Do NOT restate the spec's contents, episode lists, model configs, termination criteria, or hard constraints — those live in the spec file. Duplicating them in the prompt creates drift and wastes context.
>
> **Test:** If your ralph prompt is longer than 8 lines, you are probably rewriting the spec. Stop and point at the spec instead.

#### Variant A: Running from a pre-written spec (most common)

When the spec already exists as a file in the repo (e.g. `docs/specs/xyz.md`), the ralph prompt is a pointer. Full command you paste into Claude Code:

```
/ralph-loop Read [SPEC PATH]. Do what it says. Follow the ABW protocol at [path to your ABW doc] — use [PROGRESS FILE PATH] as the state file, spawn teammates as you see fit, commit often, terminate when the spec's termination criteria are met.
```

Concrete example:

```
/ralph-loop Read docs/specs/0411-mining-spec.md. Run that campaign. Follow the ABW protocol at [path to your ABW doc] — use runs/001_breadth-sweep/PROGRESS.md as the state file, spawn teammates as you see fit, commit often, terminate when the spec's termination criteria are met.
```

That's the entire prompt. The agent reads the spec to learn what to do, reads the ABW doc to learn HOW to work (teams, PROGRESS.md, git discipline, termination), and begins. No duplication.

#### Variant B: No pre-written spec (ad-hoc build)

Only use this when there isn't a spec file yet and the work is being defined in the prompt itself:

```
Read [DESIGN DOC PATH]. Build this.

Work autonomously using agent teams. You decide how to decompose the work
and when to spawn teammates. Guidelines:

PLANNING:
- Read the design doc and codebase first
- Write an implementation plan to [PROGRESS FILE]
- Identify natural work boundaries — what can be parallelized, what's sequential

BUILDING:
- Spawn teammates as needed. Each teammate should own distinct files to avoid conflicts
- You coordinate. Teammates execute. Adjust the team as the work evolves
- Commit after every meaningful unit of work with detailed messages explaining WHAT and WHY

EVALUATING:
- After major features land, spawn a QA teammate that uses agent-browser to test the running app
- The QA agent must be skeptical — not self-congratulatory. If something doesn't work, it fails the check
- QA feedback goes back to the building agent to fix before moving on

STATE MANAGEMENT:
- Update [PROGRESS FILE] after each major milestone
- Write it assuming the next reader has ZERO context from this session
- Include: what's done, what's next, architectural decisions made, known issues
- This file is your lifeline if context compacts or the session restarts

TERMINATION:
- When all features are implemented and tested, update PROGRESS with final status and stop
```

**If you find yourself writing Variant B when a spec file exists, STOP. Put the contents in a spec file at `docs/specs/` and use Variant A.**

---

## Why This Works

### From the Anthropic Harness Post (March 2026)

- **Planner → Generator → Evaluator** is the proven three-agent pattern
- **Self-evaluation doesn't work** — agents praise their own mediocre output. Separate the builder from the judge.
- **Opus 4.6 runs coherently for 2+ hours** without sprint decomposition. Don't over-structure.
- **Context resets with structured handoff** beat degraded long context. PROGRESS.md is the handoff artifact.
- **"Find the simplest solution possible, only increase complexity when needed."** Every harness component encodes an assumption about what the model can't do. Stress-test those assumptions.

### From the Community (X/Twitter, March 2026)

- Top users run 3-5 teammates, 5-6 tasks each
- Each teammate owns different files to avoid conflicts
- The 4-layer system: CLAUDE.md → Skills → Hooks → Agents
- Ralph loop + dangerously-skip-permissions = true autonomy
- Auto-compact env vars (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`) keep quality high on 1M context

---

## The State File (PROGRESS.md)

This is the most important artifact. It's what makes restarts seamless.

```markdown
# [Feature Name] — Build Progress

## Status: IN PROGRESS | COMPLETE | BLOCKED

## What's Done
- [Feature 1]: implemented and tested ✓
- [Feature 2]: implemented, QA pending

## What's Next
- [Feature 3]: [brief description of what needs to happen]
- [Feature 4]: blocked on [reason]

## Architectural Decisions
- Chose X over Y because [reason]
- Changed approach to Z after discovering [issue]

## Known Issues
- [Issue description] — not blocking, will address in [feature]

## Team Structure (current)
- Lead: coordinating, managing progress
- Teammate A: working on [what], owns [files]
- Teammate B: working on [what], owns [files]

## Observations / Field Notes
- [Anything surprising, lesson learned, hunch, or thing to tell the next agent]
- [Unstructured — rough lab notebook, not documentation]

## Git Log (recent)
- abc1234: [commit message]
- def5678: [commit message]
```

---

## When to Use This

- **Big features** that span multiple files and take hours
- **New systems** being built from a design doc
- **Refactors** that touch many parts of the codebase
- **NOT for** small bug fixes, quick features, or anything you could do in one session

---

## Checklist Before Walking Away

- [ ] Design doc / spec is written and comprehensive
- [ ] CLAUDE.md in the project has the autonomous build protocol
- [ ] `CLAUDE_CODE_AUTO_COMPACT_WINDOW` and `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` are set
- [ ] `--dangerously-skip-permissions` is on
- [ ] `/ralph-loop` is running
- [ ] You're on a feature branch (so main is safe)
- [ ] The prompt has been given with the design doc path and progress file path
- [ ] You've reviewed the implementation plan before walking away (optional but recommended)
