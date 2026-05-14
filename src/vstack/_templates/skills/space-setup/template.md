{{SKILL_CONTEXT}}

# space-setup - Copilot Space Setup and Maintenance

Set up a project Space that keeps Copilot context focused, current, and easy to audit.

## When to use

- New repository onboarding to Copilot Spaces
- Space quality cleanup after major docs or architecture updates
- Regular context refresh before a release cycle

## Procedure

1. Define Space objective and audience.
1. Select core sources: requirements, architecture, design, README, and key ADRs.
1. Exclude noisy/generated paths and duplicate docs.
1. Create or update the Space using GitHub UI (or approved API workflow).
1. Validate discoverability: each key topic maps to at least one source document.
1. Record refresh cadence and owner.
1. Re-check after `vstack install` or release docs updates.

## Output format

Provide this structure:

### Space Scope

- objective
- audience
- included sources
- excluded sources

### Setup Actions

- action taken
- rationale
- owner

### Quality Findings

- missing context
- stale context
- duplicate/noisy context

### Maintenance Plan

- refresh trigger
- cadence
- owner

## Escalation

Escalate when required docs are missing, stale, or inconsistent across product/architecture/design baselines.
