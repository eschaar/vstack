---
name: analyse
description: 'Analyse impact, tradeoffs, causes, feasibility, risks, or change consistency without implementation or intent edits. Use for "analyse this", "compare approaches", or "review consistency". Return scoped findings with evidence.'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
allowed-tools: 'execute read search'
argument-hint: '[topic, change, or question to analyse]'
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

```bash
# Detect base branch (main / master / develop / trunk)
BASE=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null) \
  || BASE=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}') \
  || BASE=$(git branch -r 2>/dev/null | grep -E '/(main|master|develop|trunk)' | head -1 | sed 's|.*origin/||') \
  || BASE="main"
echo "Base branch: $BASE"
```

# analyse - Technical Analysis

Investigate impact, tradeoffs, feasibility, causes, risks, or change consistency.
Do not implement changes, rewrite acceptance, or run a verification fix loop.
Use `debug` for fixes, `performance` for profiling, `architecture`/`adr` for
decisions, and `verify` for implementation checks.

## Scope and evidence

Establish the question, scope, and known decisions from context. Ask only for
material missing information. Read relevant code, callers, contracts, baselines,
and data; do not launch a whole-repository audit by default.

Support findings with file locations, measured data, or explicit assumptions.
Inspect history and dependents when relevant; distinguish facts from hypotheses.

## Select relevant dimensions

| Analysis    | Questions                                                            |
| ----------- | -------------------------------------------------------------------- |
| Impact      | Dependents, blast radius, compatibility, migration, rollback?        |
| Tradeoff    | Complexity, performance, maintenance, cost, risk, effort per option? |
| Feasibility | Stack capability, limits, dependencies, blockers?                    |
| Cause       | Symptom, timeline, primary cause versus contributing factors?        |
| Risk        | Likelihood, impact, mitigation?                                      |
| Consistency | Do intent, acceptance, contracts, and useful tasks agree?            |

## Change-consistency review

Use before implementation when explicitly requested or justified by risk.
Read only relevant requirements, criteria, constraints, contracts, and tasks.
Identify:

- contradictions, including contracts conflicting with agreed behavior;
- uncovered obligations or vague, untestable criteria;
- proposed additions with no requirement or engineering rationale;
- artificial prerequisites inferred from task order or role names.

For each finding, give source, consequence, and proposed next action. Necessary
implementation details need not each be a product requirement. An unexplained
addition is a scope question, not permission to delete code. Do not silently
change intent, tasks, or implementation.

## Output

Return a compact response: question/scope, findings with evidence and impact,
recommendation, open questions, and confidence (`certain`, `probable`, `uncertain`).
For consistency reviews, use the response or an existing document when authorized;
no mandatory standalone report. A requested broader report may use the same
structure. Requirement quality and consistency findings are not behavioral proof.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"analyse","artifact_type":"skill","artifact_version":"20261026001","generator":"vstack","vstack_version":"4.0.0"} -->
