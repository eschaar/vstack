---
name: migration-plan
description: 'Produce a safe migration plan with sequencing, fallback paths, and verification checkpoints.'
allowed-tools: 'read search'
argument-hint: '[migration scope or affected components]'
user-invocable: true
disable-model-invocation: true
---
## Skill Context

This skill is part of **vstack** — a VS Code-native AI engineering workflow system.

### AskUserQuestion Format

When you need clarification, use this exact format — never invent or guess:

> **Question:** [The specific question]
> **Options:** A) … | B) … | C) …
> **Default if no response:** [What you'll do]

Never ask more than one question at a time without waiting for the answer.

### Diagram Convention

When producing hand-authored Markdown outputs, prefer Mermaid for flow,
interaction, lifecycle, state, topology, dependency, and decision diagrams when
the format is supported and improves clarity. Use ASCII as a fallback when
Mermaid is unsupported or would be less readable. Keep ASCII/text trees for
directory structures and other scan-friendly hierarchies.

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

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"migration-plan","artifact_type":"skill","artifact_version":"20261017001","generator":"vstack","vstack_version":"4.0.0"} -->
