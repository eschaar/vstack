# ADR-020: `install` and `init` Command Semantics

> Maintained by: **architect** role

**date:** 2026-05-03\
**status:** accepted\
**supersedes:** [ADR-015](015-conservative-install-by-default.md)

## context

vstack originally had a single `vstack install` command that both set up a project
and regenerated Copilot artifacts on subsequent runs. This conflated two distinct
concerns:

1. **First-run project setup** — creating `.vstack/`, seeding `docs/` stubs,
   writing `config.yaml`, and generating `.github/` artifacts for the first time.
1. **Ongoing artifact regeneration** — idempotently regenerating `.github/` after
   a vstack upgrade or template change.

This mismatch was confusing: the same command behaved differently depending on
whether `.vstack/` existed. CI pipelines ran `vstack install`, which implied
"installing" something on every pipeline run — not the expected mental model.

The conventional software model separates these concerns clearly:

- `install` = first-time setup, run once (analogous to `npm install`, `terraform init`)
- `init` = idempotent, safe to re-run (analogous to `git init`, `terraform init`)

vstack had these semantics reversed.

## decision

**`vstack install`** is the first-run project setup command. It:

- Creates `.vstack/` with `config.yaml`, `vstack.json`, and `templates/`
- Seeds `docs/` baseline stubs (additive — never overwrites existing files)
- Calls `vstack init` internally to generate `.github/` artifacts
- Is intended to be run once per project
- Is safe to re-run: already-existing files in `.vstack/` and `docs/` are skipped

**`vstack init`** is the idempotent artifact regeneration command. It:

- Generates or updates `.github/` artifacts from current vstack templates
- Is the command to run in CI pipelines and after `pip install --upgrade vstack`
- Adds new `.vstack/templates/` files from newer vstack versions (additive only)
- Is conservative by default for `.github/` artifacts (inherits ADR-015 policy):
  - Untracked files in `.github/` are never overwritten
  - Tracked files with local modifications are skipped and reported
  - Tracked clean files are replaced
  - `--force` overrides all preservation for explicit upgrade

**`vstack manifest upgrade`** handles breaking migrations (schema changes, file
location changes) and remains a separate, explicit command.

### conservative policy for `.github/` (inherited from ADR-015)

| Flag                  | Behaviour                                                                                                                   |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| _(default)_           | Skip untracked files; skip modified tracked files; replace clean tracked files; report obsolete candidates without removing |
| `--force`             | Overwrite all target files                                                                                                  |
| `--force-name <name>` | Overwrite one named artifact                                                                                                |
| `--adopt-name <name>` | Take ownership of an untracked file without overwriting                                                                     |
| `--update`            | Overwrite clean tracked files; skip locally modified files                                                                  |
| `--prune`             | Remove obsolete tracked artifacts that are clean (checksum matches manifest); preserve locally modified obsolete files      |

### additive policy for `.vstack/templates/` and `docs/`

Files seeded by `vstack install` into `.vstack/templates/` and `docs/` are
project-owned after creation. vstack will never overwrite them. On subsequent
`vstack init` runs, only missing files are added (additive-only). Projects can
freely modify seeded files.

### `vstack manifest upgrade` migration path (3.0)

In addition to existing schema migration (ADR-017), `vstack manifest upgrade` in
3.0 also handles location migration:

- Detects `.github/vstack.json` (legacy location)
- Moves it to `.vstack/vstack.json`
- Updates internal paths accordingly

Other `vstack` commands fail fast when `.github/vstack.json` is detected without a
corresponding `.vstack/vstack.json`, directing users to `vstack manifest upgrade`.

## alternatives considered

### Option A: Keep `vstack install` for both setup and CI regeneration

**Pros:** Single command; no migration burden.

**Cons:** Semantically incorrect — running "install" in CI on every build does not
match developer expectations. Forces consumers to explain why they run `install`
repeatedly. Conflates setup and maintenance into one command.

**Why rejected:** Mental model clarity matters for a developer tool. The confusion
was a recurring source of questions.

### Option B: Introduce `vstack sync` or `vstack update` for CI

**Pros:** Avoids overloading `install` or `init`.

**Cons:** Neither `sync` nor `update` is as universally understood as `init`.
`init` already carries the "idempotent setup" meaning from `git init`,
`terraform init`, and similar tools.

**Why rejected:** `init` is the established convention; inventing a new verb adds
vocabulary without benefit.

### Option C: Single `vstack init` command for everything (no `install`)

**Pros:** Minimal surface area; one command to learn.

**Cons:** No semantic distinction between first-run and ongoing use. Users cannot
tell from the command whether it will create new directories and files or only
regenerate existing artifacts.

**Why rejected:** The distinction between "set up a project" and "keep artifacts
current" is meaningful and worth exposing.

## rationale

Aligning with the convention established by `git init`, `terraform init`, and
`npm install` reduces cognitive load. `install` as a first-run wizard matches how
developers think about onboarding a new tool; `init` as an idempotent regenerator
matches how developers think about keeping generated files current. The separation
also makes CI configuration self-documenting: `vstack init` in a workflow step
clearly communicates "regenerate artifacts".

## impact on future orchestrated pipeline

The orchestrated pipeline (ADR-004) would invoke `vstack init` to ensure
Copilot artifacts are current before executing role stages, not `vstack install`.
This is consistent with the idempotent, side-effect-free intent of `init`.
