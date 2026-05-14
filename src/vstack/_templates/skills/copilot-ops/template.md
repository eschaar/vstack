{{SKILL_CONTEXT}}

# copilot-ops - Copilot Governance Operations

Run Copilot governance changes safely with evidence, rollback intent, and verification.

## When to use

- Audit Copilot governance settings before release or compliance review
- Apply policy updates for repository or organization scope
- Investigate configuration drift between expected and actual Copilot controls

## Procedure

1. Capture current scope (repo/org/enterprise) and required permissions.
1. Pull current Copilot-relevant settings and record baseline evidence.
1. Compare baseline with expected policy and identify drift.
1. Propose minimal changes with explicit risk notes.
1. Apply approved changes using audited commands/workflows.
1. Re-read settings and confirm effective state.
1. Log follow-up checks and ownership.

## Output format

Provide this structure:

### Baseline

- scope reviewed
- settings checked
- evidence source

### Drift Findings

- setting
- expected value
- current value
- risk

### Change Plan

- proposed change
- approval needed
- rollback note

### Verification

- post-change check
- result
- residual risk

## Escalation

Escalate when permissions are insufficient, settings conflict across scopes, or policy intent is ambiguous.
