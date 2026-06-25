## handoff cache

Use `.vstack/memories/session/<RUN_ID>/` only to avoid replaying the same short-lived context across delegated calls.

- `RUN_ID` is any stable coordinating run id. In planner-led runs it is usually `PLANNER_RUN_ID`.
- The coordinator owns `index.md` and may assign one file per delegated agent: `<role>.md` or `<role>-<scope>.md` for parallel variants.
- A delegated agent reads `index.md` first, then only its assigned file, and writes only its own file.
- Keep only current-state bullets under `facts`, `decisions`, `open`, `next`.
- Replace stale bullets instead of appending history.
- Limits: `index.md` max 15 bullets; each role file max 10 bullets; 1 line per bullet.
- Never store transcripts, command logs, long excerpts, or duplicated file inventories.
