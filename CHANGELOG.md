# Changelog

## [Unreleased]

- No unreleased changes yet.

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
