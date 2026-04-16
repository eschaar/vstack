---
name: unfreeze
description: 'Remove a directory edit lock. Use after freeze when you want to allow edits again.'
argument-hint: '[path to unfreeze]'
disable-model-invocation: true
---
## Skill Context

This skill is part of **vstack** — a VS Code-native AI engineering workflow system.

### Completeness Principle

AI-assisted coding compresses implementation time 10–100x. When evaluating "approach A (100%, full implementation) vs approach B (90%, shortcut)", **prefer A**. The delta costs seconds with AI assistance. "Ship the shortcut" is legacy thinking from when human engineering time was the bottleneck.

### AskUserQuestion Format

When you need clarification, use this exact format — never invent or guess:

> **Question:** [The specific question]
> **Options:** A) … | B) … | C) …
> **Default if no response:** [What you'll do]

Never ask more than one question at a time without waiting for the answer.

### Repo Context

```bash
# Determine project and branch context
git rev-parse --show-toplevel 2>/dev/null | xargs basename || echo "unknown-project"
git branch --show-current 2>/dev/null || echo "unknown-branch"
```

# unfreeze — Remove Directory Edit Lock

Remove a previously activated directory freeze.

## Out of scope

- Activating a freeze (use `freeze`)
- Disabling careful mode (ask to "disable guardrails")

---

Parse the user's request for the path to unfreeze.

If no path was specified and there are active freezes, list them:
> **Question:** Which directory should I unfreeze?
> **Options:** A) [list frozen paths] | B) Unfreeze all
> **Default if no response:** Ask again

Once confirmed:

```text
✓ UNFROZEN: [path]

Edit restrictions on [path] have been removed.
```

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
