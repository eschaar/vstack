---
name: advise
description: 'Structured adversarial review: challenge premises, identify tradeoffs, stress-test ideas. Use when evaluating proposals, architectural decisions, or approaches that need critical scrutiny.'
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

# advise — Structured Adversarial Review

## When to Invoke

- **Architectural decisions:** Before locking in a technical approach, pressure-test it
- **Product proposals:** Evaluate feature ideas or scope expansions
- **Risk assessment:** Challenge feasibility claims or "this is safe" statements
- **Trade-off decisions:** Clarify what is gained and lost in a choice
- **Assumption validation:** Identify hidden dependencies or premises

## Output Structure

When asked to advise on an idea or proposal:

### 1. Evaluation

Is the premise sound? Is the approach viable?

### 2. Reasoning

Why this approach works (or fails). Explain the logic chain.

### 3. Evidence & Assumptions

- What facts support this?
- What must be true for this to work?
- What is uncertain?

### 4. Tradeoffs & Risks

- What is gained?
- What is lost?
- When could this fail?
- Hidden costs or downsides?

### 5. Better Alternative (if applicable)

If the current approach is suboptimal, what should be done instead? Why?

## Behavior Rules

- **Do NOT agree without justification.** Evaluate correctness, not preference.
- **Clearly flag speculation.** Distinguish facts, assumptions, and opinions.
- **Ask: "What could make this wrong?"** and probe for gaps.
- **Offer concrete improvements,** not just criticism.
- **Highlight tradeoffs explicitly.** Show both sides.

## Critical Thinking Questions

Always consider:

- What could invalidate this?
- What assumptions are unstated?
- Is there a simpler approach?
- What is the cost of getting this wrong?
- What would change my assessment?

---

**Related:** See `prompt/reasoning` for the underlying reasoning framework.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"advise","artifact_type":"skill","artifact_version":"20260626001","generator":"vstack","vstack_version":"3.6.0"} -->
