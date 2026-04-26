# requirements

> Maintained by: **product** role\
> Last updated: 2026-04-26

______________________________________________________________________

## context

vstack is a VS Code-native AI engineering workflow system. It installs structured
agents, skills, instructions, and prompts into `.github/` so GitHub Copilot Agent
Mode has a clear operating model. vstack is distributed as a standalone Python CLI
tool (`pipx install vstack`) with no runtime dependencies beyond the Python standard
library.

______________________________________________________________________

## functional requirements

### FR-1 — template-driven artifact generation

- Source templates live under `src/vstack/_templates/<type>/<name>/`.
- Supported artifact types: `skill` (`.github/skills/<name>/SKILL.md`), `agent`
  (`.github/agents/<name>.agent.md`), `instruction`
  (`.github/instructions/<name>.instructions.md`), `prompt`
  (`.github/prompts/<name>.prompt.md`).
- At generation time the generator resolves `{{TOKEN}}` placeholders from shared
  partials and injects frontmatter validated against the artifact schema.
- Unresolved tokens are flagged as errors by `validate` and `install`.

### FR-2 — install targets

- `--target DIR` installs artifacts into `DIR/.github/`.
- `--global` installs artifacts into the VS Code user profile directory.
- Both targets are mutually exclusive per invocation.

### FR-3 — manifest tracking

- `vstack install` writes a `vstack.json` manifest to the install root tracking
  every installed artifact (name, relative path, version, SHA-256 checksum, and
  algorithm).
- The manifest schema is versioned; older schemas must be explicitly upgraded with
  `vstack manifest upgrade`.

### FR-4 — file protection and install modes

- Untracked files in the target directory are never overwritten.
- Tracked artifacts are only rewritten when their on-disk checksum matches the
  stored manifest checksum (i.e., the file has not been locally modified), unless
  an explicit override flag is provided.
- `--force` overwrites all tracked artifacts regardless of local modifications.
- `--force-name <name>` overwrites one named artifact regardless of local modifications.
- `--adopt-name <name>` starts tracking an existing unmanaged file without rewriting
  its content.
- `--update` rewrites only when a newer version is available and the tracked file is
  still clean. Mutually exclusive with `--force`.
- `--dry-run` prints what would change without writing any files.

### FR-5 — uninstall

- `vstack uninstall` removes only tracked artifacts whose current checksum still
  matches the stored manifest entry.
- Modified tracked files are preserved unless `--force` or `--force-name` is provided.

### FR-6 — validation

- `vstack validate` renders all source templates in memory and reports unresolved
  tokens. No files are written. Exits 1 on any error.
- `--only <type>...` restricts validation to specific artifact types.

### FR-7 — verification

- `vstack verify` checks source templates (schema, required tokens, structure) and
  installed output (file presence, checksum drift).
- `--target DIR` / `--global` selects the install root for output checks.
- `--no-source` skips source template checks.
- `--no-output` skips installed output checks.

### FR-8 — status reporting

- `vstack status` inspects installed artifacts against `vstack.json` ownership and
  checksum state without writing files.
- Output formats: `text` (compact default with color markers), `json`, `yaml`.
- `--verbose` includes managed entries; `--no-color` disables ANSI colors.

### FR-9 — manifest subcommands

- `vstack manifest status` — manifest-scoped status for installed output.
- `vstack manifest verify` — manifest-scoped verify for installed output only.
- `vstack manifest upgrade` — upgrade legacy `vstack.json` schema to current format.

### FR-10 — role model

- 6 fixed agent roles: `product`, `architect`, `designer`, `engineer`, `tester`,
  `release`.
- 27 backend-oriented skills with canonical names enforced at source-verify time.

______________________________________________________________________

## non-functional requirements

| ID    | Requirement                                                                                            |
| ----- | ------------------------------------------------------------------------------------------------------ |
| NFR-1 | No runtime dependencies beyond the Python standard library.                                            |
| NFR-2 | Python 3.11–3.14 compatibility.                                                                        |
| NFR-3 | Manifest writes are atomic: write to a temporary file, then replace atomically.                        |
| NFR-4 | All public behavior exercised by automated tests (pytest). CI gate enforces test pass.                 |
| NFR-5 | CLI operates standalone; no VS Code process required for `install`, `verify`, or `validate`.           |
| NFR-6 | Lint (ruff) and type checking pass on every commit. CI gate enforces zero violations.                  |
| NFR-7 | Generated output lives under `.github/` only; source templates under `_templates/` are never modified. |

______________________________________________________________________

## success criteria

1. `vstack install --target DIR` installs all artifacts and writes `vstack.json` with
   correct checksums.
1. `vstack uninstall --target DIR` removes only tracked artifacts with matching
   checksums; modified files are preserved.
1. `vstack verify --target DIR` reports zero errors on a clean install.
1. `vstack validate` exits 0 when all source templates resolve cleanly.
1. Locally modified tracked files are preserved on re-install by default (FR-4).
1. All 27 canonical skill names are present after a full install.
1. `vstack manifest upgrade` migrates a legacy manifest without data loss.

______________________________________________________________________

## constraints

1. No external runtime dependencies (stdlib-only at runtime).
1. Generated output lives under `.github/` only; source templates are never modified
   at runtime.
1. Manifest schema is versioned; old manifests require explicit upgrade before further
   use.
1. CLI behavior must be reproducible across Python 3.11–3.14.
1. No cloud, network, or VS Code process dependency for CLI operations.
