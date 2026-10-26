---
name: requirements
description: 'Clarify requirements, constraints, and observable acceptance in the existing intent source. Use for "gather requirements", "define the spec", or "what are we building?". Keep change-local intent separate from shared system baselines.'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
allowed-tools: 'execute read search edit'
argument-hint: '[feature or system to document]'
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

# requirements - Requirements Gathering

Define what must be built and observable acceptance before engineering. Product
owns scope; architecture, design, roadmap planning, and implementation belong to
their respective roles.

## Choose the intent source

- System-level intent: `docs/product/requirements.md` on the branch.
- Change-local intent: the existing changedoc, not a separate specification.
- Small, clear, low-risk task: sufficient existing issue or conversation context.

Update shared baselines only when shared behavior or contracts change. Preserve
project gates and approvals regardless of task size; do not mandate every role.

## Clarify from evidence

1. Read relevant vision, requirements, roadmap, code, and recorded decisions first.
1. Identify the highest-impact uncertainty. Ask one focused question only when
   it materially affects correctness, scope, risk, or approval; no interview quota.
1. Record accepted answers in the existing intent source, or confirm them in chat.
   Do not repeat answered questions. State remaining assumptions and their risks.

## Define requirements

Capture only relevant dimensions:

| Dimension           | Record                                                                              |
| ------------------- | ----------------------------------------------------------------------------------- |
| Problem             | Who is affected, unmet need, and consequence                                        |
| Functional behavior | Must/should/won't-have outcomes, conditions, boundaries, and failure behavior       |
| Quality attributes  | Measurable performance/load, availability, security, scaling, or compliance targets |
| Constraints         | Required technology, integration, budget, deadline, and team limits                 |
| Acceptance          | Observable completion and how to check it                                           |
| Open questions      | Blocking decision, owner, and when needed                                           |

Use "The system must [behavior] under [condition]" where helpful. Keep outcomes
separate from technical choices unless a constraint requires them. Review
terminology, completeness, testability, and assumptions only for relevant scope.
A wording review is not proof that implementation works.

Prefer independently verifiable delivery slices when useful; do not force them
on small fixes or tightly coupled migrations. Reference relevant contracts and
data-lifecycle/operational constraints rather than copying them.

## Output and readiness

For system baselines, organize findings as Problem, Users, Functional Requirements,
Non-Functional Requirements, Constraints/Assumptions, Acceptance, and Open Questions.
For change-local work, maintain the corresponding existing sections.

Use stable local references when useful; no global IDs or duplicate prose.
Summarize scope, criteria, and blockers for the relevant owner. Implementation
requires understood scope, observable acceptance, resolved blocking questions,
and approval under project policy. After material revisions, reassess affected
tasks/evidence and renew approval only when scope, risk, or policy requires it.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"requirements","artifact_type":"skill","artifact_version":"20261026001","generator":"vstack","vstack_version":"4.0.0"} -->
