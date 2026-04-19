# Changelog

## 1.1.0 — 2026-04-20

Runtime response-style control via the new `concise` skill.

### Added in 1.1.0

- New `concise` skill — runtime response-style toggle with three density modes:
  - `concise normal` — full, explicit explanation depth.
  - `concise compact` — shorter prose, unchanged technical accuracy (default for most roles).
  - `concise ultra` — maximum brevity; narrative filler removed, technical correctness preserved.
  - `concise status` — reports active mode, session override, agent default, and auto-clarity override state.
  - Aliases: `concise on` → `compact`, `concise off` → `normal`.
- Per-role default concise modes wired into all 6 agent templates: `product=compact`, `architect=normal`, `designer=compact`, `engineer=compact`, `tester=ultra`, `release=compact`.
- Auto-clarity override: security warnings, destructive actions, and multi-step sequences always force `normal` regardless of active mode.

### Changed in 1.1.0

- All 6 role agent templates now reference `@#concise` in their `## skills you use` section.
- `EXPECTED_CANONICAL_NAMES` in `tests/conftest.py` now imports from `vstack.cli.constants` instead of duplicating the list.
- `README.md` updated with `concise` commands, per-role defaults table column, and verbosity control tips.
- `docs/design/skills.md` updated with `concise` row in the skills table.
- All six role agents (`product`, `architect`, `designer`, `engineer`, `tester`, `release`) now follow a shared structure:
  - `responsibilities and scope`
  - `principles`
  - `communication style`
  - `gate moments and handoffs`
  - `how you work`
  - `deliverables and success criteria`
  - `failure and escalation rules`
  - `skills you use`
- Added shared agent-skill boundary partial and wired it across all agents.
- Moved procedural detail out of agents into skills to keep agents outcome-focused and reduce template size.
- Release flow clarified: `release-notes` now explicitly owns both `docs/releases/{date}.md` and `CHANGELOG.md`; `pr` remains responsible for push/PR creation.
- Release and tester gating now treat performance baseline and observability evidence as required-for-scope artifacts rather than unconditional requirements.
- Added explicit `Deliverable and artifact policy` sections where needed across architecture/design/verification/release-related skills.
- Added explicit observability checks in verification flows (`inspect` and `verify`) for logs, metrics, traces, and alert/runbook evidence.
- Regenerated `.github` installed artifacts to match updated templates and policies.

## 1.0.5 — 2026-04-19

Workflow hardening and release-manifest refresh.

### Fixed in 1.0.5

- GitHub Actions workflows now declare explicit `permissions` to satisfy policy checks and follow least-privilege defaults.

### Changed in 1.0.5

- `release.yml` now defaults to read-only workflow permissions and scopes `contents: write` to the `version-and-release` job only.
- `qa.yml`, `security.yml`, and `verify.yml` now declare explicit workflow-level `permissions`.
- `verify.yml` normalized to use `on:` (unquoted) for style consistency with other workflows.
- `.github/vstack.json` refreshed via install to record the latest generated artifact manifest metadata.

## 1.0.4 — 2026-04-19

Skill expansion and documentation alignment update.

### Added in 1.0.4

- Six new skills: `migrate`, `openapi`, `refactor`, `onboard`, `dependency`, `incident`.
  - `migrate` — database migration review: zero-downtime analysis, expand/contract, rollback plans, index safety, batched backfills.
  - `openapi` — OpenAPI 3.1 spec writing and review: resource naming, HTTP semantics, status codes, error conventions, pagination, security schemes, versioning.
  - `refactor` — structured refactoring without behavior change: smell identification, incremental plan, step-by-step execution with test verification at each step.
  - `onboard` — contributor onboarding guide generation: prerequisites, setup, test commands, env vars, architecture overview, good first issues → `CONTRIBUTING.md`.
  - `dependency` — full dependency health audit: vulnerability scanning, outdated packages, licence compliance, transitive risk, pinning policy, supply chain hygiene.
  - `incident` — incident analysis and blameless post-mortem writing: timeline reconstruction, 5-Whys root cause, contributing factors matrix, action items → `docs/postmortems/YYYY-MM-DD-*.md`.

### Fixed in 1.0.4

- `refactor` skill: removed outer ```` ```bash ```` fences wrapping `{{RUN_TESTS}}` partial (which already includes its own fence).
- `onboard` skill: fixed nested fence issues in step 5 CONTRIBUTING.md example and step 6 README snippet.

### Changed in 1.0.4

- `engineer`, `designer`, `tester`, `product` agent templates updated with skill references for all new skills.
- `docs/design/skills.md` updated with full skill table including all new skills and their primary roles.
- `README.md` role–skill table updated to reflect new primary skills per role.
- `README.md` project structure diagram updated to include `instructions/` and `prompts/` template directories and the correct `docs/` subdirectory layout.
- `.github/copilot-instructions.md` updated: system structure diagram now includes all four template artifact types (`skills`, `agents`, `instructions`, `prompts`); hand-authored `.github/` exceptions listed explicitly; install table extended with `instructions` and `prompts` rows.

## 1.0.3 — 2026-04-19

Community health and release workflow update.

### Added in 1.0.3

- `CODEOWNERS` file.
- GitHub issue templates: `bug_report.yml`, `feature_request.yml`, `config.yml`.
- Pull request template (`.github/pull_request_template.md`).
- `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md` community health files.

### Changed in 1.0.3

- Release workflow title format updated to `Release vX.Y.Z (YYYY-MM-DD)`.

______________________________________________________________________

## 1.0.2 — 2026-04-17

Release workflow fix.

### Fixed in 1.0.2

- Release workflow: corrected Poetry setup order and opted in to Node 24 to resolve runner deprecation warnings.

______________________________________________________________________

## 1.0.1 — 2026-04-17

Tooling and release hygiene update focused on making local and CI verification match.

### Added in 1.0.1

- Repo-local `.python-version` for consistent pyenv interpreter resolution.
- Tox-based multi-version test execution across Python 3.11, 3.12, 3.13, and 3.14.
- Pre-commit hooks expanded: `trailing-whitespace`, `end-of-file-fixer`, `check-toml`, `check-yaml`, `ruff`, `ruff-format`.

### Changed in 1.0.1

- `pyproject.toml` migrated from `[tool.poetry]` to PEP 621 `[project]` form; `version = "0.0.0"` is a build-time placeholder overwritten by `poetry-dynamic-versioning`.
- Python support metadata is now explicitly bounded to 3.11–3.14.
- QA workflow now runs a Python test matrix across all supported runtimes.
- Local developer workflow now documents pyenv as the standard multi-version setup.

### Fixed in 1.0.1

- CI workflows: `pipx install poetry` now runs before `actions/setup-python` so the `cache: poetry` lookup always succeeds.
- CI workflows: bumped `actions/checkout@v4` → `v5` and `actions/setup-python@v5` → `v6` to resolve Node.js 20 deprecation warnings.

### Quality in 1.0.1

- Coverage gate raised back to 100%.
- `make test` now exercises every supported Python version when interpreters are installed.

## 1.0.0 — 2026-04-01

Initial public baseline for the VS Code-native vstack system.

### Added

- Python package layout under `src/vstack/` with runtime entrypoints:
  - `vstack` CLI
  - `python -m vstack`
- Generic artifact generation system:
  - `GenericArtifactGenerator`
  - `ArtifactTypeConfig`
  - manifest tracking via `vstack.json`
- Frontmatter system:
  - parser, schema validation, and builder
  - support for `str`, `bool`, `list`, `object-list`, and `raw`
- Agent templates and generation for six fixed roles:
  - product, architect, designer, engineer, tester, release
- Canonical skill set and generation pipeline based on source templates.
- Repository docs set:
  - architecture/design/workflow/skills docs
  - ADR set under `docs/architecture/adr/`
- Test suite for artifacts, frontmatter, CLI, agents, and skills.

### Changed

- Migrated to VS Code Agent artifacts and install-time generation model.
- Skill metadata model moved to per-skill `config.yaml`; `template.md` is body-only.
- Skills now follow a documented minimum body contract.
- Skill frontmatter output aligned to supported fields:
  - `version` kept in source config for install/version tracking, not emitted in generated `SKILL.md`
  - `allowed-tools` not emitted due to inconsistent support
- Placeholder governance moved to explicit registry mapping.

### Removed

- Legacy generator scripts and template/registry structure from earlier layout.
- Deprecated skill aliases and stale references (including freeze/unfreeze flow remnants).

### Quality

- Full suite passing at release cut.
- Coverage at 100%.
