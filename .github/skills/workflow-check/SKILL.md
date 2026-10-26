---
name: workflow-check
description: 'Review workflow stage flow, gate usage, and handoff integrity across role artifacts.'
allowed-tools: 'read search'
argument-hint: '[workflow scope or stage list]'
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

# workflow-check - Workflow Contract Audit

Review workflow stage flow, gate usage, and handoff integrity across role artifacts.
Report only; do not change workflow configuration or role artifacts.

Focus on the current project's workflow configuration, installed agent files,
role documents, and handoff definitions. These are consumer-project artifacts;
the vstack source repository and its template directories are not required.

Output exactly in this format:

## Flow Summary

- workflow scope
- current stage order
- gate model used

## Gate and Handoff Findings

For each finding:

- location: file path and section
- issue: one sentence
- impact: what can fail in execution
- fix: concrete correction

## Blocking Risks

List only issues that block reliable workflow execution.

- blocker
- owner role
- required action

## Recommended Next Steps

Provide an ordered short list of actions.

- action
- owner role
- expected result

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"workflow-check","artifact_type":"skill","artifact_version":"20261017002","generator":"vstack","vstack_version":"4.0.0"} -->
