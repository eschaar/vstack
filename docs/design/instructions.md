# vstack — instructions

> Maintained by: **designer** role\
> Last updated: 2026-04-20

## what are instructions?

Instructions are repository guidance files (`*.instructions.md`) loaded by Copilot
to apply baseline rules. They are policy-oriented and can be scoped with `applyTo`
patterns.

Examples:

- Global safety and credential handling policy.
- Git and release hygiene policy.
- Language-specific coding standards that should apply to all changes in that language.

______________________________________________________________________

## policy vs procedure boundary

vstack uses an explicit split:

- **Instructions = policy** (always-on rules and standards).
- **Skills = procedure** (task execution workflows).

Canonical decision record:
[013-instructions-vs-skills-boundary.md](../architecture/adr/013-instructions-vs-skills-boundary.md).

Use instructions when guidance is:

- expected on every applicable change,
- independent from a specific task flow,
- naturally expressed as constraints and conventions.

Use skills when guidance is:

- a step-by-step operational process,
- optional or intent-driven,
- specialized to one type of task (for example debug, migrate, performance).

______________________________________________________________________

## applyTo patterns

`applyTo` scopes an instruction to matching files.

Examples:

- `**/*.py` for Python policy.
- `**/*` for repo-wide policy.

`applyTo` is for policy targeting, not for procedural automation.

______________________________________________________________________

## file locations

| Path                                                    | Purpose                                                   |
| ------------------------------------------------------- | --------------------------------------------------------- |
| `src/vstack/_templates/instructions/<name>/config.yaml` | Source of truth: instruction metadata and `applyTo` scope |
| `src/vstack/_templates/instructions/<name>/template.md` | Source of truth: instruction body                         |
| `.github/instructions/<name>.instructions.md`           | Generated output loaded by Copilot                        |

Never edit generated `.github/instructions/` directly in the source repository.
Regenerate with `python3 -m vstack install` after template changes.

______________________________________________________________________

## minimum instruction contract

Each instruction should include:

1. Clear applicability and intent.
1. Concrete rules, not broad aspirations.
1. Safety constraints where relevant.
1. Alignment with repository automation (CI, release policy, security policy).
