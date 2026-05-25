# Engineering Principles for Building & Managing Agents

A working reference of the principles that came up while designing the Jarvis command. Most of them are not from software engineering — they're from operations, lean, and management. Software engineering is about static artifacts (compose pure functions over data). Managing agents is about flow (route work through agents with state and feedback). Different category, different principles.

The principles are grouped by what kind of failure they prevent.

---

## 1. Build the Right Thing (Smallness & Leverage)

### Walking Skeleton First (Alistair Cockburn)

Get an end-to-end thin slice working before adding depth anywhere. The walking skeleton is the smallest implementation that touches every layer of the system and produces the actual outcome — even if every layer is hacky, hardcoded, or stubbed. Once it exists, you have something to optimize and a way to know whether your optimizations help.

**The failure it prevents:** Building all the prerequisites before you have anything that works. You end up with a half-built foundation, no working product, and no way to test whether your assumptions about what's needed are correct.

**Concrete version for agent work:** The minimum viable Jarvis is one skill file with a bash script that reads existing files and one synthesis call. Hooks, indices, summaries, dashboards are all *optimizations*. Build the skill first; layer the optimizations only when you feel friction.

### Optimizations Are Not Prerequisites

Most of what feels like "I need to build X first" is actually "X would make this faster/cheaper/cleaner once it works." Those aren't prerequisites; they're optimizations. Build the unoptimized thing first, then optimize the parts that hurt.

**The failure it prevents:** Pre-building infrastructure for a product that doesn't exist yet. You optimize the wrong layer because you haven't seen where the real friction is.

**Test:** Ask "what does this buy that the raw files don't?" If the answer is "speed" or "cost" or "convenience," it's an optimization. If the answer is "the outcome itself," it's a prerequisite.

### YAGNI — You Aren't Gonna Need It

Don't build features for hypothetical future requirements. Three similar lines is better than a premature abstraction. The version you build for the imagined future case is almost always wrong, because you don't actually know the constraints of the future case yet.

**The failure it prevents:** Architecture astronomy. Generalizing before you have two real instances to generalize from.

### Worse Is Better (Richard Gabriel)

A simpler implementation that covers 80% of cases is usually better than a complete implementation that covers 100%. Simpler means faster to build, faster to understand, faster to change, and easier to throw away. Completeness has a cost that's invisible until you try to maintain it.

**The failure it prevents:** Spending weeks on edge cases that no one will ever hit, while the core thing gets neglected.

### Pareto / 80-20

80% of the value comes from 20% of the work. When ranking next moves, find the 20% and do that. The other 80% is usually optional, deferrable, or someone else's problem.

**The failure it prevents:** Spending equal effort on every item in a list, when the items have wildly different leverage.

### MVP / Build-Measure-Learn (Lean Startup)

Ship the smallest thing that can produce real signal. Then look at the signal. Then decide what to build next. The point is not "build a small product"; the point is "create a feedback loop with reality as fast as possible."

**The failure it prevents:** Building elaborate plans that turn out to be solving the wrong problem because you never tested them against reality.

---

## 2. Find the Right Place to Act (Theory of Constraints)

### The Bottleneck Is the Only Thing That Matters

From Eli Goldratt's *The Goal*. Every system has exactly one bottleneck at any given time. Optimizing anywhere that isn't the bottleneck is wasted effort — at best you're piling up more inventory in front of the constraint; at worst you're slowing the system down with unnecessary complexity.

**The discipline:**
1. Identify the constraint
2. Decide how to exploit the constraint (use 100% of its capacity)
3. Subordinate everything else to the constraint
4. Elevate the constraint (only if steps 1-3 aren't enough)
5. Once the constraint moves, repeat — the new bottleneck is usually somewhere else entirely

**The failure it prevents:** Working on whatever feels productive instead of whatever's actually blocking progress. "This bug fix would be nice" — but does it unblock anything? "This refactor would be cleaner" — but is the current state actually slowing you down?

**Concrete version for agent work:** Don't fix what isn't blocking you. If your manager dashboard has a bug but you mostly use sessions through tmux directly, the bug isn't your bottleneck. If you can't tell what your sessions are doing, *that's* the bottleneck — and the fix isn't more hooks, it's the simplest thing that gives you visibility.

### Don't Pre-Build the Optimizations

Corollary to Theory of Constraints. The "correct" optimization order is set by where pain shows up, not by where you imagine pain will show up. Reality is a better ranker than your model of reality.

---

## 3. Match the Operation to the Right Tool

### Use Cheap Models for Cheap Operations

Two-stage pipelines exist for a reason. Summarization is a cheap operation that cheap models do fine. Synthesis and reasoning are expensive operations that need a capable model. Don't make the expensive model do both — pay $0.03 for Gemini Flash Lite to summarize the noise out, then pay for one clean call to the expensive model to reason over the result.

**The failure it prevents:** Cramming raw data into the most expensive model on every invocation. The "one big call" feels simpler but is doing two jobs poorly instead of two calls doing each job well.

**The math you must do:** Before claiming "this is cheap," multiply tokens × price-per-token. Sonnet at $3/M input means 500K tokens = $1.50 per call. Opus at $15/M means $7.50 per call. Run something 5 times a day and you're at $7-37/day. "Free" is not the same as "fits in context."

### Reducing Call Count Is a Proxy, Not the Goal

"One LLM call" sounds simpler than "two LLM calls" but only if both calls are doing the same job. If the two calls are matched to two different operations (cheap summarization + expensive synthesis), collapsing them into one is *worse*, not better.

**The failure it prevents:** Optimizing for a metric that proxies for simplicity (call count, file count, line count) instead of for simplicity itself (does this match the shape of the problem?).

### Minimize Context, Don't Maximize It

"Fits in 1M tokens" is a constraint, not a target. Long context degrades reasoning quality even when nothing overflows. Models lose focus when crammed with low-signal tokens. The needle-in-haystack problem is real even at long contexts. Good engineering minimizes the input the expensive call sees.

**The failure it prevents:** Treating context capacity as a budget to spend rather than a ceiling to stay under.

---

## 4. The Discipline of Building

### Make It Work, Make It Right, Make It Fast (Kent Beck)

Three phases, in order:
1. **Make it work** — produce the correct output for the easy cases. Don't worry about elegance or performance. Hardcode whatever you can.
2. **Make it right** — refactor the working version into something clean. Now you know what the code needs to do.
3. **Make it fast** — only after it works and is clean, optimize the parts that are actually slow.

**The failure it prevents:** Trying to write clean, fast code from scratch. You can't know what's clean before you know what works, and you can't know what's slow before you can measure it.

### First, Make the Change Easy; Then Make the Easy Change (Kent Beck)

When you need to add a feature and the existing code makes it hard, *first* refactor the existing code so the new feature is easy to add. Then add the feature. Don't do both at once — that's how you end up with a half-refactored, half-extended mess that no one can review.

**The failure it prevents:** Mixing refactoring and feature work in the same change. The PR becomes unreviewable, the bugs compound, and rolling back means losing both pieces.

### Separate Generator From Evaluator

From Anthropic's harness research. Self-evaluation doesn't work — agents confidently praise their own output, even when it's mediocre. Always have a different agent (or a different model, or a deterministic check) judge the work. The generator is allowed to be optimistic; the evaluator must be skeptical.

**The failure it prevents:** Trusting an agent's claim that it finished the task, then discovering hours later that the work is broken.

**Concrete:** When dispatching a build, also dispatch a separate QA teammate whose job is to test the running app skeptically and report what's broken. Don't let the builder grade itself.

---

## 5. Managing Agents Like Operations, Not Like Functions

### Brooks's Law

Adding people to a late project makes it later. Communication overhead grows quadratically with team size. Each new person needs to be onboarded by people who would otherwise be doing the work, and once added they need to coordinate with everyone else.

**Applied to agents:** Adding more parallel agents to a confused workflow makes it more confused, not faster. Cap team size at what you can actually coordinate. 3-5 teammates is the sweet spot for agent teams; beyond that, the lead spends more time coordinating than the teammates spend producing.

### Pull, Not Push (Lean / Toyota Production System)

Don't queue up a giant plan and push tasks at agents in advance. Let work be pulled by capacity — when an agent is idle, it pulls the next task from the queue. This naturally prevents WIP from piling up and keeps the system responsive to changing priorities.

**The failure it prevents:** Pre-assigning tasks to agents that may not be the right fit by the time they're ready to work, and accumulating WIP that hides real progress.

### Build In Quality (Jidoka)

Quality should be checked at the source, not at the end. Don't let bad work pass downstream and get caught at "QA time" — every step should validate its own output before handing off. In agent terms: every teammate verifies the thing it built before reporting completion. The lead doesn't have to chase down broken work after the fact.

### Clear Context + Clear Outcome + Autonomy + Verification

The right way to delegate to a capable agent (or human). Four elements:
1. **Clear context** — what is this for, why does it matter, what constraints exist
2. **Clear outcome** — what does done look like, what's the quality bar
3. **Autonomy** — how to do it is the agent's call, not yours
4. **Verification** — check after, not during

**The failure it prevents:** Step-by-step micromanagement that wastes your time, frustrates the agent, and produces worse output than a clearly-briefed autonomous run. If you find yourself writing "first do X, then do Y, then do Z" you're probably treating the agent as a function instead of a delegate.

### Don't Pre-Assign Roles in an Agent Team

Let the lead read the spec, decompose the work, and decide which teammates to spawn. The lead has context you don't — the actual shape of the codebase and the actual dependencies between tasks. Pre-assigned teammates are usually wrong by the time work starts.

---

## 6. Thinking Discipline (For Both Of Us)

### Do the Arithmetic Before You Claim

If you're going to say "this is cheap" or "this fits" or "this scales," compute the actual numbers first. `tokens * price_per_token`. `requests_per_second * latency`. `users * avg_session_length`. Don't quote a confident figure without doing the multiplication, because confident figures get repeated and become facts.

**The failure it prevents:** Stating numbers that sound right but are wrong by an order of magnitude. (This is the lesson from the Jarvis discussion — quoting "$0.10–0.30 per call" without computing 500K × $3/M = $1.50.)

### Think From First Principles, Not From Reactions

When someone pushes back, the right response is to re-examine your reasoning, not to immediately produce whatever the person seems to want. If your previous answer was correct, defend it. If it was wrong, understand *why* it was wrong before producing a new answer. Don't pattern-match on the user's frustration and strip components for the sake of stripping.

**The failure it prevents:** Performing simplification instead of doing it. Each round of "user wants simpler, so I'll remove one more thing" can degrade a correct design into garbage if you're not asking what each layer was actually doing.

### "Fits in Context" ≠ "Should Be In Context"

Capacity and target are different. Just because something fits doesn't mean it belongs. Apply this to context windows, team sizes, file sizes, build times — anywhere you have a ceiling, the goal is to stay well under it, not to fill it up.

### Read Before You Write

Read the existing code, the existing files, the existing docs before proposing changes. Most "missing" features already exist; most "needed" infrastructure is already built. The first move on any new task is reading what's already there, not designing what should be there. (The whole reason this principles doc exists is because I kept proposing infrastructure for things Claude Code already provides.)

---

## 7. Composability & Robustness

### Postel's Law (Robustness Principle)

"Be conservative in what you do, be liberal in what you accept." Your outputs should be predictable and follow strict conventions; your inputs should tolerate variation. Applies to APIs, file formats, user interfaces, and prompts to agents.

**Applied to prompts:** Be specific in what you ask the agent for (output format, scope, constraints), but accept that the agent's output may have minor variations. Don't reject a valid response because of formatting nits.

### Single Responsibility Principle (SRP)

Each module, function, skill, or agent should do one thing. When a thing does two things, the two things eventually pull it in opposite directions and it does both poorly.

**Applied to skills:** One skill = one responsibility. Don't merge "fetch data" and "synthesize data" into one skill. Don't merge "manage sessions" and "synthesize Jarvis briefings" into one agent.

### Compose Existing Tools Before Building New Ones

Bash + git + jq + the filesystem can do an enormous amount before you need to build new infrastructure. The fact that the underlying primitives are ugly doesn't mean you need a polished alternative — it means you need a small wrapper that hides the ugliness for your specific use case.

**The failure it prevents:** Building parallel infrastructure to things that already exist. Reading raw files in `~/.claude/sessions/` is usually faster than building an index of those files.

---

## 8. System Properties

### Conway's Law

"Organizations design systems that mirror their communication structure." If the team has three groups, the architecture will have three layers. If you work alone, the architecture will be flat. If your agents don't talk to each other, your codebase will have no shared abstractions.

**Applied to agent management:** The structure of your agent team will determine the structure of the output. If you spawn one big agent to do everything, you get a monolith. If you spawn five agents that communicate through files, you get a system with five components and file-based interfaces.

### Antifragility (Taleb)

Some systems get *stronger* from stress and failure, instead of just surviving them. Design for systems that learn from incidents — every failure should produce a permanent improvement, not just a fix for that specific failure. (This is what `/vent` and `/therapy` are for in the Claude harness — every mistake gets recorded and turned into a structural fix, not just a one-time correction.)

### Principle of Least Surprise

The behavior of a system should match what a reasonable person would expect from its name and interface. If a function is called `delete_user`, it should not also send an email. If a skill is called `summarize`, it should not also propose next moves.

**Applied to skills:** Pick names that say what the thing does. If the name doesn't fit anymore, rename it.

---

## How These Principles Apply to Building Jarvis (Concrete Worked Example)

The Jarvis discussion was a worked example of getting these wrong twice in opposite directions.

**Round 1: Over-engineering.** Proposed a 6-step plan starting with manager bug fixes, hooks, summaries, playbooks, and only *then* the actual product. Violated walking skeleton (built prerequisites before the thing), Theory of Constraints (fixed bugs that weren't blocking), and YAGNI (wrote infrastructure for a product that didn't exist).

**Round 2: Over-simplifying.** After getting caught on round 1, swung the other way: proposed dumping `tail -n 500` of every JSONL into one giant Claude call. Violated "match operation to tool" (used the expensive model for a cheap operation), "do the arithmetic" (claimed $0.10-0.30 when the actual cost was $1.50), "minimize context" (filled 500K tokens with garbage), and "think from first principles" (pattern-matched on "user wants simpler" instead of asking what each component did).

**The middle path that respects all the principles:** A skill file with a bash script that finds recent sessions, summarizes each one cheaply with Gemini Flash Lite (cheap model for cheap operation), then makes one Claude call to synthesize over the clean summaries (expensive model for expensive operation, with minimized context). No hooks. No bug fixes. No new infrastructure. Just two appropriately-sized calls in the right order.

That's the walking skeleton. Optimizations (caching summaries, hooks for SessionEnd, manager bug fix, river substrate) get layered in *only* when friction shows up.

---

## Reading List

If any of these principles feel useful, the underlying books are worth reading. None are about software:

- **Goldratt, *The Goal*** — Theory of Constraints in novel form. The most important book on operations thinking.
- **Reinertsen, *The Principles of Product Development Flow*** — the most quantitative book on managing knowledge work. Heavy but essential.
- **Kim, Behr, Spafford, *The Phoenix Project*** — TOC + Lean applied to IT operations, also as a novel.
- **Brooks, *The Mythical Man-Month*** — old but still correct on the social dynamics of building software.
- **Beck, *Extreme Programming Explained*** — the source of "make it work, make it right, make it fast" and "first make the change easy, then make the easy change."
- **Cockburn, *Crystal Clear*** — origin of walking skeleton and a lot of the agile-but-not-stupid school.
- **Anthropic engineering blog, "Harness Design"** — the most relevant modern source for the agent-specific versions of these principles. Generator vs. evaluator, decoupling brain from hands, why self-evaluation doesn't work.
