# vstack — roadmap

> Maintained by: **product** role\
> Last updated: 2026-05-06

______________________________________________________________________

## feature status table

| Feature                                  | Version | Status      | Notes                                                                                                                                |
| ---------------------------------------- | ------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| foundation                               | v1.0.0  | shipped     | Core template-driven install model is in place                                                                                       |
| backend-first verification               | v1.0.0  | shipped     | Verify/inspect focus on contracts, observability, security                                                                           |
| VS Code agent migration                  | v1.x    | shipped     | Native `.github/agents/*.agent.md` output format implemented                                                                         |
| role model + doc restructure             | v1.1.0  | shipped     | 6-role model, agent templates, and docs baseline established                                                                         |
| new skill scaffolding                    | v2.2.0  | shipped     | 42-skill set with canonical naming                                                                                                   |
| agent skill wiring                       | v2.2.0  | shipped     | Role-to-skill mapping, handoffs, and concise modes wired into all agents                                                             |
| CLI modularisation                       | v2.0.0  | shipped     | 12 focused CLI modules; BaseCommand + CommandContext contract                                                                        |
| manifest package                         | v2.0.0  | shipped     | Dedicated `manifest/` package; atomic writes (ADR-016)                                                                               |
| mypy type checking                       | v2.0.0  | shipped     | Full mypy coverage enforced in CI; 100% test coverage gate                                                                           |
| manifest schema versioning               | v2.0.0  | shipped     | `manifest_version: 2`; upgrade path via `manifest upgrade` (ADR-014)                                                                 |
| checksum backfill                        | v2.0.0  | shipped     | `manifest upgrade --backfill` adds SHA-256 for VSTACK-META-tagged files (ADR-017)                                                    |
| conservative install                     | v2.0.0  | shipped     | Untracked files never overwritten; checksum-gated update (ADR-015, superseded by ADR-020)                                            |
| dry-run install                          | v2.1.0  | shipped     | `vstack install --dry-run` previews actions; type/name selectors in summary                                                          |
| project-scope directory                  | v3.0.0  | shipped     | `.vstack/` directory: `config.yaml`, manifest, delta templates (ADR-019)                                                             |
| install/init command semantics           | v3.0.0  | shipped     | `install` = first-run setup; `init` = idempotent CI regeneration (ADR-020, breaking change)                                          |
| manifest relocation                      | v3.0.0  | shipped     | `vstack.json` moves from `.github/` to `.vstack/`; migration via `manifest upgrade` (ADR-014)                                        |
| selective install                        | v3.0.0  | shipped     | Per-type and per-name exclusions via `exclude:` in `.vstack/config.yaml`; agents always installed (ADR-022)                          |
| agent hooks support                      | t.b.d.  | candidate   | Generate `.github/hooks/<name>.json` from vstack templates; enforce quality gates at session boundaries                              |
| new skills (next batch)                  | t.b.d.  | candidate   | `spaces`: set up Copilot Spaces; `copilot-admin`: manage Copilot settings via `gh api`                                               |
| team customization layer                 | t.b.d.  | candidate   | Custompacks on top of vstack defaults; agents non-removable, skills fully overridable; overlay merge model                           |
| workflow contract source-of-truth        | t.b.d.  | shipped     | `workflow:` block in `.vstack/config.yaml`; `gate`, `hitl`, `handoffs` schema; `vstack migrate` command (ADR-023, ADR-026)           |
| optional orchestrated role pipeline      | v3.2.0  | shipped     | `planner` coordinator agent implemented with mode-aware generation; default mode is `agentic` (`manual` and `hybrid` also supported) |
| parallel workflow via DAG model          | v3.3.0  | candidate   | Directed Acyclic Graph orchestration: run stages in parallel where safe; serialize only on data dependencies                         |
| multi-IDE support (IntelliJ first)       | t.b.d.  | candidate   | Not planned before current model stabilizes                                                                                          |
| heavy agent runtime framework            | —       | not planned | Keeps runtime lightweight and transparent                                                                                            |
| cloud control plane dependency           | —       | not planned | Keeps operation local/offline-capable                                                                                                |
| VS Code extension packaging              | —       | not planned | Not required for current install model                                                                                               |
| browser automation as default dependency | —       | not planned | Backend/microservice-first remains default                                                                                           |
| install target directory override        | —       | not planned | Won't implement unless a concrete tool incompatibility with `.github/` arises                                                        |

______________________________________________________________________

## features

Legend: shipped = implemented and available; candidate = optional future feature (not committed); not planned = evaluated and intentionally excluded for now.

______________________________________________________________________

### foundation [shipped — v1.0.0]

- Template-driven generation with source under `src/vstack/_templates/` and install output under `.github/`
- Generated install manifest (`.vstack/vstack.json`) tracking installed artifacts
- VS Code prompt file (`.prompt.md`) support
- Global install workflow (`vstack install --global`)

### backend-first verification [shipped — v1.0.0]

- verify + inspect skills emphasizing contract tests, observability, security
- Skill renaming to canonical backend names (vision, architecture, verify, etc.)
- `derive-from` removed from all templates

### VS Code agent migration [shipped — v1.x]

- Migrated from `.prompt.md` → `.github/agents/*.agent.md` format
- Generator produces agents output with YAML frontmatter
- Tool mapping (template tool names → VS Code tool IDs)
- Removed upstream compatibility markers from generated artifacts

### role model + doc restructure [shipped — v1.1.0]

- Delivery role model defined: product, architect, designer, engineer, tester, release
- Artifact ownership documented per role; all docs renamed to lowercase
- `docs/architecture/adr/` structure established
- Docs rewritten to match agent-output format; per-role concise modes wired into all agents

### new skill scaffolding [shipped — v2.2.0]

42 skills across 6 roles. Representative additions:

- `requirements`, `adr`, `analyse` (new)
- `gh-issues`, `codeql`, `dependabot`, `secret-scan`, `gh-release`
- `gdpr`, `terraform`, `terragrunt`, `cloudformation`, `aws-cli`
- `k8s`, `helm`, `rancher`, `threat-model`, `conventional-commit`
- Renames: `experience` → `consult`, `design-consult` → `design`, `docs-release` → `docs`, `discovery` → `explore`
- All templates: WHO→HOW (removed role persona preamble, added out-of-scope sections)

### agent skill wiring [shipped — v2.2.0]

- Product + architect include `requirements` and `adr`
- Architect + engineer include `analyse` and `explore`
- Designer includes `consult`
- Agent configs define role-to-role handoff buttons for pipeline flow
- `artifacts.input` / `artifacts.output` fields in all agent `config.yaml` files

______________________________________________________________________

### CLI modularisation [shipped — v2.0.0]

- 12 focused CLI modules under `src/vstack/cli/`; one `BaseCommand` subclass per command
- `BaseCommand` + `CommandContext` contract replaces ad hoc argument passing
- `CommandService` refactored to shared coordinator (generators, manifest, state)
- `COMMAND_CATALOG` as the single registration point for all commands

### manifest package [shipped — v2.0.0]

- Dedicated `src/vstack/manifest/` package extracted from CLI internals
- Atomic manifest writes via temp-file + `os.replace` (ADR-016)
- `ManifestFile` handles read/write/existence checks; `read_error` for diagnostics
- `manifest_version: 2` schema with `hash_algorithm` and per-entry `checksum_algorithm`
- Upgrade path: `vstack manifest upgrade [--backfill]`
- Checksum backfill for VSTACK-META-tagged files (ADR-017)
- mypy type checking added as a quality gate; 100% test coverage enforced in CI

### conservative install [shipped — v2.0.0]

- Untracked files are never overwritten by default (ADR-015)
- Checksum-gated `--update` mode: only rewrites clean tracked files
- `--force-name` / `--adopt-name` accept `type/name` selectors (e.g. `agent/engineer`)

### dry-run install [shipped — v2.1.0]

- `vstack install --dry-run` previews all planned actions without writing any files
- Summary shows which artifacts would be installed, updated, preserved, or skipped
- Type/name selectors (`--only`) compose with dry-run for scoped previews

______________________________________________________________________

### project-scope directory [shipped — v3.0.0]

- `.vstack/` directory introduced as the project-scope state container (ADR-019)
- `config.yaml` — human-authored project configuration (YAML)
- `vstack.json` — machine-generated install manifest (JSON), relocated from `.github/`
- `templates/` — project-owned artifact starter templates, seeded by `vstack install`
- `.vstack/.gitignore` seeded on every install run

### install/init command semantics [shipped — v3.0.0]

- `vstack install` — first-run setup: seeds `.vstack/`, generates all artifacts, writes manifest (ADR-020)
- `vstack init` — idempotent CI regeneration: rewrites artifacts from templates, updates manifest
- Breaking change: previous `install` behavior is now split across both commands

### manifest relocation [shipped — v3.0.0]

- `vstack.json` moved from `.github/` to `.vstack/` to separate generated config from generated artifacts
- Migration via `vstack manifest upgrade` for existing installs
- Format difference (JSON vs YAML) signals machine-generated vs human-authored ownership (ADR-019)

### selective install [shipped — v3.0.0]

- Per-type exclusion via `exclude: <type>: all` in `.vstack/config.yaml` removes an entire artifact type
- Per-name exclusion via `exclude: <type>: [name, …]` installs all but the listed names
- Agents are always installed; the six-role chain is an atomic unit (ADR-022)
- Composes with `--only`: type exclusions subtract from the effective install set

______________________________________________________________________

### agent hooks support [candidate — t.b.d.]

GitHub Copilot agents support a repository-level hooks mechanism: shell commands defined in
`.github/hooks/<name>.json` that execute at key points during an agent session —
`sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, and `errorOccurred`.

vstack is well-positioned to provide curated, installable hook templates for common quality-gate patterns:

- **Pre-tool safety gate** (`preToolUse`) — block or log destructive operations before they run
- **Session audit log** (`sessionStart` / `sessionEnd`) — record session boundaries with timestamp and working directory
- **Auto-format on edit** (`postToolUse`) — trigger `ruff format`, `terraform fmt`, `mdformat` after file edits
- **Commit policy check** (`postToolUse`) — run `cchk` or commit-message lint after `git commit` tool calls
- **Security scan on push** (`postToolUse`) — run `gitleaks` or `detect-secrets` after repository mutations

Planned direction:

- Add a `hooks` artifact type to the vstack generator, parallel to `skills` and `instructions`
- Templates live in `src/vstack/_templates/hooks/<name>/hook.json` (source of truth)
- Generated output written to `.github/hooks/<name>.json` at install time
- Register hooks in `vstack.json` manifest and track them with checksums like other artifact types
- Note: the per-agent `hooks` frontmatter field (already supported) is separate — it scopes hooks to one
  agent; repository hooks apply to all agent sessions

Ref: [GitHub — Customize agent workflows with hooks](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/use-hooks)

### new skills (next batch) [candidate — t.b.d.]

Two new skills planned for the next skill expansion:

#### `spaces`

Guides setup and maintenance of a Copilot Space for a project.

- Identify which project artifacts belong in the Space (architecture docs, design docs, README, ADRs, skills)
- Step-by-step setup via GitHub UI or `gh api`
- Refresh procedure when baseline docs change (after `vstack install` or a release)
- Quality check: detect stale or missing context entries

Ref: [GitHub — Copilot Spaces](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/copilot-spaces)

#### `copilot-admin`

Operational skill for Copilot administrators. Covers all `gh api` operations across the Copilot admin surface:

- **Content exclusion** — query and set excluded paths at repo/org/enterprise scope; path-pattern conventions and anti-patterns
- **MCP governance** — list and manage allowed MCP servers; define allowlist/denylist policy defaults
- **Memory governance** — enable/disable memory per org or repo; view and delete repository memories
- **Usage and billing** — query seat usage, premium-request consumption, and alert thresholds; monthly review checklist
- **Observability** — pull adoption and usage metrics via API; define operational KPIs and escalation triggers

Ref: [GitHub — Administer GitHub Copilot for your team](https://docs.github.com/en/copilot/how-tos/administer-copilot)

### team customization layer [candidate — t.b.d.]

Teams want to put their own layer on top of vstack — tuning agents to company context,
replacing generic skills with company-specific ones, and bundling those changes as a
reusable custompack that travels with the project.

Rules:

- **Agents** — can be customized (description, tools, handoffs, prompt body); cannot be removed
  (the six-role chain is an atomic unit, ADR-022)
- **Skills** — can be overridden entirely with a company version, or supplemented with new skills
- **Instructions and prompts** — fully under team control; vstack defaults are a starting point
- **Custompacks** — a named bundle of overrides and additions tracked in the manifest alongside first-party artifacts

Planned direction:

- Define a `custompack` artifact type: a directory of templates with the same structure as
  `src/vstack/_templates/` that a team maintains in their own repo
- `vstack install --pack <path>` installs the custompack after the base set; team artifacts
  win on conflict for skills, instructions, and prompts; agents are merged, not replaced
- Track custompack artifacts in `vstack.json` with a `source: custompack` marker so
  `vstack status` and `uninstall` can distinguish first-party from team-owned files
- Add a `vstack pack init` scaffold command to create a well-structured custompack starter

Overlay model (template source priority):

- Multiple template sources resolved in priority order: upstream vstack first, custompack second
- Conflict resolution is deterministic: custompack wins for skills, instructions, and prompts;
  agents are merged (custompack fields override, core structure preserved)
- Source-aware checksums in `vstack.json` so updates can be applied safely per origin
- Longer term: `vstack install --profile company` for named install profiles

Ref: [GitHub — Customize Copilot for your project](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-copilot-overview)

### workflow contract source-of-truth [shipped — t.b.d.]

Shipped in this release:

- `workflow:` block seeded in `.vstack/config.yaml` by `vstack install`, with `stage`, `gate`,
  `hitl`, and `handoffs.prompt` for all six roles (ADR-023)
- `handoffs:` section in generated `.agent.md` files is now driven by the workflow config rather
  than hardcoded in each agent's `config.yaml`
- `baseline:` flag on output artifacts; agents explicitly maintain baseline docs vs. per-session deliverables
- `vstack migrate` command applies docs artifact path moves between major versions,
  with `--dry-run`, `--from`, and `--to` flags; migration records in `src/vstack/_migrations/` (ADR-026)
- `docs/design/workflow.md` remains the human-readable explanation layer

Not yet implemented (deferred to orchestrated pipeline milestone):

- Generator-level cross-role validation of input/output chains
- Central read-only contract export for external orchestrator consumption

### parallel workflow via DAG model [candidate — v3.3.0]

**What is DAG?** (Directed Acyclic Graph)

A DAG is a directed graph with no cycles that represents task dependencies. In the context of vstack:

- Each workflow stage (product, architect, designer, engineer, tester, release) is a **node**
- An edge from stage A → B means "B depends on output from A" (e.g., engineer depends on designer)
- **Parallel execution** happens when stages have no direct or transitive dependency between them
- **Deterministic ordering** is preserved: a stage never starts until all its dependencies complete

**Current limitation:**

Today, vstack uses **linear/serial execution**: stages run strictly in canonical order (product → architect →
designer → engineer → tester → release). This is safe and deterministic, but inefficient:

```
time →
product     ████
            ├─ architect     ████
            │   ├─ designer      ████
            │   │   ├─ engineer       ████
            │   │   │   ├─ tester         ████
            │   │   │   │   ├─ release         ████
```

Total: 6 sequential stages, ~6× the wall-clock time of a single stage.

**Why DAG matters:**

Many stages **do not** have dependencies. For example:

- `architect` and `tester` are often independent: architecture design does not block security/performance
  review of a feature proposal
- `designer` and `tester` may be independent: API contract specification does not block observability design
- `release` is independent of most stages except explicit gate decisions

With DAG, independent stages can run **in parallel**:

```
time →
product        ████
               ├─ architect     ████   ┐
               │                       ├─ (parallel) engineer ████
               ├─ designer      ████   ┤
               │                       ┤ tester         ████
               └─ tester               ┘
                   └─ release ████
```

Potential wall-clock reduction: 6 stages → 3 stages (~50% faster).

**DAG-model implementation plan:**

1. **Dependency schema** — extend `.vstack/config.yaml` `workflow.stages` with optional `depends_on: [list]` field

   - Default (omitted): inherits canonical ordering (backwards-compatible)
   - Explicit deps: enables parallel scheduling

1. **Scheduling algorithm** — topological sort of the DAG

   - `planner` agent computes the schedule at orchestration start
   - Stages are grouped into "layers": all stages in layer N can run in parallel; layer N+1 starts after layer N completes

1. **Artifact locking** — prevent concurrent modification of shared output files

   - Manifest locks at the artifact type level (e.g., only one agent can write to `.github/agents/`)
   - Staged writes: all agents in a layer write to temp files; `planner` merges after layer completes

1. **Join semantics** — configurable failure policy per stage layer

   - `all_success` (default): if any stage in a layer fails, the entire DAG fails
   - `fail_fast`: same; no alternative in the initial version
   - Future: `best_effort`, `skip_on_error` for optional quality gates

1. **Output ordering** — ensure deterministic artifact ordering in generated files

   - Agent output is sorted by role name; same for skills, instructions
   - Reproducible builds remain a design principle

**Backwards compatibility:**

- `.vstack/config.yaml` without `depends_on` fields defaults to canonical ordering
- Existing configs work unchanged
- DAG adoption is opt-in: teams explicitly add `depends_on` to enable parallelism

**Risks and mitigations:**

| Risk                                         | Mitigation                                                               |
| -------------------------------------------- | ------------------------------------------------------------------------ |
| Non-deterministic artifact ordering          | Sort all outputs by role/name/type                                       |
| Race conditions on manifest writes           | Atomic writes, per-layer serialization of merges                         |
| Unclear error causation in parallel failures | Preserve stage execution order in logs; label outputs by layer and stage |
| Config complexity                            | Sane defaults (canonical order); optional `depends_on`                   |

**Example config:**

```yaml
version: 3
workflow:
  mode: agentic
  stages:
    - role: product
      gate: required

    - role: architect
      gate: required
      depends_on: [product]  # must wait for product

    - role: designer
      gate: required
      depends_on: [product]  # can run in parallel with architect

    - role: engineer
      gate: required
      depends_on: [architect, designer]  # waits for both

    - role: tester
      gate: required
      depends_on: [product, architect]  # independent of designer

    - role: release
      gate: required
      depends_on: [engineer, tester]  # waits for both
```

**Next steps:**

1. Write ADR-027 (DAG-model orchestration with dependency schema)
1. Design `depends_on` schema and topological sort algorithm
1. Implement `planner` layer-grouping logic
1. Add integration tests for parallel stage execution and failure scenarios
1. Update config schema docs and examples

### optional orchestrated role pipeline [shipped — v3.2.0]

ADR-024 is implemented.

Shipped:

- Added `planner` agent template (`src/vstack/_templates/agents/planner/`)
- Implemented mode-aware agent generation via `workflow.mode`
- Added planner/worker mode semantics for `agentic` (default): planner generated, worker handoff buttons omitted
- Added planner/worker mode semantics for `manual`: planner omitted, worker handoff buttons generated
- Added planner/worker mode semantics for `hybrid`: planner generated, worker handoff buttons generated
- Added mode-switch pruning for tracked planner artifact when switching to `manual`
- Added CLI parsing defaults and validation for workflow mode
- Added tests for manual/agentic/hybrid behavior and mode-switch behavior

### multi-IDE support [candidate — t.b.d.]

IntelliJ is the first candidate beyond VS Code. Not planned until after the current model stabilizes.
Requires separate template sets, different generator targets, and different frontmatter schemas.

______________________________________________________________________

### heavy agent runtime framework [not planned]

Not included to keep execution lightweight and transparent in VS Code native workflows.

### cloud control plane dependency [not planned]

Not included so teams can run vstack fully local/offline without hosted infrastructure.

### VS Code extension packaging [not planned]

Not required for the current install model (`vstack install`) and kept out to reduce maintenance overhead.

### browser automation as default dependency [not planned]

Kept optional; backend/microservice verification remains the default priority.

### install target directory override [not planned]

Configuring the output root (e.g. `.cursor/` instead of `.github/`) is not implemented.
All mainstream AI editors read `.github/` without issue. This will only be reconsidered
if a concrete tool incompatibility with `.github/` is reported.

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
