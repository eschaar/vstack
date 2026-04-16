# ADR-011: Skill Restructure (rename, new, retire)

> Maintained by: **agents** role

**date:** 2026-03-28\
**status:** accepted — implementation planned for v0.5.0

## context

With the 6-role model (ADR-009) defined, the existing skill set of 19 skills
needs to be aligned to:

1. Reflect the names that backend teams actually use
1. Map clearly to specific roles and output artifacts
1. Remove skills that are better expressed as role behaviors

Several existing skills have names that don't align with role ownership
or carry ambiguous scope (e.g., `design-consult`, `experience`, `discovery`).

## decision

### renames

| old name         | new name  | reason                                                            |
| ---------------- | --------- | ----------------------------------------------------------------- |
| `experience`     | `consult` | "experience" implies UX; "consult" better describes design review |
| `design-consult` | `design`  | the skill IS the design step; "consult" was redundant             |
| `docs-release`   | `docs`    | simpler, more general                                             |
| `discovery`      | `explore` | "explore" is action-oriented and less survey-tool-specific        |

### new skills (v0.5.0)

| skill          | owned by  | output                           |
| -------------- | --------- | -------------------------------- |
| `requirements` | product   | `docs/product/requirements.md`   |
| `adr`          | architect | `docs/architecture/adr/NNN-*.md` |
| `analyse`      | any       | structured analysis report       |

### skills to retire (become documentation, not skills)

| skill         | disposition                                          |
| ------------- | ---------------------------------------------------- |
| `guardrails`  | Inline note in tester/release workflow documentation |
| `freeze`      | Inline note in engineer/architect agent file         |
| `unfreeze`    | Inline note in engineer/architect agent file         |
| `orchestrate` | Responsibility moves to product + release roles      |

## alternatives considered

1. Keep all names — rejected because `design-consult` and `experience` cause
   confusion when mapping to roles.
1. Delete utility skills immediately — deferred to v0.5.0 to avoid breaking
   existing workflows.

## rationale

Clarity over backward compatibility for internal skills. Prefer the final vstack
vocabulary over carrying legacy naming layers.

## impact on future orchestrated pipeline

Pipeline stage names remain stable (product, architect, designer, engineer,
tester, release). Skill renames are internal to role execution.
