# ADR-006: No Runtime Dependency on External Binaries in Skill Content

> Maintained by: **agents** role

**date:** 2026-03-27\
**status:** accepted

## context

Skill templates must work on any machine without requiring custom binary installation.
VS Code Copilot skills run as instructions to the AI agent, not as scripts.
The agent can run any shell command available in the terminal, but the skills
themselves should not require special binary installation.

## decision

- Skill templates contain only shell snippets using standard commands (`node`, `python`, `go`, `curl`)
- Test framework autodetection uses standard language runtimes only
- No custom binaries required in skill content
- Build infrastructure (generator, tests) is separate from skill runtime
- Fallback shell commands provided for each operation

## alternatives considered

- Include a minimal binary — unnecessary complexity for VS Code target.
- Require custom tool installation — defeats portability goal.

## rationale

Universal portability. The AI agent can execute standard shell commands without
any prerequisites beyond the project's own toolchain.

## impact on future orchestrated pipeline

The future orchestrated pipeline runner will be `scripts/runner.py` (stdlib only), not a
skill runtime dependency.
