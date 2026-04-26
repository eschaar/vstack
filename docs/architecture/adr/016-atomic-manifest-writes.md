# ADR-016: Atomic Manifest Writes

> Maintained by: **architect** role

**date:** 2026-04-26\
**status:** accepted

## context

`vstack.json` is the manifest that records every file vstack has installed in a
project. It is read by `verify`, `status`, `uninstall`, and `install --update`.
If the manifest is corrupt or truncated, these commands cannot function correctly
and manual repair is required.

Before this change, `ManifestFile.write()` called `Path.write_text()` directly:

```python
path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
```

`write_text` is not atomic. A crash, `KeyboardInterrupt` (Ctrl+C), `SIGTERM`, or
an OS-level flush failure between the open and the close could leave `vstack.json`
in a partially-written state — truncated, incomplete JSON, or an empty file.

The question was: how should we eliminate this class of corruption without adding
a runtime dependency or significant implementation complexity?

## decision

`ManifestFile.write()` stages the serialized manifest to a sibling file
`vstack.json.tmp` and then atomically promotes it via `os.replace()`:

```python
tmp = self.path.with_suffix(".tmp")
tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
os.replace(tmp, self.path)
```

`os.replace` is guaranteed atomic on POSIX when source and destination are on the
same filesystem (which they always are for a `.tmp` sibling), so `vstack.json` is
either the old content or the new content — never a partial write.

A stale `.tmp` file from a previous crash is silently overwritten by the next
successful write. No cleanup step is required.

## alternatives considered

### Option A: Write-and-verify (read back after write)

Write the file, then read it back and compare against the intended content. If they
differ, raise an error.

**Pros:** Catches write failures.

**Cons:** Does not prevent partial writes from appearing from the perspective of
another concurrent reader between the write and the verify. Does not help on a
crash that happens after write and before verify. Adds a read I/O on every write.

**Why rejected:** Does not eliminate the atomic-write problem; only detects it
after the fact.

### Option B: Backup before write

Copy the current `vstack.json` to `vstack.json.bak` before writing.

**Pros:** Gives users a recovery path after a crash.

**Cons:** Requires users to know to look for and use `.bak`. Still leaves `vstack.json`
potentially corrupt after the crash. Does not eliminate the need for manual
intervention.

**Why rejected:** Shifts recovery burden to users rather than eliminating the
failure mode.

### Option C: Accept the risk of partial writes

Trust that modern OS buffering and Python's flush-on-close behaviour make partial
writes rare in practice.

**Cons:** A partial write during `vstack install` leaves the project in a state where
`vstack verify`, `vstack status`, and `vstack uninstall` all fail with a JSON parse
error and there is no automated recovery path. The failure is silent (no error from
the install command itself) and the root cause is non-obvious.

**Why rejected:** The consequence of a partial write is severe and non-obvious. The
fix is a trivial code change. Accepting the risk would be negligent given a simple
remedy exists.

### Option D: `os.replace` via sibling `.tmp` file (chosen)

See the decision above.

**Why chosen:** `os.replace` is specified as atomic in POSIX.1-2008. No external
library is required. The implementation adds three lines of code. Stale `.tmp` files
are self-cleaning. The approach is a well-established pattern in systems programming.

## rationale

Eliminating an entire class of manifest corruption with three lines and zero new
dependencies is the correct tradeoff. The `os.replace` POSIX guarantee is
well-documented and widely relied upon. The alternative approaches either shift
recovery burden to users or detect failures too late.

NFR-3 explicitly requires atomic manifest writes; this ADR records the implementation
decision that satisfies it.

## consequences

### positive

- `vstack.json` is never left in a partially-written state on POSIX systems.
- No new dependencies introduced.
- `.tmp` cleanup is implicit (next write overwrites any stale `.tmp`).

### negative / tradeoffs

- On Windows, `os.replace` is not guaranteed atomic (it is atomic on POSIX only).
  vstack's primary target is POSIX (Linux, macOS) CI environments; Windows is
  best-effort for now.
- A stale `.tmp` file may be visible in the directory listing if a write is
  interrupted between `write_text` and `os.replace`. It will be cleaned up on the
  next successful write.

## impact on future orchestrated pipeline

No direct impact. If a future multi-role pipeline introduces parallel artifact writes,
each manifest write must still go through `ManifestFile.write()` to preserve the
atomicity guarantee. Concurrent writes from multiple processes to the same
`vstack.json` would require an additional locking mechanism not covered here.
