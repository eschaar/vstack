{{SKILL_CONTEXT}}

# migration-plan - Cross-Component Migration Planning

Produce a safe migration plan with sequencing, fallback paths, and verification checkpoints.
Plan only; do not apply migrations or change files.

Use source changes, schema/contracts, and deployment constraints.

Output exactly in this format:

## Migration Overview

- scope
- dependencies
- compatibility strategy

## Execution Plan

For each phase:

- phase
- changes applied
- validation checkpoint

## Rollback Plan

For each phase:

- rollback trigger
- rollback steps
- data integrity check

## Post-Migration Validation

- required tests
- smoke checks
- success criteria
