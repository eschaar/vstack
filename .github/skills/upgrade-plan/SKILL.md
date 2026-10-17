---
name: upgrade-plan
description: 'Build a safe upgrade plan with sequencing, compatibility checks, and rollback points.'
allowed-tools: 'read search'
argument-hint: '[target version, component, or full repo]'
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

# upgrade-plan - Upgrade Planning

Build a safe upgrade plan with sequencing, compatibility checks, and rollback points.
Plan only; do not install packages, apply upgrades, or change files.

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

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"upgrade-plan","artifact_type":"skill","artifact_version":"20261017001","generator":"vstack","vstack_version":"3.7.8"} -->
