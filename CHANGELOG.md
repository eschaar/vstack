# Changelog

<!-- markdownlint-disable MD024 -->

## [2.0.3](https://github.com/eschaar/vstack/compare/2.0.2...2.0.3) (2026-04-28)

### Maintenance

- **ci:** harden release workflows and normalize changelog ([5a38709](https://github.com/eschaar/vstack/commit/5a387091dcea8dc7545bda5430fd02aee88ac0af))
- **ci:** restructure pipeline with release-please and GitHub App token ([8c06090](https://github.com/eschaar/vstack/commit/8c060906ae7d8a662ff1e772fa531484eafb1067))
- **ci:** restructure pipeline with release-please and GitHub App token ([#30](https://github.com/eschaar/vstack/issues/30)) ([0008127](https://github.com/eschaar/vstack/commit/0008127fafbf261fbbf6363fe9a4eb7769edfe83))

## [2.0.2](https://github.com/eschaar/vstack/compare/2.0.1...2.0.2) (2026-04-27)

### Maintenance

- **ci:** bump trufflesecurity/trufflehog from 3.94.3 to 3.95.2 ([#25](https://github.com/eschaar/vstack/issues/25)) ([5724dbe](https://github.com/eschaar/vstack/commit/5724dbe605523da2c90a4f143fa8c4a92322adf4))

## [2.0.1](https://github.com/eschaar/vstack/compare/2.0.0...2.0.1) (2026-04-27)

### Maintenance

- **ci:** bump actions/download-artifact from 7 to 8 ([#26](https://github.com/eschaar/vstack/issues/26)) ([24d5a58](https://github.com/eschaar/vstack/commit/24d5a585c37fe8097de41863e0085917e81a376f))

## 2.0.0 (2026-04-26)

CLI architecture refactor and manifest package extraction. **BREAKING CHANGE** — import paths have changed.

### BREAKING CHANGES

- `vstack.cli.commands` removed. `CommandService` and command classes now live in dedicated modules (`vstack.cli.service`, `vstack.cli.install`, `vstack.cli.verify`, etc.).
- Manifest persistence classes moved to new `vstack.manifest` package (`vstack.manifest.store`).

### Features

- `vstack manifest upgrade --backfill`: retroactively compute and write checksums for tracked manifest entries with no checksum.
- New `vstack.manifest` package with schema-versioned manifest read/write and `content_hash` utility.
- 12 focused CLI modules replacing the monolithic `commands.py`.
- mypy type checking added as a quality gate (106 files, 0 errors).
- 4 new ADRs: manifest schema versioning (014), conservative install defaults (015), atomic manifest writes (016), checksum backfill (017).

### Fixes

- `InstallCommand._version_gt` no longer raises `TypeError` when `existing` version is `None` on first install.

### Maintenance

- Full test suite restructured: per-module test files, `TestClass` layout, catch-all files deleted. Test count: 288 → 342.
- End-to-end integration tests consolidated into `tests/vstack/test_integration.py`.

## 1.3.6 (2026-04-22)

README and PyPI README badge/layout alignment.

### Fixes

- Fixed oversized logo rendering in `README-pypi.md` by constraining image width.
- Fixed duplicate title/branding in `README-pypi.md` by removing redundant `# vstack` heading.
- Fixed badge ordering so badges render beneath the logo in `README-pypi.md`.
- Fixed PyPI version badge formatting in both `README.md` and `README-pypi.md` to show the raw version (no `v` prefix).
- Fixed verify/security workflow badges in both `README.md` and `README-pypi.md` by removing `branch=main` filter so PR-based workflows report status correctly.

## 1.3.5 (2026-04-22)

Changelog and PyPI packaging metadata alignment update.

### Maintenance

- Corrected changelog version history from 1.3.0 onward so entries align with actual created tags and release chronology.
- Switched published long description source from `README.md` to `README-pypi.md` for PyPI-compatible rendering.
- Added PyPI-focused project metadata in `pyproject.toml`: `keywords`, `classifiers`, and `project.urls`.
- Added explicit repository guidance to keep `README-pypi.md` in sync with `README.md`.

### Features

- Added a dedicated `README-pypi.md` with PyPI-safe links, badges, and a concise DX-first quickstart.

## 1.3.4 (2026-04-22)

Release build versioning fix: explicit plugin activation and full history checkout.

### Fixes

- Fixed CI release builds still producing `0.0.0` artifacts by calling `poetry dynamic-versioning` explicitly before `poetry build`. Poetry reads the version once at load time — the plugin must be active and called before the build step runs.
- Fixed release build tag visibility by setting `fetch-depth: 0` on the tag-pinned checkout so `git describe` can traverse full history.
- Fixed dynamic versioning compatibility in `pyproject.toml` by switching to PEP 621 dynamic versioning (`project.dynamic = ["version"]`) and keeping the placeholder at `tool.poetry.version`.
- Fixed `poetry dynamic-versioning` compatibility by removing unsupported `tool.poetry-dynamic-versioning.fallback-version`.
- Fixed release race conditions by adding workflow `concurrency` controls, including serialized main release execution.
- Fixed release integrity by creating the GitHub release only after PyPI publish succeeds.
- Fixed tag existence validation to check `refs/tags/<version>` directly instead of a generic ref lookup.
- Fixed rerun friction after failed release attempts by automatically deleting the freshly created tag when build or publish fails.
- Added post-build wheel smoke test (`pip install --no-deps` + `vstack --help`) before artifact upload to avoid network-dependent dependency resolution.
- Clarified PR workflow concurrency comments in `security.yml` and `verify.yml` to match `github.ref` behavior (`refs/pull/<id>/merge`).

## 1.3.3 (2026-04-22)

Release build plugin activation fix.

### Fixes

- Fixed CI release builds producing `0.0.0` artifacts by installing `poetry-dynamic-versioning` as a Poetry plugin via `pipx inject` in the release build job.
- Fixed release build reproducibility by pinning the Poetry CLI version (`POETRY_VERSION`) in workflow environment configuration.
- Fixed CI drift by aligning Poetry installation to the same pinned version across `release.yml`, `qa.yml`, `verify.yml`, and `security.yml`.

## 1.3.2 (2026-04-22)

Release build version-guard fix.

### Fixes

- Fixed release build determinism by checking out `refs/tags/<version>` in the build job instead of building from a moving branch ref.
- Fixed accidental `0.0.0` package publishing by validating that HEAD is pinned to the expected release tag before build and that produced artifacts include the expected version.

## 1.3.1 (2026-04-22)

Release workflow and test isolation fixes.

### Fixes

- Fixed release workflow trigger: switched from `pull_request: closed` to `push: branches: [main]` so the workflow runs under `refs/heads/main` and satisfies the PyPI environment deployment branch protection rule.
- Fixed `build` job checkout configuration so `poetry-dynamic-versioning` can read git tags during the build.
- Fixed `download-artifact` version mismatch (`v5` → `v7`) to align with `upload-artifact@v7`.

## 1.3.0 (2026-04-22)

DX, onboarding, and PyPI publishing release.

### Features

- Added GitHub Discussion templates for onboarding and adoption feedback:
  - `onboarding-feedback`
  - `first-run-report`
  - `model-cost-feedback`
- Added team setup guidance in `README.md` with project-first install flow and expected outcomes.
- Added explicit expected output examples for first install validation in `README.md`.
- Added a troubleshooting decision flowchart in `README.md`.

### Maintenance

- Restructured `README.md` for faster onboarding with clearer quick paths, role usage guidance, and troubleshooting navigation.
- Updated architect and product agent template model ordering and regenerated installed agent artifacts.
- Updated generated artifact metadata and aligned generation tests with current template output.
- Added PyPI publish job to release workflow using OIDC trusted publishing (no API tokens required).

### Fixes

- Fixed `test_install_and_verify_exits_zero` writing generated artifacts into the repository root instead of an isolated `tmp_path`.

## 1.2.5 (2026-04-21)

CI dependency maintenance release.

### Maintenance

- GitHub Actions: bumped `actions/checkout` from v5 to v6.

## 1.2.4 (2026-04-21)

CI dependency maintenance release.

### Maintenance

- GitHub Actions: bumped `actions/upload-artifact` from v4 to v7.

## 1.2.3 (2026-04-21)

Release workflow dependency maintenance.

### Maintenance

- GitHub Actions: bumped `softprops/action-gh-release` from v2 to v3.

## 1.2.2 (2026-04-21)

Security workflow dependency maintenance.

### Maintenance

- GitHub Actions: bumped `trufflesecurity/trufflehog` from `3.88.2` to `3.94.3`.

## 1.2.1 (2026-04-21)

README rendering fix release.

### Fixes

- Fixed Mermaid flowchart syntax in `README.md` so GitHub renders the role-flow diagram correctly.

## 1.2.0 (2026-04-21)

CLI provenance verification and documentation system alignment.

### Features

- CLI artifact provenance verification against the install manifest.

### Maintenance

- Refactored CLI parser flow into a `CommandLineParser` class and simplified install and verify control flow.
- Refactored frontmatter serialization internals (instance-method serializer, naming cleanup, and reduced nested parse/validation flow).
- Aligned hand-authored Markdown docs toward Mermaid-first diagram usage, with ASCII as fallback where needed.
- Updated skill template guidance and regenerated installed skill artifacts to adopt the Mermaid-first diagram convention.
- README branding/header refreshed with centered logo and badges plus light/dark logo switching.
- Centralized commit and branch policy in `cchk.toml` and wired local `pre-commit` hooks for commit-message and pre-push branch validation.
- Removed hard CI scope allowlist enforcement; commit scopes are now guidance-level in documentation rather than a strict gate.
- Fixed multiple documentation link paths under `docs/design/` so relative Markdown links resolve correctly on GitHub.
- Updated `CONTRIBUTING.md` commit-policy wording to match the current `cchk.toml` enforcement model.
- Strengthened generated skill footer tests to assert the `AUTO-GENERATED` and `VSTACK-META` footer structure at end-of-file.

## 1.1.0 (2026-04-20)

Runtime response-style control via the new `concise` skill.

### Features

- New `concise` skill — runtime response-style toggle with three density modes:
  - `concise normal` — full, explicit explanation depth.
  - `concise compact` — shorter prose, unchanged technical accuracy (default for most roles).
  - `concise ultra` — maximum brevity; narrative filler removed, technical correctness preserved.
  - `concise status` — reports active mode, session override, agent default, and auto-clarity override state.
  - Aliases: `concise on` → `compact`, `concise off` → `normal`.
- Per-role default concise modes wired into all 6 agent templates: `product=compact`, `architect=normal`, `designer=compact`, `engineer=compact`, `tester=ultra`, `release=compact`.
- Auto-clarity override: security warnings, destructive actions, and multi-step sequences always force `normal` regardless of active mode.

### Maintenance

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

## 1.0.5 (2026-04-19)

Workflow hardening and release-manifest refresh.

### Fixes

- GitHub Actions workflows now declare explicit `permissions` to satisfy policy checks and follow least-privilege defaults.

### Maintenance

- `release.yml` now defaults to read-only workflow permissions and scopes `contents: write` to the `version-and-release` job only.
- `qa.yml`, `security.yml`, and `verify.yml` now declare explicit workflow-level `permissions`.
- `verify.yml` normalized to use `on:` (unquoted) for style consistency with other workflows.
- `.github/vstack.json` refreshed via install to record the latest generated artifact manifest metadata.

## 1.0.4 (2026-04-19)

Skill expansion and documentation alignment update.

### Features

- Six new skills: `migrate`, `openapi`, `refactor`, `onboard`, `dependency`, `incident`.
  - `migrate` — database migration review: zero-downtime analysis, expand/contract, rollback plans, index safety, batched backfills.
  - `openapi` — OpenAPI 3.1 spec writing and review: resource naming, HTTP semantics, status codes, error conventions, pagination, security schemes, versioning.
  - `refactor` — structured refactoring without behavior change: smell identification, incremental plan, step-by-step execution with test verification at each step.
  - `onboard` — contributor onboarding guide generation: prerequisites, setup, test commands, env vars, architecture overview, good first issues → `CONTRIBUTING.md`.
  - `dependency` — full dependency health audit: vulnerability scanning, outdated packages, licence compliance, transitive risk, pinning policy, supply chain hygiene.
  - `incident` — incident analysis and blameless post-mortem writing: timeline reconstruction, 5-Whys root cause, contributing factors matrix, action items → `docs/postmortems/YYYY-MM-DD-*.md`.

### Fixes

- `refactor` skill: removed outer ```` ```bash ```` fences wrapping `{{RUN_TESTS}}` partial (which already includes its own fence).
- `onboard` skill: fixed nested fence issues in step 5 CONTRIBUTING.md example and step 6 README snippet.

### Maintenance

- `engineer`, `designer`, `tester`, `product` agent templates updated with skill references for all new skills.
- `docs/design/skills.md` updated with full skill table including all new skills and their primary roles.
- `README.md` role–skill table updated to reflect new primary skills per role.
- `README.md` project structure diagram updated to include `instructions/` and `prompts/` template directories and the correct `docs/` subdirectory layout.
- `.github/copilot-instructions.md` updated: system structure diagram now includes all four template artifact types (`skills`, `agents`, `instructions`, `prompts`); hand-authored `.github/` exceptions listed explicitly; install table extended with `instructions` and `prompts` rows.

## 1.0.3 (2026-04-19)

Community health and release workflow update.

### Features

- `CODEOWNERS` file.
- GitHub issue templates: `bug_report.yml`, `feature_request.yml`, `config.yml`.
- Pull request template (`.github/pull_request_template.md`).
- `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md` community health files.

### Maintenance

- Release workflow title format updated to `Release vX.Y.Z (YYYY-MM-DD)`.

## 1.0.2 (2026-04-17)

Release workflow fix.

### Fixes

- Release workflow: corrected Poetry setup order and opted in to Node 24 to resolve runner deprecation warnings.

## 1.0.1 (2026-04-17)

Tooling and release hygiene update focused on making local and CI verification match.

### Features

- Repo-local `.python-version` for consistent pyenv interpreter resolution.
- Tox-based multi-version test execution across Python 3.11, 3.12, 3.13, and 3.14.
- Pre-commit hooks expanded: `trailing-whitespace`, `end-of-file-fixer`, `check-toml`, `check-yaml`, `ruff`, `ruff-format`.

### Maintenance

- `pyproject.toml` migrated from `[tool.poetry]` to PEP 621 `[project]` form; `version = "0.0.0"` is a build-time placeholder overwritten by `poetry-dynamic-versioning`.
- Python support metadata is now explicitly bounded to 3.11–3.14.
- QA workflow now runs a Python test matrix across all supported runtimes.
- Local developer workflow now documents pyenv as the standard multi-version setup.
- Coverage gate raised back to 100%.
- `make test` now exercises every supported Python version when interpreters are installed.

### Fixes

- CI workflows: `pipx install poetry` now runs before `actions/setup-python` so the `cache: poetry` lookup always succeeds.
- CI workflows: bumped `actions/checkout@v4` -> `v5` and `actions/setup-python@v5` -> `v6` to resolve Node.js 20 deprecation warnings.

## 1.0.0 (2026-04-01)

Initial public baseline for the VS Code-native vstack system.

### Features

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

### Maintenance

- Migrated to VS Code Agent artifacts and install-time generation model.
- Skill metadata model moved to per-skill `config.yaml`; `template.md` is body-only.
- Skills now follow a documented minimum body contract.
- Skill frontmatter output aligned to supported fields:
  - `version` kept in source config for install/version tracking, not emitted in generated `SKILL.md`
  - `allowed-tools` not emitted due to inconsistent support
- Placeholder governance moved to explicit registry mapping.
- Legacy generator scripts and template/registry structure from earlier layout.
- Deprecated skill aliases and stale references (including freeze/unfreeze flow remnants).
- Full suite passing at release cut.
- Coverage at 100%.
