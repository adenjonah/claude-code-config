---
name: therapy
description: Review logged gripes, identify patterns, design and implement structural fixes for recurring Claude behavior problems. Use when the user says "let's fix this", "what keeps going wrong", or invokes /therapy.
---

# Therapy

Like CBT: identify patterns in behavior, understand what causes them, design structural interventions that change the behavior at its root. Not more rules — actual changes to how Claude works.

## When to use

- User invokes `/therapy`
- User says "let's fix this," "let's talk about what keeps going wrong," or similar

## Steps

### 1. Review the current state

Read:
- `~/notes/therapy/problems/index.md` — index of known problems
- `~/notes/therapy/problems/general.md` — undiagnosed gripes
- `~/notes/therapy/feedback-log.json` — recent entries

If these files don't exist yet, say so and offer to start the system from scratch.

Present a brief summary: what's been logged since the last session, what existing problems have new entries, what's sitting in general.md.

### 2. Look for patterns in general.md

Do undiagnosed gripes cluster together? Do they connect to existing problems? Discuss with the user. If a new pattern emerges:
- Create a new problem file in `~/notes/therapy/problems/`
- Add it to the index
- Move relevant entries from general.md to the new file

### 3. For each active problem, review the log

Is the intervention working? Evidence: has the user complained about this pattern recently? Are complaints getting less severe? Did the intervention fire in relevant situations?

Discuss honestly. If it's not working, figure out why together.

### 4. Design or refine interventions

An intervention is a structural change that makes the bad behavior less likely — not a rule, a process change. Options (best to worst):

- **Hook** — automated trigger in settings.json (fires without relying on Claude's attention)
- **New skill** — a process that fires in specific situations
- **Skill modification** — adding steps or checks to an existing skill
- **CLAUDE.md directive** — a persistent instruction (weakest option, Claude can miss it)

For each intervention, discuss: what's the trigger? What's the cause? What structural change addresses the cause? How will we know if it's working?

### 5. Implement

Build whatever was agreed on. Update the problem file with what was done. Change the status:
- **flagged** — identified but no intervention yet
- **working on it** — intervention designed, being implemented
- **unresolved** — intervention exists but isn't working
- **resolved** — pattern no longer occurring

### 6. Update the index

Make sure `~/notes/therapy/problems/index.md` reflects current state.

## Rules

- This is collaborative. Don't diagnose and prescribe — discuss with the user.
- Be honest about what's not working. Don't claim progress that isn't there.
- Prefer structural fixes over rules. Rules get ignored. Process changes stick.
- One session doesn't need to address everything. Pick what's most urgent.
