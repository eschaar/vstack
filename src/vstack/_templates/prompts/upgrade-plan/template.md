Build a safe upgrade plan with sequencing, compatibility checks, and rollback points.

Use repository docs, manifests, and test constraints.

Output exactly in this format:

## Upgrade Scope

- target
- baseline version
- compatibility boundaries

## Step Plan

Ordered upgrade steps.

- step
- dependency/precondition
- success check

## Risk and Rollback

For each major step:

- risk
- trigger to rollback
- rollback action

## Verification Matrix

- check
- command
- pass criteria
