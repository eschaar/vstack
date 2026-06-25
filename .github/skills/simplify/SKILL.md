---
name: simplify
description: 'Generic simplification skill for any role. Removes unnecessary scope, complexity, and moving parts while preserving required outcomes, correctness, safety, and maintainability.'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
allowed-tools: 'execute read search edit'
argument-hint: '[proposal, plan, or change request to simplify]'
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

# simplify - Outcome-First Simplification

Simplify proposals, plans, and changes by removing unnecessary scope and
complexity while preserving required outcomes, safety, and quality.

This skill is role-agnostic and can be used by any agent.

## Use this when

- A proposal includes too many moving parts.
- A plan looks harder than the problem requires.
- A change can likely be solved with fewer artifacts, steps, or dependencies.

## Non-negotiables

Never simplify away:

- Required outcomes and acceptance criteria
- Security, compliance, and trust-boundary controls
- Safety checks for destructive or irreversible operations
- Critical observability and error handling
- Explicit architectural or contract constraints

If simplification would violate any non-negotiable, keep that part intact and
simplify elsewhere.

## Simplification ladder

Stop at the first level that preserves all required outcomes.

1. **Clarify**: Remove ambiguity and redundant requirements.
1. **De-scope**: Remove nice-to-have scope that does not affect required outcomes.
1. **Reuse**: Reuse existing contracts, components, workflows, and patterns.
1. **Collapse**: Merge duplicate steps, layers, or handoffs.
1. **Reduce**: Minimize new logic, artifacts, dependencies, and surface area.
1. **Refine**: Keep only the smallest complete solution.

## Procedure

## Step 0 - Define essentials

Capture the minimum set that must remain true:

- Required outcome
- Hard constraints
- Quality and safety expectations

Output:

```text
Essentials:
- Outcome: ...
- Constraints: ...
- Safety/quality gates: ...
```

## Step 1 - Simplify with evidence

For each ladder level, record what changed and why it is safe:

```text
Level 1 (Clarify): [change] - [evidence]
Level 2 (De-scope): [change] - [evidence]
...
Chosen level: [N]
```

Prefer concrete repository or spec evidence over assumptions.

## Step 2 - Produce the simplified version

Return a simplified proposal/plan/change with:

- Fewer moving parts
- Fewer assumptions
- Clearer ownership and flow
- Same required outcomes

## Step 3 - Validate equivalence of intent

Confirm the simplified version still satisfies essentials:

- Outcome preserved
- Constraints respected
- Safety/quality gates preserved
- No hidden risk introduced

## Output contract

```text
## Simplify Report

Original scope:
[short summary]

Simplified scope:
[short summary]

What was removed or merged:
- ...
- ...

What was intentionally kept:
- ...

Why this is still safe:
- ...

Residual risk:
- none | [risk + mitigation]
```

## Escalation rules

Escalate instead of over-simplifying when:

- Constraints conflict and require a policy decision.
- Simplification changes approved architecture or external contracts.
- Safety, compliance, or legal obligations are unclear.
- Required outcomes are underspecified.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"simplify","artifact_type":"skill","artifact_version":"20260625001","generator":"vstack","vstack_version":"3.6.0"} -->
