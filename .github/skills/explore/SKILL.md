---
name: explore
description: 'Fast codebase exploration and technical Q&A. Uses broad-to-narrow search, parallel context gathering, and depth modes (`quick`, `medium`, `thorough`) to map architecture, find reusable patterns, and answer targeted questions without making code changes. Use when asked to "explore the repo", "where is X implemented", "how does this system work", or "find examples to reuse".'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
allowed-tools: 'execute read search'
argument-hint: '[repository or system to explore]'
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

# explore — Fast Repository Exploration & Reuse Discovery

Answer codebase questions quickly and accurately.
Map architecture, find reusable patterns, and return targeted evidence.
Do not change files.

## Out of scope

- Implementing or fixing code (use `engineer`, `debug`, or `verify` workflows)
- Full architecture decisioning (use `architecture`)
- Deep security/performance audits (use `security` or `performance`)

## Operating modes

Choose depth based on user intent.

- `quick` (2-5 minutes): answer one focused question with minimal reads.
- `medium` (5-15 minutes): map the relevant subsystem and provide reuse candidates.
- `thorough` (15+ minutes): broader architecture map with risks, dependencies, and integration points.

If the user does not specify a depth, default to `medium`.

## Search strategy (broad -> narrow)

1. Start broad to find candidate areas quickly.
1. Narrow to concrete symbols, endpoints, and call paths.
1. Read only the files needed to answer confidently.
1. Stop when evidence is sufficient; avoid exhaustive sweeps by default.

Prefer parallel discovery for independent branches.
Examples:

- API layer + data layer + job/worker layer
- frontend feature + backend endpoint
- primary implementation + analogous implementation template

## Recommended command patterns

```bash
# 1) Inventory project shape quickly
ls -la
find . -maxdepth 3 \
  -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/vendor/*' \
  -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/.venv/*' \
  -not -path '*/__pycache__/*' | head -120

# 2) Locate likely implementation areas
rg --files | head -200
rg -n "router|endpoint|handler|service|repository|controller|usecase|workflow" src tests docs 2>/dev/null | head -120

# 3) Find symbol definitions/usages once a likely area is known
rg -n "<symbol-or-pattern>" src tests docs 2>/dev/null | head -120
```

Language and contract hints:

```bash
cat pyproject.toml 2>/dev/null | head -80 || true
cat package.json 2>/dev/null | head -80 || true
cat go.mod 2>/dev/null | head -80 || true
find . \( -name 'openapi*.yaml' -o -name 'openapi*.json' -o -name '*.proto' \) 2>/dev/null | head -40
```

## Reuse-first discovery

Always look for an existing analogous implementation before suggesting net-new structure.

For each candidate pattern, capture:

- where it lives (file + symbol)
- why it is analogous
- what can be reused directly
- what must be adapted

When asked to support implementation planning, return at least one "golden path" example and one fallback example.

## Evidence quality rules

- Prefer explicit evidence over assumptions.
- Cite concrete files and symbols, not only directories.
- Distinguish facts from inferences.
- If confidence is low, say what is missing and what to check next.

## Output contract

Tailor output to the requested depth, but keep this structure:

```text
## Exploration Result

### Answer
[Direct answer to the question in 2-6 sentences]

### Evidence
- [file/symbol]: [what it proves]
- [file/symbol]: [what it proves]

### Reusable Patterns
- [pattern A]: [why reusable, adaptation notes]
- [pattern B]: [why reusable, adaptation notes]

### Suggested Next Checks
- [targeted check 1]
- [targeted check 2]

### Confidence
[high/medium/low + one-line reason]
```

For `thorough` mode, append:

- subsystem map
- major dependency boundaries
- main risk hotspots (coupling, missing tests, unclear ownership)

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"explore","artifact_type":"skill","artifact_version":"20260611001","generator":"vstack","vstack_version":"3.6.0"} -->
