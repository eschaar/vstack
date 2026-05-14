# Prompts Overview

This page lists prompt templates built into the installed vstack package and explains what they are for.

## What Prompts Are

Prompts are reusable review and analysis templates that guide a focused task.

In vstack, prompts are generated into `.github/prompts/*.prompt.md`.

## Built-in Prompts

| Prompt               | What It Helps With                                                                                  |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| `api-design-review`  | Review an API design or OpenAPI spec for correctness, completeness, and consistency.                |
| `architecture-risk`  | Identify architectural risks, tradeoffs, and mitigation priorities for a proposed design.           |
| `artifact-integrity` | Check source templates against generated artifacts and identify drift or missing regeneration.      |
| `ci-triage`          | Triage CI failures into root-cause clusters and prioritize the fastest safe recovery path.          |
| `code-review`        | Review a change for bugs, regressions, and missing tests.                                           |
| `dependency-audit`   | Audit dependencies for vulnerabilities, outdated versions, licence risks, and supply chain hygiene. |
| `incident-timeline`  | Build a structured, evidence-based incident timeline and action-oriented postmortem summary.        |
| `migration-plan`     | Produce a safe migration plan with sequencing, fallback paths, and verification checkpoints.        |
| `migration-safety`   | Review database migration safety, rollback strategy, and zero-downtime risk.                        |
| `ops-readiness`      | Assess operational readiness across observability, runbooks, failure handling, and supportability.  |
| `release-check`      | Evaluate release gate readiness using required reports, artifacts, and sign-off evidence.           |
| `repo-assessment`    | Assess a repository for production-readiness gaps and prioritized improvements.                     |
| `template-impact`    | Assess impact of a template change on generated artifacts, tests, and release risk.                 |
| `test-gaps`          | Identify missing behavioral coverage and prioritize test additions by production risk.              |
| `upgrade-plan`       | Build a safe upgrade plan with sequencing, compatibility checks, and rollback points.               |
| `workflow-check`     | Review workflow stage flow, gate usage, and handoff integrity across role artifacts.                |

## Related Docs

- [Skills overview](skills-overview.md)
- [Instructions overview](instructions-overview.md)
- [Work items](work-items.md)
