# ADR-019: `.vstack/` Project-Scope Directory

> Maintained by: **architect** role

**date:** 2026-05-03\
**status:** accepted

## context

vstack installs Copilot artifacts into `.github/` and tracks them via a manifest.
However, there was no designated location for project-level configuration, doc
baseline stubs, or role-scoped doc templates that belong to the consuming project
rather than to vstack's generated output.

Previously, `vstack.json` lived at `.github/vstack.json`, mixing machine-generated
tracking state with Copilot artifacts. There was also no place for:

- Install configuration (e.g. which artifact types to exclude).
- Doc structure stubs seeded once and then owned by the project.
- Role-scoped doc templates for architecture, design, and release artifacts.

The question was: where should project-scoped, vstack-related state and
configuration live, and how should it be separated from generated Copilot artifacts?

## decision

Introduce `.vstack/` as the project-scope directory for all vstack-related state
and configuration that belongs to the project, not to the generated Copilot output.

```
.vstack/
├── config.yaml          ← human-authored install configuration (YAML)
├── vstack.json          ← machine-generated manifest (JSON, moved from .github/)
├── templates/           ← doc templates, seeded once then project-owned
│   ├── architect/
│   ├── designer/
│   ├── engineer/
│   ├── product/
│   ├── release/
│   └── tester/
└── tmp/                 ← scratch space, listed in .gitignore
```

`.vstack/` is created by `vstack install` (first-run setup) and is committed to
version control. `tmp/` is the only subdirectory excluded from git.

### file ownership and update policy

| File                   | Owner     | vstack overwrites?                                            |
| ---------------------- | --------- | ------------------------------------------------------------- |
| `.vstack/config.yaml`  | project   | Never                                                         |
| `.vstack/vstack.json`  | vstack    | Yes (machine-generated)                                       |
| `.vstack/templates/**` | project   | Additive only — new files added, existing files never touched |
| `.vstack/tmp/**`       | ephemeral | Not tracked                                                   |

### format convention

Two formats are used intentionally, signalling ownership:

- **JSON** (`vstack.json`) — machine-generated state. vstack owns it; do not
  hand-edit. The JSON format discourages accidental manual modification.
- **YAML** (`config.yaml`) — human-authored configuration. The project team owns
  it. YAML supports comments and is easier to read and maintain by hand.

This is analogous to `package-lock.json` (machine-generated) alongside
`package.json` (human-authored) in the npm ecosystem.

### `config.yaml` schema

```yaml
# vstack install  — first-run setup. Seeds this file if missing (never overwrites).
#                   Then runs init to generate .github/ artifacts from templates.
#                   Use once per project, or when onboarding a new machine.
#
# vstack init     — idempotent regeneration. Reads this file on every run.
#                   Safe to re-run in CI after pip install --upgrade vstack.

# Selective install exclusions — remove or comment out to install everything.
#
# exclude:
#   skills:
#     - terraform
#     - terragrunt
#     - helm
#     - k8s
#   instructions: all
#   prompts: all

# Root directory for generated agent artifact paths.
# Default: docs
#
# artifacts:
#   root: docs
```

All fields are optional. An absent `exclude:` block means install everything.
Artifact type values are either a list of names to skip, or `all` to skip
the entire type. `agents` cannot be excluded — the 6-role chain is an atomic unit.

The `artifacts: root:` key overrides the path prefix used in generated agent files
(e.g. links to architecture docs). Default is `docs`.

### scope boundary

`.vstack/` is repo-scoped only. Global installs (`vstack install --global`) write
Copilot artifacts directly to the VS Code user data directory and have no project
context — they do not create a `.vstack/` directory.

## alternatives considered

### Option A: Keep everything in `.github/`

**Pros:** Single directory; no new convention.

**Cons:** Mixes project-owned config with generated artifacts. Makes it harder to
determine what vstack regenerates vs what the project owns. `vstack.json` adjacent
to `agents/` and `skills/` creates confusion about what is source vs state.

**Why rejected:** Ownership clarity is a first-class concern. Generated output
(`.github/`) and project state (`.vstack/`) serve different purposes and have
different update policies.

### Option B: Use a dotfile (e.g. `.vstackrc` or `.vstack.yaml`)

**Pros:** Familiar single-file pattern.

**Cons:** A single file cannot accommodate both machine-generated state (`vstack.json`)
and project templates. Would require multiple dotfiles, which is more scattered than
a single directory.

**Why rejected:** A directory naturally groups related concerns.

### Option C: Use an existing directory (e.g. `.config/vstack/`)

**Pros:** Follows XDG conventions.

**Cons:** Less discoverable; `.vstack/` is self-explanatory and consistent with
tool naming conventions (`.terraform/`, `.nx/`, `.husky/`).

**Why rejected:** `.vstack/` is more immediately recognisable to users of the tool.

## rationale

A dedicated `.vstack/` directory makes ownership explicit: everything in `.github/`
is generated by vstack and can be regenerated at any time; everything in `.vstack/`
(except `vstack.json`) is project-owned and preserved. The format difference between
`vstack.json` (JSON) and `config.yaml` (YAML) reinforces this boundary without
requiring documentation.

## impact on future orchestrated pipeline

The `.vstack/config.yaml` file provides install configuration that `vstack init`
reads to determine which artifact types to generate. Additional configuration
concepts (model preferences, artifact path overrides, template overlays) may be
added to this schema as they are implemented — only fields with an active code
afnemer are documented here.
