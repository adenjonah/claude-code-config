# Agent Orchestration

## Immediate Agent Usage

No user prompt needed — delegate automatically:
1. Complex feature requests → **planner** or **question-refinement** agent
2. Code just written/modified → **code-reviewer** agent (via plugin)
3. Bug fix or new feature → **tdd-guide** or **test-writer** agent
4. Architectural decision → **architect** agent
5. Security concern → **security-reviewer** or **deep-audit** agent
6. Build errors → **build-error-resolver** agent

## Parallel Task Execution

ALWAYS use parallel Task execution for independent operations:

```markdown
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: Security analysis of auth module
2. Agent 2: Performance review of cache system
3. Agent 3: Type checking of utilities

# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
