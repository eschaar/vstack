---
name: freeze
description: 'Lock a directory from edits for the current session. Any attempt to edit files in the frozen path will be refused. Use when you want to prevent accidental modification of stable, shared, or generated code.'
argument-hint: '[path to freeze]'
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

# freeze — Directory Edit Lock

Lock a directory to prevent accidental edits during this session.

## Out of scope

- Session-wide careful mode for destructive commands (use `guardrails`)
- Removing a freeze (use `unfreeze`)
- Permanent file permissions (this is session-local only)

---

Parse the user's request for the path to freeze.

If no path was specified:
> **Question:** Which directory should I freeze?
> **Options:** A) Specify the path | B) Freeze the current directory | C) List directories to choose
> **Default if no response:** Ask again

Once the path is confirmed:

```text
⛔ FROZEN: [path]

I will not edit any files under [path] until you run the unfreeze skill.
This is a hard block, not a warning. If you ask me to edit a frozen file,
I will refuse and explain how to unfreeze it.
```

**To unfreeze:** Use the `unfreeze` skill.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
