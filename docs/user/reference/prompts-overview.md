# Prompts Overview

This page lists prompt templates built into the installed vstack package and explains what they are for.

## What Prompts Are

Prompts are reusable review and analysis templates that guide a focused task.

In vstack, prompts are generated into `.github/prompts/*.prompt.md`.

Prompt files should stay model-agnostic by default. Leave `model` out unless a prompt has a specific, justified need to pin a model for reproducibility or model-specific behavior.

## Built-in Prompts

| Prompt               | Scope             | What It Helps With                                                                                  |
| -------------------- | ----------------- | --------------------------------------------------------------------------------------------------- |
| `api-design-review`  | `general-purpose` | Review an API design or OpenAPI spec for correctness, completeness, and consistency.                |
| `architecture-risk`  | `general-purpose` | Identify architectural risks, tradeoffs, and mitigation priorities for a proposed design.           |
| `artifact-integrity` | `vstack-internal` | Check source templates against generated artifacts and identify drift or missing regeneration.      |
| `ci-triage`          | `general-purpose` | Triage CI failures into root-cause clusters and prioritize the fastest safe recovery path.          |
| `quick-review`       | `general-purpose` | Review a change for bugs, regressions, and missing tests.                                           |
| `dependency-audit`   | `general-purpose` | Audit dependencies for vulnerabilities, outdated versions, licence risks, and supply chain hygiene. |
| `incident-timeline`  | `general-purpose` | Build a structured, evidence-based incident timeline and action-oriented postmortem summary.        |
| `migration-plan`     | `general-purpose` | Produce a safe migration plan with sequencing, fallback paths, and verification checkpoints.        |
| `migration-safety`   | `general-purpose` | Review database migration safety, rollback strategy, and zero-downtime risk.                        |
| `ops-readiness`      | `general-purpose` | Assess operational readiness across observability, runbooks, failure handling, and supportability.  |
| `release-check`      | `general-purpose` | Evaluate release gate readiness using required reports, artifacts, and sign-off evidence.           |
| `repo-assessment`    | `general-purpose` | Assess a repository for production-readiness gaps and prioritized improvements.                     |
| `template-impact`    | `general-purpose` | Assess impact of a template change on generated artifacts, tests, and release risk.                 |
| `test-gaps`          | `general-purpose` | Identify missing behavioral coverage and prioritize test additions by production risk.              |
| `upgrade-plan`       | `general-purpose` | Build a safe upgrade plan with sequencing, compatibility checks, and rollback points.               |
| `workflow-check`     | `general-purpose` | Review workflow stage flow, gate usage, and handoff integrity across role artifacts.                |

## Related Docs

- [Skills overview](skills-overview.md)
- [Instructions overview](instructions-overview.md)
- [Work items](work-items.md)
