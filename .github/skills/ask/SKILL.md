---
name: ask
description: 'Read-only technical Q&A for the current codebase. Clarifies ambiguous questions, gathers evidence from code and docs, and returns concise, referenced answers without making any changes. Use for "how does this work", "where is X", "why might this fail", and "what should we do" guidance.'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and optional web lookup.'
metadata:
  owner: vstack
  maturity: stable
allowed-tools: 'read search web vscode'
argument-hint: '[question about code, architecture, behavior, or workflow]'
user-invocable: true
disable-model-invocation: false
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

# ask — Read-Only Technical Q&A

Answer questions clearly using evidence from the repository.
Do not edit files, run write operations, or apply changes.

## Out of scope

- Implementing fixes or refactors (route to `engineer`)
- Running destructive commands or state-changing operations
- Producing release artifacts (route to `release`)

## Workflow

1. Understand the question and classify it:
   - code behavior/explanation
   - architecture/ownership
   - debugging hypothesis
   - API usage/contract
   - process/tooling guidance
1. Identify what evidence is needed.
1. Gather evidence with focused search and minimal file reads.
1. Ask one clarification question if ambiguity blocks a reliable answer.
1. Respond with direct answer + evidence + actionable next steps.

## Clarification rule

If the question is ambiguous, ask exactly one focused question before deeper research.
Use options when useful and include a default assumption.

Example format:

- Question: Which path do you mean by "review flow"?
- Options: A) PR review lifecycle | B) code quality skill flow | C) release sign-off flow
- Default if no response: B

## Research strategy

Prefer broad-to-narrow exploration:

1. Find candidate areas quickly.
1. Narrow to specific symbols/functions/configs.
1. Read only files required to answer confidently.

Recommended commands:

```bash
rg -n "<topic-or-symbol>" src tests docs 2>/dev/null | head -120
rg --files src tests docs | head -200
```

When needed, inspect relevant runtime evidence:

```bash
# read-only diagnostics/examples
# terminal output snapshots or test failure summaries can be used as evidence
```

## Answer quality rules

- Lead with the answer, then provide evidence.
- Distinguish verified facts from assumptions.
- Reference concrete files and symbols for code-related questions.
- Keep answers concise but complete for the asked scope.
- If changes are needed, describe them but do not apply them.

## Output contract

Use this format:

```text
## Answer
[Direct answer in plain language]

## Evidence
- [file/symbol]: [what it shows]
- [file/symbol]: [what it shows]

## Recommended Next Step
- [single best next action]

## Confidence
[high/medium/low + one-line reason]
```

## Escalation guidance

- If the question requires implementation, hand off to `engineer` with a scoped summary.
- If it requires deep root-cause investigation, hand off to `debug`.
- If it requires risk/impact comparison, hand off to `analyse`.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"ask","artifact_type":"skill","artifact_version":"20260611001","generator":"vstack","vstack_version":"3.5.1"} -->
