# vstack — roadmap

> Maintained by: **product** role\
> Last updated: 2026-04-16

______________________________________________________________________

## feature status table

| Feature                                  | Status      | Notes                                                          |
| ---------------------------------------- | ----------- | -------------------------------------------------------------- |
| foundation                               | shipped     | Core template-driven install model is in place                 |
| backend-first verification               | shipped     | Verify/inspect focus on contracts, observability, security     |
| VS Code agent migration                  | shipped     | Native agent output format implemented                         |
| role model + doc restructure             | shipped     | 6-role model and docs baseline established                     |
| new skill scaffolding                    | shipped     | 27-skill set with canonical naming                             |
| agent skill wiring                       | shipped     | Role-to-skill mapping and handoffs are present                 |
| optional orchestrated role pipeline      | candidate   | Optional future model, only if coordination bottlenecks appear |
| multi-IDE support (IntelliJ first)       | candidate   | Not planned before v1 stabilization                            |
| heavy agent runtime framework            | not planned | Keeps runtime lightweight and transparent                      |
| cloud control plane dependency           | not planned | Keeps operation local/offline-capable                          |
| VS Code extension packaging              | not planned | Not required for current install model                         |
| browser automation as default dependency | not planned | Backend/microservice-first remains default                     |

______________________________________________________________________

## features

Legend: shipped = implemented and available; candidate = optional future feature (not committed); not planned = evaluated and intentionally excluded for now.

### foundation [shipped]

- template-driven generation with source under `src/vstack/_templates/` and install output under `.github/`
- 27 backend-oriented skills
- generated install manifest (`.github/vstack.json`) tracking installed artifacts
- VS Code prompt file (`.prompt.md`) support
- global install workflow (`vstack install --global`)

### backend-first verification [shipped]

- verify + inspect skills emphasizing contract tests, observability, security
- skill renaming to canonical backend names (vision, architecture, verify, etc.)
- `derive-from` removed from all templates

### VS Code agent migration [shipped]

- migrated from `.prompt.md` → `.github/agents/*.agent.md` format
- generator produces agents output with YAML frontmatter
- tool mapping (template tool names → VS Code tool IDs)
- removed upstream compatibility markers from generated artifacts

### role model + doc restructure [shipped]

- 6-role model defined: product, architect, designer, engineer, tester, release (guardian merged into tester)
- artifact ownership documented per role
- all docs renamed to lowercase
- docs/architecture/adr/ structure established
- docs rewritten to match agent-output format

### new skill scaffolding [shipped]

27 skills across 6 roles. New additions:

- `requirements`, `adr`, `analyse` (new)
- Renames: `experience` → `consult`, `design-consult` → `design`, `docs-release` → `docs`, `discovery` → `explore`
- All templates: WHO→HOW (removed role persona preamble, added out-of-scope sections)
- `guardrails` retained as a per-project installable safety skill

### agent skill wiring [shipped]

Role templates now reference the intended canonical skills:

- Product + architect include `requirements` and `adr`
- Architect + engineer include `analyse` and `explore`
- Designer includes `consult`
- Agent configs define role-to-role handoff buttons for pipeline flow

______________________________________________________________________

### optional orchestrated role pipeline [candidate]

Possible future workflow with explicit orchestration (only if real coordination bottlenecks appear):

- Each role makes its own model call
- Artifacts pass between roles via disk files
- User gates pause the pipeline at defined checkpoints
- Orchestrator role (product) manages pipeline state
- Parallel execution possible for multiple tester passes

See `docs/design/workflow.md` for current execution and the orchestrated future model.

### multi-IDE support [candidate]

IntelliJ is the first candidate beyond VS Code. Not planned until after v1 stabilization.

### heavy agent runtime framework [not planned]

Not included to keep execution lightweight and transparent in VS Code native workflows.

### cloud control plane dependency [not planned]

Not included so teams can run vstack fully local/offline without hosted infrastructure.

### VS Code extension packaging [not planned]

Not required for the current install model (`vstack install`) and kept out to reduce maintenance overhead.

### browser automation as default dependency [not planned]

Kept optional; backend/microservice verification remains the default priority.

______________________________________________________________________

## decisions captured

### global install scope

`vstack install --global` is now scoped to VS Code user-profile artifacts only:

- `agents/`
- `prompts/`
- `instructions/`
- `skills/`

All artifact types are supported globally. vstack provides generic, reusable
behavior; project-specific customization is out of scope.
