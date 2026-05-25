# Development Workflow

## Feature Implementation Pipeline

0. **Research & Reuse** _(mandatory before any new implementation)_
   - Search GitHub for existing implementations and patterns
   - Check package registries (npm, PyPI) before writing utility code
   - Prefer battle-tested libraries over hand-rolled solutions
   - Search for adaptable implementations that solve 80%+ of the problem

1. **Plan First**
   - Use **planner** or **question-refinement** agent for implementation plan
   - Identify dependencies and risks
   - Break down into phases

2. **TDD Approach**
   - Use **test-writer** agent
   - Write tests first (RED)
   - Implement to pass tests (GREEN)
   - Refactor (IMPROVE)
   - Verify 80%+ coverage

3. **Code Review**
   - Use **code-reviewer** agent immediately after writing code
   - Address CRITICAL and HIGH issues
   - Fix MEDIUM issues when possible

4. **Commit & Push**
   - Detailed commit messages (conventional commits)
   - Always push when finishing work (multi-machine sync)
