# ADR-018: Skill Genericity — Skills are Procedures, Agents own Workflow Context

> Maintained by: **architect** role

**date:** 2026-05-02\
**status:** accepted — artifact paths made configurable via ADR-021

## context

Several vstack skills currently contain project-specific artifact paths and workflow
sequencing that belongs to the agent layer, not the skill layer.

Examples observed:

- `release-notes` references `docs/releases/{date}.md`, `docs/reports/test-report.md`,
  `docs/reports/security-report.md` as required inputs.
- `pr` references `docs/releases/{date}.md` as the PR body source and enforces
  a vstack-specific release checklist.

These references make the skills correct for vstack's own workflow but incorrect
as general-purpose procedures. A consumer repo with a different documentation
structure cannot use these skills without modification.

This contradicts the install model: skills are installed as reusable procedures
into any repository, not just vstack-structured ones.

ADR-013 established the policy vs procedure boundary for instructions and skills.
This ADR extends that boundary to the skill vs agent layer.

## decision

**Skills are generic procedures. Agents own workflow context.**

### the boundary

| Layer | Contains                                                                                                              | Does not contain                                                                   |
| ----- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Skill | How to perform a task: steps, checks, output format, quality criteria                                                 | Which files to read/write, artifact paths, role sequencing, project-specific gates |
| Agent | When to invoke a skill, which artifacts to pass as context, what output files to write, stop conditions, gate moments | How to perform the task itself                                                     |

### rules

1. A skill must not reference named project artifact paths (e.g. `docs/releases/`,
   `docs/reports/test-report.md`). These belong in the agent template.
1. A skill must not enforce a role-sequencing gate (e.g. "verify tester sign-off before
   proceeding"). Gates belong in the agent template.
1. A skill may reference generic placeholders (e.g. `{release-notes-file}`,
   `{change-summary}`) that the invoking agent resolves.
1. An agent template must declare which artifacts it reads and writes, and may
   reference skills by name to execute specific procedures.
1. The artifact hand-off table in ADR-010 remains authoritative for which role reads
   and writes which files.

### immediate changes

| Skill           | Current violation                                                                        | Fix                                                                    |
| --------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `pr`            | Hardcodes `docs/releases/{date}.md` as PR body source; enforces vstack release checklist | Remove artifact paths; describe generic PR creation procedure          |
| `release-notes` | Hardcodes required input artifact paths and checklist                                    | Remove specific paths; describe generic release note writing procedure |

The removed workflow context moves to the `release` agent template, which already
owns the artifact hand-off contract per ADR-010.

## alternatives considered

1. **Keep skills workflow-specific, document the coupling** — rejected: breaks reusability
   for consumers with different documentation structures. Skills are installed into any repo.

1. **Remove skills entirely and inline everything in agents** — rejected: skills provide
   reusable, named procedures that can be invoked directly or referenced across agents.
   Removing them collapses the separation of concerns.

1. **Use a templating mechanism to inject artifact paths at install time** — considered:
   would allow per-consumer customisation. Not adopted now because it adds generator
   complexity. Revisit if consumer customisation becomes a first-class requirement
   (see orchestrated pipeline roadmap item).

## rationale

The install model assumes skills are drop-in procedures for any repository. Coupling them
to vstack's internal artifact layout creates an implicit dependency that is invisible to
consumers and breaks the design intent.

Agents are already the correct place for workflow-specific context: they declare their
scope, artifact contracts, and gate moments. Moving project-specific paths there makes the
coupling explicit, inspectable, and maintainable in one place.

## impact on orchestrated pipeline

In the orchestrated pipeline, each pipeline stage has declared input and output artifacts.
This decision aligns direct execution with that design: agents declare artifact contracts,
skills are stateless procedures. When the orchestrated pipeline is implemented, the agent
artifact declarations become the pipeline stage contracts without requiring skill changes.

## references

- [ADR-009: Role model](009-role-model.md)
- [ADR-010: Artifact hand-off pipeline](010-artifact-flow.md)
- [ADR-013: Policy vs procedure boundary](013-instructions-vs-skills-boundary.md)
- [ADR-004: Direct execution and orchestrated pipeline](004-option-a-to-b-pipeline.md)
