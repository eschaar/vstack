# ADR-015: Conservative Install-by-Default

> Maintained by: **architect** role

**date:** 2026-04-26\
**status:** accepted

## context

vstack installs skill, agent, instruction, and prompt artifacts into a project's
`.github/` directory. Projects that use vstack frequently customize these installed
files — adjusting skill prompts, tightening instructions, or extending agent
behaviours to fit their specific conventions.

A naive re-install that overwrites existing files would silently destroy local
customizations. The install command therefore needs a clear policy for what it
will and will not overwrite.

There are two distinct cases:

1. **Untracked files**: files present in the target directory that were not placed
   there by `vstack install` (not in the manifest, or not matched by any installed
   artifact entry).
1. **Tracked files**: files placed by a previous `vstack install` and present in
   the manifest with a stored checksum.

The question was: should install be destructive by default (always overwrite), opt-in
safe (overwrite unless told not to), or conservative by default (refuse to overwrite
unless explicitly permitted)?

## decision

`vstack install` is conservative by default:

- **Untracked files** are never overwritten. The install skips them and reports the
  conflict.
- **Tracked files with local modifications** (on-disk checksum differs from manifest
  checksum) are not overwritten. The install skips them and reports the drift.
- **Tracked files in a clean state** (on-disk checksum matches manifest checksum)
  are safe to overwrite and are replaced.

Explicit escape hatches for intentional updates:

| Flag                  | Behaviour                                                           |
| --------------------- | ------------------------------------------------------------------- |
| `--force`             | Overwrite all target files, tracked or not, modified or clean       |
| `--force-name <name>` | Same as `--force` but scoped to a single named artifact             |
| `--adopt-name <name>` | Take ownership of an untracked file without overwriting its content |
| `--update`            | Overwrite clean tracked files; skip files with local modifications  |

## alternatives considered

### Option A: Always overwrite (destructive by default)

**Pros:** Simple implementation; install is idempotent in the naive sense.

**Cons:** Silently destroys local customizations. Forces users to diff and re-apply
customizations after every upgrade. Not acceptable for a tool whose primary value
is customizable role and skill files.

**Why rejected:** User customizations are first-class vstack usage; destroying them
by default contradicts the product intent.

### Option B: Interactive prompt per conflict

**Pros:** User decides case-by-case; no silent destruction.

**Cons:** Unworkable in CI/CD pipelines. Makes scripted or automated installs
impossible without a `--yes` flag. Adds significant complexity to the CLI contract.

**Why rejected:** vstack must operate non-interactively in CI contexts (NFR-5).

### Option C: Conservative by default with explicit escape hatches (chosen)

**Pros:** No silent destruction. Safe to re-run in CI (exits non-zero on conflict,
does not silently modify). Explicit flags (`--force`, `--adopt-name`, `--update`)
give full control for intentional upgrades.

**Cons:** First-time experience may confuse users who expect re-install to just work.
Conflict output must be clear enough that the correct flag is obvious.

**Why chosen:** Conservative default matches the principle of least surprise for a
tool managing files users have customized. CI pipelines can use `--force` or `--update`
explicitly when automation requires it.

## rationale

The checksum guard makes the boundary between "clean" and "modified" precise and
testable. An untracked file is never silently replaced. A file the user has modified
is never silently overwritten. The flags give escape hatches for every intentional
upgrade scenario, so conservative-by-default imposes no long-term friction on users
who understand the model.

This also simplifies the manifest invariant: if a file is tracked and its checksum
matches, the manifest is the authoritative source and the overwrite is safe.

## consequences

### positive

- Local customizations are always preserved unless the user explicitly opts in.
- CI pipelines that do not pass `--force` will fail loudly rather than silently
  mutate committed artifacts.
- Checksum-based tracking enables drift detection (`verify`, `status`).

### negative / tradeoffs

- First-time update workflows require learning one of the escape-hatch flags.
- `adopt-name` adds a non-obvious concept to the install surface.
- Skipped-file output must be well-formatted to be actionable in CI logs.

## impact on future orchestrated pipeline

No direct impact on the multi-role pipeline model. The conservative install policy
is a CLI contract concern and does not affect how roles pass artifacts between stages.
