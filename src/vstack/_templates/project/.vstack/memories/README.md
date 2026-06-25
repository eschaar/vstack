# vstack handoff cache

This directory holds a small run-scoped cache for coordinated agent delegation.

## purpose

Use `.vstack/memories/session/<RUN_ID>/` only to avoid replaying the same short-lived
context between agents and subagents.

In planner-led runs, `RUN_ID` is usually `PLANNER_RUN_ID`.

This cache is not a source of truth.

- Durable truth stays in role-owned docs, reports, and code.
- `.vstack/vstack.json` remains the only machine-generated install manifest.

## layout

```text
.vstack/memories/
├── README.md
└── session/
    └── <PLANNER_RUN_ID>/
        ├── index.md
        ├── product.md
        ├── architect.md
        ├── designer.md
        ├── engineer.md
        ├── tester.md
        └── release.md
```

Same-role parallel variants must use distinct names such as `tester-security.md` and
`tester-performance.md`.

## compact format

Keep only these sections:

- `facts`
- `decisions`
- `open`
- `next`

Rules:

1. Use one line per bullet.
1. Replace stale bullets instead of appending history.
1. Keep `index.md` at 15 bullets max.
1. Keep each role file at 10 bullets max.
1. Do not paste transcripts, command output, long excerpts, or repeated file lists.

Example:

```markdown
# engineer

facts:
- failing check is limited to install gitignore coverage

decisions:
- keep session cache ephemeral and gitignored

open:
- none

next:
- run targeted install tests
```

## git policy

`.vstack/memories/session/` is ignored by the generated `.vstack/.gitignore`.
Commit this README, not the session cache.
