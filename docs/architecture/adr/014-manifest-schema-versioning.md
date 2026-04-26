# ADR-014: Manifest Schema Versioning and Explicit Upgrade Gate

> Maintained by: **architect** role

**date:** 2026-04-26\
**status:** accepted

## context

`vstack.json` is a per-project manifest that grows over time as vstack adds
tracking capabilities. Early versions of the manifest stored artifacts with a flat
`content_hash` field and no explicit algorithm. Later versions introduced `checksum`,
`checksum_algorithm`, and `manifest_version` fields.

Without explicit schema versioning, running a newer version of the vstack CLI
against an older manifest could silently produce incorrect behaviour:

- Checksum comparisons might use the wrong algorithm.
- A missing `checksum_algorithm` field could be misinterpreted.
- `verify` and `status` could report false positives or false negatives.

The question was: should the CLI auto-upgrade manifests transparently, require
an explicit upgrade step, or simply accept any schema version at any time?

## decision

The manifest carries a `manifest_version` integer field (current value: `2`).

Operations that require current-schema semantics (`install`, `verify`, `status`,
`uninstall`) **fail fast** when a legacy schema is detected and print a diagnostic
pointing to `vstack manifest upgrade`. The upgrade is never automatic.

`vstack manifest upgrade --target DIR` explicitly migrates the manifest to the
current schema and is the only path that changes the version field.

## alternatives considered

### Option A: Transparent auto-upgrade on every read

**Pros:** Zero user friction; manifests are always current.

**Cons:** Silently mutates on-disk state during read-only operations (`status`,
`verify`). Surprises users who inspect the file. Creates hidden side effects that
are difficult to audit or test. Breaks the principle of least surprise for a
read-only command.

**Why rejected:** Read-only commands (`status`, `verify`) must not write files.

### Option B: Accept any schema version at any time

**Pros:** Maximum backwards compatibility; no user action required.

**Cons:** The CLI would have to carry forward all legacy parsing paths indefinitely.
Mismatches between manifest fields and CLI expectations would produce subtle,
hard-to-diagnose bugs rather than a clear error message.

**Why rejected:** Silent mismatches are harder to debug than an explicit upgrade
requirement, especially for a tool that manages shared `.github/` artifacts.

### Option C: Explicit upgrade gate (chosen)

**Pros:** Fail-fast with a clear message at the point of first mismatch. Upgrade
is intentional and auditable. Read-only commands remain side-effect-free. Test
coverage is straightforward — test both legacy-rejection and upgrade paths.

**Cons:** One extra command for users upgrading from an old vstack version.

## rationale

Explicit over implicit. A clear error message pointing to `vstack manifest upgrade`
is faster to resolve than a silent behavioural mismatch. The upgrade step is a
one-time migration, not a recurring cost, and it keeps `status` and `verify`
side-effect-free (NFR alignment).

The `allow_legacy=True` parameter on `ManifestFile.read` is the single code-level
bypass, used only by the upgrade command itself.

## consequences

### positive

- `status` and `verify` are guaranteed side-effect-free.
- Upgrade path is explicit, auditable, and testable.
- Old manifests are never silently misinterpreted.

### negative / tradeoffs

- Users upgrading from vstack < 1.0 must run `vstack manifest upgrade` once before
  other commands work again.
- The CLI must maintain `from_dict` legacy parsing for the upgrade command's
  `allow_legacy=True` path.

## impact on future orchestrated pipeline

No direct impact. The manifest schema gate is a CLI-only concern and would not
change if a multi-role orchestration layer is introduced.
