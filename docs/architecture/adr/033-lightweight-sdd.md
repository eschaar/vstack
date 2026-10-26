# ADR-033: Lightweight SDD Through Changedoc Evolution

**Date:** 2026-10-26
**Status:** accepted

## Context

Existing changedocs describe scope and tests but do not explicitly connect
requirements, execution tasks, and observed verification. Broad changedoc and
report requirements also add ceremony to clear low-risk work. The approved
[change contract](../../changes/lightweight-sdd_changedoc_evolution_20261017.md)
requires stronger agreement and evidence without a second specification system,
new runtime tooling, or increased prompt overhead.

## Decision

Extend the changedoc with change-local obligations, optional useful tasks, and
verification evidence. Allow sufficient issue/chat context for clear low-risk
work. Involve relevant owners while preserving configured gates and approvals.
Use existing analyse/inspect/verify procedures for consistency and completion
review; keep the stage-report schema unchanged.

Keep policy-required baseline reports authoritative. Otherwise use the existing
changedoc or response. Preserve historical documents and additive local-template
seeding; supplement new documents rather than overwriting customized templates.
Replace repetitive guidance with compact, concrete instructions.

## Alternatives Considered

| Alternative                                 | Benefit                                         | Limitation and disposition                                             |
| ------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------- |
| Keep current guidance                       | No adoption work                                | Weak evidence links and unnecessary ceremony; rejected                 |
| New spec/task system with parsing and gates | Potential machine enforcement                   | Duplicate truth, runtime/configuration burden, unproven need; deferred |
| Evolve changedoc and existing procedures    | Shared intent/evidence with proportional effort | Advisory compliance needs review; selected                             |

## Rationale

Existing roles already own scope, contracts, implementation, and verification.
Improving their handoffs is smaller and safer than adding artifacts or a second
orchestrator. Explicit evidence states expose gaps without implying that wording
checks, code coverage, or completed tasks prove acceptance.

## Consequences

- Old documents remain usable; new sections are additive and task lists optional.
- Required failed/unrun checks block full verification. Approved exceptions name
  limitations; they are never passes.
- Agent adherence remains nondeterministic. Static regressions and rendered
  scenario review verify guidance, not autonomous delivery reliability.
- Measure source/rendered text size as a compactness proxy, not exact tokens,
  credits, or a guarantee of lower session cost.

## Option B Pipeline Impact

Future orchestration can reuse stable criterion/evidence references in existing
handoff fields. No mandatory stages, schema fields, revision hashes, approval
signatures, or automated compliance claims are introduced. Configured stage
dependencies and human approvals remain authoritative.

## Related ADRs

- [ADR-010](010-artifact-flow.md): preserves role-owned artifact boundaries.
- [ADR-013](013-instructions-vs-skills-boundary.md): test policy stays in instructions;
  delivery procedures stay in skills.
- [ADR-020](020-install-init-command-semantics.md): preserves additive seeding.
- [ADR-028](028-dag-dependency-semantics.md): preserves configured prerequisites.
