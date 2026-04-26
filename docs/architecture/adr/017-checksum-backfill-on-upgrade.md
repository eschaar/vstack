# ADR-017: Checksum Backfill During Manifest Upgrade

> Maintained by: **architect** role

**date:** 2026-04-26\
**status:** accepted

## context

Manifest v2 (ADR-014) introduced per-artifact `checksum` and `checksum_algorithm`
fields. The `vstack manifest upgrade` command migrates legacy manifests to the v2
schema: it promotes `manifest_version` to `2`, sets `hash_algorithm`, and infers
`checksum_algorithm` for entries that already carry a checksum but lack an explicit
algorithm field. It does not backfill checksums for entries that have no checksum
at all.

Projects that installed artifacts before checksum tracking was introduced have a
manifest where every `ArtifactEntry` has `checksum: None`. After running
`manifest upgrade`, the schema version is current but all entries still lack
checksums. The CLI classifies these entries as `MANAGED_LEGACY`:

```text
classify_state():
  if existing_entry.checksum is None:
    return MANAGED_LEGACY, "<path>: tracked legacy entry without checksum; treated as managed"
```

`MANAGED_LEGACY` has three material consequences:

1. **`status`** — reports all tracked files as legacy warnings rather than clean.
1. **`verify --output`** — accepts legacy entries as pass but cannot detect drift.
1. **`install --update`** — cannot compute drift, so it cannot determine whether a
   file is safe to overwrite under the conservative default (ADR-015). The conservative
   update is blocked for every legacy entry.

The question is: should `vstack manifest upgrade` optionally compute and store
checksums for tracked files that currently lack them, resolving these consequences?

## decision

`vstack manifest upgrade` accepts an optional `--backfill` flag.

When `--backfill` is set:

1. For each tracked artifact entry that has no checksum, locate the on-disk file at
   the expected relative path under the install root.
1. If the file exists and contains a `VSTACK-META` footer comment, compute its
   SHA-256 checksum and store it in the upgraded entry alongside
   `checksum_algorithm: "sha256"`.
1. If the file exists but lacks a `VSTACK-META` footer (unverifiable identity), skip
   backfill for that entry and emit a warning. The entry retains `MANAGED_LEGACY`
   status after upgrade.
1. If the file does not exist on disk, skip silently — the entry is already `MISSING`
   and no checksum is meaningful.
1. The manifest is written atomically after all entries are processed (ADR-016).

When `--backfill` is not set, `manifest upgrade` behavior is unchanged: schema-only
upgrade. **The `--backfill` flag is explicitly opt-in. There is no default backfill.**

### upgrade behaviour table

| Condition                                     | Without `--backfill` | With `--backfill`           |
| --------------------------------------------- | -------------------- | --------------------------- |
| Entry has checksum, no algorithm              | Infer algorithm      | Infer algorithm (unchanged) |
| Entry has no checksum, file exists + footer   | No change            | Compute + store SHA-256     |
| Entry has no checksum, file exists, no footer | No change            | Skip; emit warning          |
| Entry has no checksum, file missing           | No change            | Skip silently               |

The `VSTACK-META` footer is the machine-readable comment appended to every
generated artifact:

```text
<!-- VSTACK-META: {"artifact_name":"…","artifact_type":"…","artifact_version":"…","generator":"vstack","vstack_version":"…"} -->
```

Its presence is the identity gate. Absence means the file is either user-created,
pre-footer vstack output, or so heavily modified that the footer was removed.

## alternatives considered

### Option A: Eager unconditional backfill (no flag, always backfill on upgrade)

During `manifest upgrade`, unconditionally compute checksums for all tracked files
found on disk, regardless of identity check.

**Pros:** Zero friction — a single command resolves all `MANAGED_LEGACY` warnings.

**Cons:** If a tracked file has been locally modified after install, the backfill
stores the modified state as canonical. Future `install --update` then sees the file
as `MANAGED` (clean) and overwrites the modified content — a silent violation of
the conservative-install guarantee in ADR-015.

**Why rejected:** Silently promoting a modified file to clean state is a correctness
violation. An upgrade command that accepts arbitrary on-disk state as authoritative
without any user acknowledgement is unsafe.

### Option B: No backfill — leave MANAGED_LEGACY entries indefinitely

Schema upgrade only. Users who want checksums must re-run `vstack install --force`
to reinstall artifacts from source and record fresh checksums.

**Pros:** No risk of incorrectly canonicalising a modified file.

**Cons:** `MANAGED_LEGACY` persists indefinitely after upgrade. All tracked files
remain blocked from `install --update`. Users who want a clean status report must
force-reinstall every artifact — which overwrites local customisations and itself
violates ADR-015. This is a chicken-and-egg situation: conservative install needs
checksums, but the only path to checksums requires destructive overwrite.

**Why rejected:** Forces destructive re-install as the only exit from `MANAGED_LEGACY`.
Incompatible with the conservative-install contract for projects with local
customisations.

### Option C: Separate `vstack manifest backfill` command

Introduce a new sub-command `vstack manifest backfill` with an identity-check flag.
Upgrade remains schema-only; backfill is a distinct step.

**Pros:** Clean command separation. Backfill intent is maximally explicit.

**Cons:** Requires two commands to fully recover from legacy state. Most users want
both in sequence; splitting them into two commands adds no clarity beyond a flag on the
existing upgrade command. Adds a permanent command-catalogue entry for a one-time
migration operation.

**Why rejected:** The marginal clarity benefit does not justify the additional
command surface. A flag on the existing upgrade command is equally explicit and
simpler to document.

### Option D: Opt-in flag with identity check (chosen)

`vstack manifest upgrade --backfill` with `VSTACK-META` footer verification.

See the decision above.

**Why chosen:** Explicit user intent (opt-in flag). The `VSTACK-META` footer is a
reliable identity signal — only vstack writes it, and user-customised files rarely
strip the footer while retaining the surrounding content. The flag is one extra
argument that users supply once, not a recurring cost. The identity check is a
meaningful guard without requiring a separate command or complex heuristics.

## rationale

Safe-by-default is the governing constraint (ADR-015). An opt-in flag preserves it:
the user explicitly chooses to canonicalise current on-disk state. The `VSTACK-META`
footer check is lightweight but meaningful — it screens out files that were never
vstack-generated and files whose footers were removed as part of heavy
customisation.

The check is an identity guard, not a modification guard. A user-modified file that
still carries the original `VSTACK-META` footer will have its modified content
checksummed and stored. This is documented behaviour: `--backfill` canonicalises
current state. Users who have modified files and need accurate drift detection
should run `vstack install --force-name <name>` for those artifacts after backfill,
not use backfill as a substitute for a fresh install.

The result after a successful `--backfill` run is a manifest where every tracked file
that exists on disk and passes identity verification is classified as `MANAGED`, not
`MANAGED_LEGACY`. Conservative install (`--update`) then operates correctly for those
entries.

## consequences

### positive

- After `vstack manifest upgrade --backfill`, tracked files with `VSTACK-META` footers
  are promoted from `MANAGED_LEGACY` to `MANAGED`.
- `status` no longer shows legacy warnings for those entries.
- `verify --output` can detect drift for those entries.
- `install --update` operates correctly for those entries.
- Entries without `VSTACK-META` footers continue to report `MANAGED_LEGACY`, which is
  the correct conservative signal for files whose vstack origin is unverifiable.

### negative / tradeoffs

- `--backfill` canonicalises current on-disk state. Modified content that retains the
  `VSTACK-META` footer is accepted as canonical — drift is no longer detectable for
  that entry until a fresh install records a new checksum.
- The `VSTACK-META` footer check is a heuristic, not a cryptographic proof of origin.
  A manually crafted file with a forged footer would pass the check. This is an
  acceptable risk in a developer tooling context.
- Entries that lack the `VSTACK-META` footer remain `MANAGED_LEGACY` after backfill
  and continue to block conservative `--update`. Users with such entries must use
  `--force` or `--force-name` for those artifacts.

## impact on future orchestrated pipeline

No direct impact. Checksum backfill is a manifest-maintenance operation. It would not
change if a multi-role orchestration layer is introduced in Option B.

______________________________________________________________________

## designer handoff

The following sections of `docs/design/design.md` must be updated to reflect this
decision before implementation begins.

### 1. Section 1.1 — artifact lifecycle states

Add `managed-legacy` as an explicit named state in the state table:

```text
managed-legacy — in manifest; checksum absent; file exists but drift cannot be determined
```

Extend the state machine diagram with backfill transitions:

```text
managed-legacy --> managed        : manifest upgrade --backfill (VSTACK-META footer present)
managed-legacy --> managed-legacy : manifest upgrade --backfill (no footer; entry unchanged)
managed-legacy --> clean          : install --force or --force-name rewrites file + records checksum
```

### 2. Section 6 — `manifest upgrade` command contract

Add `--backfill` to the command synopsis and flag table:

```bash
vstack manifest upgrade [--target <dir>] [--backfill]
```

| Flag         | Description                                                                                                     |
| ------------ | --------------------------------------------------------------------------------------------------------------- |
| `--backfill` | Compute and store SHA-256 checksums for tracked entries with no checksum, gated by `VSTACK-META` identity check |

Extend the exit-code table:

| Exit code | Meaning                                                                    |
| --------- | -------------------------------------------------------------------------- |
| `0`       | Manifest upgraded (and backfilled if `--backfill`; partial backfill is OK) |
| `1`       | Manifest missing, unreadable, or parse error                               |

Document that `--backfill` is a one-way operation: current on-disk state becomes the
canonical baseline for backfilled entries. Users should be informed which entries were
backfilled and which were skipped (missing footer or missing file).

### 3. Section 2.1 — manifest domain interface

Document the `with_backfilled_checksums` method on `Manifest`:

```python
def with_backfilled_checksums(
    self,
    install_dir: Path,
) -> tuple["Manifest", list[str], list[str]]:
    """Return an updated manifest with checksums backfilled where possible.

    For each entry with ``checksum=None``, reads the on-disk file at
    ``install_dir / entry.file``. Computes SHA-256 and stores it only when
    the file contains a ``VSTACK-META`` footer comment.

    Returns:
        (updated_manifest, backfilled_names, skipped_names)
        where ``skipped_names`` are entries whose files existed but lacked the footer.
    """
```

Document: `CommandService.manifest_upgrade` calls `upgraded()` first (schema
migration), then `with_backfilled_checksums(install_dir)` when `--backfill` is set,
and passes the result to `manifest_file.write()`.
