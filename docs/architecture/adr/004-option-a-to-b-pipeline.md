# ADR-004: Single-Call Execution with Optional Future Orchestration

> Maintained by: **agents** role

**date:** 2026-03-27\
**status:** accepted

## context

Modern multi-agent models can run sequential pipelines where output from one stage
feeds the next. This enables better quality (each stage focuses deeply) and
parallelism (independent stages run concurrently).

However, the infrastructure for true multi-agent pipelines adds complexity.
For the initial iteration, single-shot behavior is sufficient and simpler.

## decision

Implement single-call execution now, designed so future orchestration requires minimal refactoring.

**Current model:**

- One skill = one model call
- No pipeline runner, no stage output passing

**Possible future model:**

- Pipeline: `[product, architect, designer, engineer, tester, release]`
- Runner calls each stage as a separate model call
- Artifacts pass between stages via files on disk
- Parallel execution within testing concerns is optional, but remains inside the tester stage

**Preparation done now:**

- Stage boundaries are explicit in role and skill documentation
- Skill steps are idempotent
- Resolver system is stateless
- Artifact filenames are canonical and stable

**Refactoring required for future orchestration:**

- Add `scripts/runner.py` that executes the pipeline
- Add user gate logic (pause + await approval)
- No changes to skill templates needed

## rationale

Adopt the simplest executable approach now. Pre-design boundaries so orchestration
is a runner addition, not a skill rewrite.

## impact on future orchestrated pipeline

This is the foundational decision. See also `docs/design/workflow.md`.
