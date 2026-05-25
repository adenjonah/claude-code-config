# Performance Optimization

## Model Selection Strategy

**Haiku 4.5** (lightweight, cost-efficient):
- Utility agents (bookkeeper, memory-retrieval)
- Frequent invocation worker agents
- Simple code generation

**Sonnet 4.6** (best coding model):
- Main development work
- Orchestrating multi-agent workflows
- Complex coding tasks

**Opus 4.6** (deepest reasoning):
- Complex architectural decisions
- Research and analysis tasks
- LaTeX document generation

## Context Window Management

Avoid last 20% of context window for:
- Large-scale refactoring
- Feature implementation spanning multiple files
- Debugging complex interactions

Lower context sensitivity tasks:
- Single-file edits
- Independent utility creation
- Documentation updates
- Simple bug fixes

## Extended Thinking + Plan Mode

For complex tasks requiring deep reasoning:
1. Ensure extended thinking is enabled (on by default)
2. Enable **Plan Mode** for structured approach
3. Use multiple critique rounds for thorough analysis
4. Use split role sub-agents for diverse perspectives
