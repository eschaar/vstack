# vstack — architecture

> Maintained by: **agents** role\
> Last updated: 2026-04-01

## overview

vstack is a VS Code–native AI engineering workflow system. It provides template-driven
skills for planning, reviewing, verifying, and releasing backend services, microservices,
and libraries via GitHub Copilot Agent Mode.

______________________________________________________________________

## system structure

```text
vstack/
├── src/vstack/                  ← Python package (source of truth)
│   ├── frontmatter/             ← parser, builder, schema
│   ├── artifacts/               ← GenericArtifactGenerator, ArtifactTypeConfig
│   ├── skills/                  ← SKILL_SCHEMA, SKILL_TYPE
│   ├── agents/                  ← AGENT_SCHEMA, AGENT_TYPE
│   └── cli/                     ← commands, parser, constants
├── _templates/
│   ├── skills/
│   │   ├── <skill-name>/
│   │   │   ├── config.yaml          ← skill frontmatter fields
│   │   │   └── template.md          ← skill instructions body
│   │   └── _partials/
│   │       └── *.md                 ← shared partial snippets
│   └── agents/
│       └── <agent-name>/
│           ├── template.md          ← agent instructions body
│           └── config.yaml          ← agent frontmatter fields
├── test/
│   └── test_skills.py
├── docs/
│   ├── architecture.md          ← this file (architect)
│   ├── design.md                ← component design (designer)
│   ├── roadmap.md               ← milestones + vision (product)
│   ├── skills.md                ← skill reference
│   ├── workflow.md              ← execution flow
│   └── adr/                     ← architecture decision records
├── .github/                     ← generated output (never edit directly)
│   ├── skills/<name>/SKILL.md
│   └── agents/<name>.agent.md
└── README.md
```

______________________________________________________________________

## components

### 1. template system (`src/vstack/_templates/`)

Each skill is a directory under `src/vstack/_templates/skills/<name>/` containing a `config.yaml`
and a `template.md` body. Each agent is a directory under `src/vstack/_templates/agents/<name>/`
containing a `template.md` (body only) and a `config.yaml` (frontmatter fields).

Shared partial snippets live in `src/vstack/_templates/skills/_partials/*.md` and are injected
via `{{TOKEN}}` substitution at generation time.

Templates are the source of truth. No generated files live in `src/vstack/_templates/`.

### 2. generator (`src/vstack/artifacts/generator.py`)

`GenericArtifactGenerator` discovers template directories, validates frontmatter
against the artifact schema, resolves `{{PLACEHOLDER}}` tokens from partials, and
writes output files. All type-specific behaviour is expressed through an
`ArtifactTypeConfig` descriptor.

Run at install time: `vstack install`

### 3. resolver system

Key resolvers defined inline in the generator:

| Placeholder                   | Purpose                                                             |
| ----------------------------- | ------------------------------------------------------------------- |
| `{{SKILL_CONTEXT}}`           | Shared context block: role, completeness principle, question format |
| `{{BASE_BRANCH}}`             | Shell snippet to detect git base branch                             |
| `{{RUN_TESTS}}`               | Detect test framework and run tests                                 |
| `{{OBSERVABILITY_CHECKLIST}}` | Observability coverage checklist                                    |
| `{{API_CONTRACT_CHECKLIST}}`  | API contract review checklist                                       |

### 4. role model

vstack uses 6 fixed agent roles. Each role has defined skill access and artifact ownership.
See `docs/architecture/adr/009-role-model.md` for the decision record.

| Role      | Artifact ownership                                                                  |
| --------- | ----------------------------------------------------------------------------------- |
| product   | `docs/product/vision.md`, `docs/product/requirements.md`, `docs/product/roadmap.md` |
| architect | `docs/architecture/architecture.md`, `docs/architecture/adr/*.md`                   |
| designer  | `docs/design/design.md`, `docs/design/ux.md` (frontend scope), API specs            |
| engineer  | code, unit tests                                                                    |
| tester    | `docs/test-report.md`, `docs/security-report.md`, `docs/performance-baseline.md`    |
| release   | `docs/releases/{date}.md`, `CHANGELOG.md`, release PR                               |

### 5. manifest (`vstack.json`)

Generated at install time in the target directory. Tracks every artifact installed
by `vstack install` (skills, agents, instructions, and prompts) so that `vstack uninstall` can remove
exactly those files. Not committed to the vstack source repo.

### 6. VS Code agent files (`.github/agents/<name>.agent.md`)

Generated output — one file per role (6 total: product, architect, designer, engineer,
tester, release). Installed to `.github/agents/` in a project.

```yaml
---
name: "architect"
description: "Senior software architect…"
tools:
  - read
  - search
  - edit
  - web
  - vscode
  - todo
  - agent
agents: ["*"]
target: vscode
user-invocable: true
---
```

Each agent body describes: responsibilities, workflow steps, artifact ownership,
and which skills to invoke.

______________________________________________________________________

## execution model

### current execution model — single-call

Copilot reads a `SKILL.md` file and executes the workflow in a single context window.

```text
User → /skill-name → Copilot reads .github/agents/<skill>.agent.md
                   → Executes steps in one model call
                   → Writes output to disk
```

### possible future model — orchestrated role pipeline

Each role makes its own model call. Output artifacts are passed to the next role.

```text
User → product (intake)
     → architect (design)
     → designer (specs)   [conditional: frontend scope]
     → engineer (build)
     → tester (validate + audit)
     → product (sign-off) [gate: user approval]
     → release (deploy + monitor)
```

See `docs/architecture/adr/004-option-a-to-b-pipeline.md` and `docs/design/workflow.md` for pipeline detail.

______________________________________________________________________

## decision records

All significant architectural decisions are recorded in `docs/architecture/adr/`.
See individual files for context, decision, alternatives, and rationale.
