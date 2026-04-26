# ADR-012: Template Directories and Install-Time Generation

> Maintained by: **agents** role

**date:** 2026-03-28\
**status:** accepted — implemented

## context

vstack separates source templates from generated artifacts. The source of truth lives
in `src/vstack/_templates/`, while generated output is written at install time.

This created three problems:

1. **Source vs output must stay separate.** Generated files should not be edited as source.

1. **Agents must stay role-based.** Agent files represent fixed roles, not skills.

1. **Install-time generation must be deterministic.** Fresh generation from templates must be repeatable,
   while install/update in consumer repos must preserve unmanaged files and locally modified tracked files unless forced.

## decision

### 1. template directories under `_templates`

Keep source templates under:

```
src/vstack/_templates/
├── skills/<name>/
│   ├── config.yaml
│   └── template.md
└── agents/<name>/
   ├── config.yaml
   └── template.md
```

### 2. no direct edits to generated output

In the vstack source repo, generated output under `.github/` is install-time output
and should not be edited directly.

### 3. install-time generation with `vstack install`

At install time (`vstack install` or `vstack install --target <project-dir>`), the
installer generates artifacts into `.github/`, including:

- `.github/skills/<name>/SKILL.md`
- `.github/agents/<name>.agent.md`
- `.github/prompts/*.prompt.md`
- `.github/instructions/*.instructions.md`

The installer is conservative by default:

- existing files that are not tracked in `vstack.json` are preserved
- tracked files are updated only when their content still matches the last installed SHA-256 checksum
- `--adopt-name <artifact-name>` allows explicitly adopting one unmanaged file into tracking without overwriting it
- `--force-name <artifact-name>` can override preservation for one artifact
- `--force` is the explicit opt-in for overwriting local changes

The same manifest checksum is also used for safe uninstall and status reporting:

- `vstack uninstall` preserves tracked files with local drift unless forced
- `vstack verify` fails when installed output no longer matches the manifest checksum
- `vstack status` reports which files still match the manifest and which no longer do

### 4. role-first agents (generated from templates)

Agent instructions are authored in `src/vstack/_templates/agents/` and generated as
6 role agents (product, architect, designer, engineer, tester, release).

## alternatives considered

1. **Treat generated `.github/` files as source.** Rejected — source of truth is `_templates`.

1. **Generate to a separate build tree by default.** Rejected — project-local `.github/`
   output matches VS Code discovery and keeps behavior explicit for the workspace.

1. **Mix role and skill agent concepts.** Rejected — roles are canonical for agent identity.

## rationale

**Separation of concerns:** Source (`src/vstack/_templates/`) is clean. Generated output is an install
artifact, not a repo concern. This eliminates stale-file confusion and makes
`git status` clean after editing templates.

**Role-first model:** Agents represent WHO does work (roles), not HOW (skills).
Separating them allows roles to evolve independently from skill definitions.

## impact on future orchestrated pipeline

Future orchestrated role pipeline stages map directly to role agents, not skills. This
structure reinforces that boundary: each stage in the pipeline corresponds to a
role agent that references skills by name.

## validation

Template and install validation run through the current Python CLI/tooling
(`vstack validate`, `vstack install`, and tests under `test/`).
