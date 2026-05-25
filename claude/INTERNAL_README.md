# Jonah's Claude Code Setup

Custom skills, agents, rules, and reference docs for Claude Code.

---

## Directory Layout

```
~/.claude/
  CLAUDE.md           Global behavioral directives + mandatory auto-triggers
  README.md           This file
  settings.json       Hooks, permissions, model config
  skills/
    corrections/      Make Claude less wrong — behavioral tools
    research/         Knowledge and content tools
    mobile/           iOS and Swift tools
    orchestration/    Session management (log-session)
    learned/          System-managed skill memory
  agents/             Custom agent definitions (35 agents, flat — required by Claude Code)
  rules/
    common/           Universal coding standards (auto-loaded every session)
    typescript/       TypeScript-specific patterns (auto-loaded in TS projects)
  docs/               Reference documents — principles, playbooks, landscape surveys
```

---

## Skills

### corrections/
| Skill | What it does |
|---|---|
| **human-writing** | Write prose that sounds like Jonah — kills AI patterns, enforces his voice |
| **vent** | Log a gripe about Claude's behavior to the therapy system |
| **therapy** | Review logged gripes, find patterns, design structural fixes |
| **second-opinion** | Query GPT/Gemini/Grok for an independent take on a decision |

### research/
| Skill | What it does |
|---|---|
| **graphify** | Turn any input (code, docs, papers) into a knowledge graph |
| **youtube-parse** | Fetch and analyze a YouTube video |
| **youtube-dl** | Download MP3 or MP4 from YouTube |

### mobile/
| Skill | What it does |
|---|---|
| **ios-testing** | iOS testing expert for unit tests |
| **swiftui-components** | SwiftUI component expert |
| **code-analyzer** | Read-only code analysis for architecture review |

### orchestration/
| Skill | What it does |
|---|---|
| **log-session** | Log current session with commits, timestamps, resume info |
| **manager** | List, message, kill, create, and monitor Claude Code sessions via recon API |
| **consult** | Ask another running Claude Code session a question and get an answer back |

**Recon backend** — `~/dev/claude-manager/server/target/release/recon`
- Starts automatically when `/manager` or `/consult` is invoked
- Runs at `localhost:3100`
- To rebuild after updates: `cd ~/dev/claude-manager && cargo build --release --manifest-path server/Cargo.toml`

---

## Agents

35 custom agents in `agents/`. Key ones:

| Agent | Auto-triggered? |
|---|---|
| **bookkeeper** | Yes — mandatory at every session end |
| **memory-retrieval** | Yes — mandatory before dev work |
| **latex-doc** | Yes — any LaTeX request |
| **study-guide** | Yes — any study guide request |
| **stats-helper** | Yes — stats questions |
| **essay-planner** | For academic essay planning |
| **quote-finder** | Find verified quotes from course materials |
| **source-researcher** | Search course materials broadly |
| **homework-solver** | Solve homework with Python-verified math |
| **architect** | System design and architecture reviews |
| **deep-debug** | Systematic bug investigation |
| **security-reviewer** | Security vulnerability detection |
| **test-writer** | Comprehensive test writing |
| **tdd-guide** | TDD enforcement |

---

## Rules

Auto-loaded by Claude Code. No action needed.

`rules/common/` — loads in every session:
- `agents.md` — agent orchestration patterns
- `coding-style.md` — immutability, file organization, error handling
- `development-workflow.md` — feature pipeline, research-first, TDD
- `git-workflow.md` — commit format, PR workflow, multi-machine sync
- `hooks.md` — hook types and patterns
- `ios-dev.md` — Swift 6, SwiftUI, XcodeBuildMCP
- `performance.md` — model selection, context window management
- `security.md` — mandatory security checks, secret management
- `testing.md` — 80% coverage, test types, TDD

`rules/typescript/` — loads in TypeScript projects:
- `coding-style.md`
- `patterns.md`
- `security.md`

---

## Docs

Reference documents — not auto-loaded, but linked from CLAUDE.md and skills:

| Doc | What it is |
|---|---|
| `engineering-principles.md` | 19 principles from operations/lean/management applied to agent work |
| `autonomous-build-workflow.md` | Playbook for autonomous builds — agent teams, ralph loops, Planner/Generator/Evaluator |
| `claude-code-landscape.md` | Survey of the Claude Code ecosystem (March 2026) |
| `jarvis-spec.md` | Design spec for a session orientation skill (future implementation) |

---

## Therapy System

Behavioral improvement loop — logs patterns, designs structural fixes:

- **`/vent`** — log a gripe immediately when something goes wrong
- **`/therapy`** — review patterns, design fixes, implement interventions

Logs live at `~/notes/therapy/`.

---

## Adding New Skills

1. Create `~/.claude/skills/<category>/<skill-name>/SKILL.md`
2. Add `name:` and `description:` frontmatter
3. Add trigger rule to `~/.claude/CLAUDE.md` if it should auto-fire
4. Update this README

## Adding New Agents

1. Create `~/.claude/agents/<agent-name>.md` (must be flat, no subdirs)
2. Add frontmatter: `name:`, `description:`, `tools:`
3. Add auto-trigger to `CLAUDE.md` if needed
