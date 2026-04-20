# ADR-013: Policy vs Procedure Boundary for Instructions and Skills

> Maintained by: **architect** role

**date:** 2026-04-20\
**status:** accepted

## context

vstack supports two reusable guidance mechanisms:

- Instructions (`.instructions.md`) with optional `applyTo` path matching.
- Skills (`SKILL.md`) that are invoked explicitly or auto-selected by task intent.

As vstack expands language and framework support, maintainers need a stable rule
for where guidance should live. Without an explicit boundary, the same content can
be duplicated or misplaced, leading to inconsistent behavior.

## decision

vstack adopts the following boundary:

1. **Instructions are policy.**

   Use instructions for always-on rules, coding standards, safety constraints,
   and repository conventions. Use `applyTo` when the policy is file-pattern scoped
   (for example `**/*.py`).

1. **Skills are procedures.**

   Use skills for task workflows, operational sequences, and specialist methods.
   Skills are optional and intent-driven; they do not replace baseline policy.

1. **Language-specific baseline policy may live in instructions.**

   This is valid when the guidance is a repository-wide coding standard for that
   language and should apply consistently across roles and workflows.

## alternatives considered

1. **Put all language/framework guidance in skills only.** Rejected.

   This would weaken baseline enforcement for repository coding standards and lose
   file-pattern matching advantages from `applyTo`.

1. **Put all procedure detail in instructions.** Rejected.

   This would reduce modularity and increase always-on context load.

1. **No explicit boundary.** Rejected.

   This causes authoring ambiguity and inconsistent guidance placement.

## rationale

The split aligns each mechanism with its strengths:

- Instructions provide predictable policy enforcement and path-scoped applicability.
- Skills provide modular, lazy, task-focused execution guidance.

This preserves both consistency (policy) and composability (procedures).

## consequences

### positive

- Clear authoring decision rule for new templates.
- Lower risk of duplicated or conflicting guidance.
- Better scaling for new language/framework additions.

### negative / tradeoffs

- Some topics may still require judgment when they include both policy and procedure.
- Documentation must be kept synchronized across design references.

### risks

- Overly broad instructions can still increase context size if not curated.
- Overly thin skills can become under-specified if policy and procedure are mixed.

## related ADRs

- ADR-011: skill restructure
- ADR-012: flat templates and install-time generation
