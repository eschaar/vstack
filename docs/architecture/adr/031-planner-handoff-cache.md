# ADR-031: Coordinator Handoff Cache

> Maintained by: **architect** role

**date:** 2026-06-25\
**status:** accepted

## context

Coordinated runs already use file-based handoff between roles through role-owned
artifacts. That works well for durable outputs, but repeated delegated calls in a
single run still tend to replay the same short-lived context:

- current blockers
- accepted plan slice
- small decision deltas
- what each parallel branch has already learned

Reconstructing that context in every prompt wastes tokens and increases drift risk.
The problem is strongest when a coordinating agent fans out independent branches or
same-role variants in parallel.

We need a small coordination layer that:

1. stays native to VS Code and file-based orchestration
1. supports parallel worker branches safely
1. reduces repeated prompt context
1. does not become a second durable artifact system

## decision

Introduce a **run-scoped coordinator handoff cache** under:

```text
.vstack/memories/session/<RUN_ID>/
```

The cache is a disposable coordination aid for one planner run only.

### ownership

- The coordinating agent owns `index.md`.
- Each worker or same-role variant owns exactly one file:
  - `<role>.md`
  - `<role>-<scope>.md` for same-role parallel variants

### content contract

Each cache file keeps only current-state bullets in these sections:

- `facts`
- `decisions`
- `open`
- `next`

Rules:

1. Replace stale bullets instead of appending history.
1. Keep one line per bullet.
1. Keep files compact: planner `index.md` at 15 bullets max; worker files at 10 bullets max.
1. Do not store chat transcripts, command logs, large artifact excerpts, or duplicated file inventories.
1. Durable truth remains in role-owned docs, reports, code, and manifest state.

### git policy

`.vstack/memories/session/` is gitignored by the generated `.vstack/.gitignore`.

`.vstack/memories/README.md` is committed so the protocol is discoverable and stable.

## alternatives considered

### Option A: No cache, pass full context every time

**Pros:** No new convention.

**Cons:** Repeats short-lived coordination context in each delegated prompt; higher token use;
more opportunity for branch drift in parallel work.

**Why rejected:** The overhead is real in coordinated multi-stage runs.

### Option B: Make cache files durable project artifacts

**Pros:** Full traceability across runs.

**Cons:** Promotes ephemeral coordination notes into long-lived project state; encourages
large files; duplicates role-owned artifacts.

**Why rejected:** This would create a second source of truth.

### Option C: Add a dedicated runtime service or database

**Pros:** Could support locking, indexing, and richer state queries.

**Cons:** Violates the VS Code-native, file-based operating model and adds operational complexity.

**Why rejected:** The coordination problem does not justify new runtime infrastructure.

## rationale

This is the lazy solution that fits the current architecture.

- It reuses the existing file-based coordination model.
- It keeps the coordinating agent thin.
- It supports parallel branches by assigning one owner per file.
- It reduces repeated prompt payloads without introducing a new subsystem.

The protocol is intentionally small and disposable so it does not compete with durable
artifacts or repository memory.

## impact on future orchestrated pipeline

- Coordinator prompts can pass a cache path instead of replaying the same coordination prose.
- Same-role parallel variants need a distinct scope suffix to avoid write conflicts.
- Future automation may prune stale run directories, but pruning is operational hygiene,
  not a precondition for the protocol.
