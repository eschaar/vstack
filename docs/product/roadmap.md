# vstack — roadmap

> Maintained by: **product** role\
> Last updated: 2026-06-01

______________________________________________________________________

## feature status table

| Feature                                       | Version | Status      | Notes                                                                                                                                                              |
| --------------------------------------------- | ------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| foundation                                    | v1.0.0  | shipped     | Core template-driven install model is in place                                                                                                                     |
| backend-first verification                    | v1.0.0  | shipped     | Verify/inspect focus on contracts, observability, security                                                                                                         |
| VS Code agent migration                       | v1.x    | shipped     | Native `.github/agents/*.agent.md` output format implemented                                                                                                       |
| role model + doc restructure                  | v1.1.0  | shipped     | 6-role model, agent templates, and docs baseline established                                                                                                       |
| CLI modularisation                            | v2.0.0  | shipped     | 12 focused CLI modules; BaseCommand + CommandContext contract                                                                                                      |
| manifest package                              | v2.0.0  | shipped     | Dedicated `manifest/` package; atomic writes (ADR-016)                                                                                                             |
| mypy type checking                            | v2.0.0  | shipped     | Full mypy coverage enforced in CI; 100% test coverage gate                                                                                                         |
| manifest schema versioning                    | v2.0.0  | shipped     | `manifest_version: 2`; upgrade path via `manifest upgrade` (ADR-014)                                                                                               |
| checksum backfill                             | v2.0.0  | shipped     | `manifest upgrade --backfill` adds SHA-256 for VSTACK-META-tagged files (ADR-017)                                                                                  |
| conservative install                          | v2.0.0  | shipped     | Untracked files never overwritten; checksum-gated update (ADR-015, superseded by ADR-020)                                                                          |
| dry-run install                               | v2.1.0  | shipped     | `vstack install --dry-run` previews actions; type/name selectors in summary                                                                                        |
| new skill scaffolding                         | v2.2.0  | shipped     | 42-skill set with canonical naming                                                                                                                                 |
| agent skill wiring                            | v2.2.0  | shipped     | Role-to-skill mapping, handoffs, and concise modes wired into all agents                                                                                           |
| project-scope directory                       | v3.0.0  | shipped     | `.vstack/` directory: `config.yaml`, manifest, delta templates (ADR-019)                                                                                           |
| install/init command semantics                | v3.0.0  | shipped     | `install` = first-run setup; `init` = idempotent CI regeneration (ADR-020, breaking change)                                                                        |
| manifest relocation                           | v3.0.0  | shipped     | `vstack.json` moves from `.github/` to `.vstack/`; migration via `manifest upgrade` (ADR-014)                                                                      |
| selective install                             | v3.0.0  | shipped     | Per-type and per-name exclusions via `exclude:` in `.vstack/config.yaml`; agents always installed (ADR-022)                                                        |
| workflow contract source-of-truth             | v3.1.0  | shipped     | `workflow:` block in `.vstack/config.yaml`; `gate`, `hitl`, `handoffs` schema; `vstack migrate` command (ADR-023, ADR-026)                                         |
| agent hooks support                           | v3.2.0  | shipped     | First-class `hook` artifact type: generate `.github/hooks/<name>.json` from templates and track in manifest                                                        |
| optional orchestrated role pipeline           | v3.2.0  | shipped     | `planner` coordinator agent implemented with mode-aware generation; default mode is `agentic` (`manual` and `hybrid` also supported)                               |
| parallel workflow via DAG model               | v3.3.0  | shipped     | `depends_on` DAG semantics and planner parallel scheduling are shipped in v3.3.0                                                                                   |
| new skills (next batch)                       | v3.3.0  | shipped     | `space-setup`: set up Copilot Spaces; `copilot-ops`: operate Copilot governance settings with audit-first checks                                                   |
| golden-fixture coverage expansion             | v3.3.0  | shipped     | Extend deterministic golden fixtures to cover additional high-impact templates per artifact type.                                                                  |
| defect-fixture matrix expansion               | v3.3.0  | shipped     | Expand defect fixtures across artifact types and failure classes with stable expected error assertions.                                                            |
| planner routing refinement                    | v3.4.0  | shipped     | Planner/orchestrator routing follow-up to the DAG work                                                                                                             |
| docs information architecture (Diataxis)      | t.b.d.  | candidate   | `docs/user/` scaffold and navigation are in place with segmented tutorials/how-to/reference/explanation routes; broader migration and fully realized IA come later |
| team customization layer                      | t.b.d.  | candidate   | Deferred major update after VS Code-first model proves itself; custompacks, overlay merge rules, and install profiles all add major maintenance surface            |
| multi-IDE support (IntelliJ first)            | t.b.d.  | candidate   | Deferred until vstack proves stable in VS Code; likely a major follow-up because it needs separate targets, schemas, and more maintenance                          |
| plugin/bundle distribution model              | t.b.d.  | candidate   | A self-contained, versioned bundle of vstack artifacts as a distribution model with no external registry or repository mapping                                     |
| artifact integrity and verification hardening | t.b.d.  | candidate   | Layered checks, generated-artifact drift detection, and deterministic fixtures to reduce release risk.                                                             |
| hook telemetry parser hardening (P2)          | t.b.d.  | candidate   | Optional deeper payload normalization for actor/tool/model extraction across broader event shapes without adding runtime dependencies.                             |
| planner analytics enrichment (P2)             | t.b.d.  | candidate   | Optional aggregation/reporting on stage-report telemetry (`planner_run_id`, `model_used`, `subagents_invoked`) for post-run analysis.                              |
| template-change-aware fixture CI gate         | t.b.d.  | candidate   | Require fixture drift checks automatically in CI whenever template sources are modified.                                                                           |
| fixture update policy in PR workflow          | t.b.d.  | candidate   | Enforce contributor guidance that intended generated-output changes include fixture updates in the same pull request.                                              |
| deeper targeted verify tier                   | t.b.d.  | candidate   | Define and run a deeper pre-merge/release verification tier covering integration, fixture, and contract checks.                                                    |
| heavy agent runtime framework                 | —       | not planned | Keeps runtime lightweight and transparent                                                                                                                          |
| cloud control plane dependency                | —       | not planned | Keeps operation local/offline-capable                                                                                                                              |
| VS Code extension packaging                   | —       | not planned | Not required for current install model                                                                                                                             |
| browser automation as default dependency      | —       | not planned | Backend/microservice-first remains default                                                                                                                         |
| install target directory override             | —       | not planned | Won't implement unless a concrete tool incompatibility with `.github/` arises                                                                                      |

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

### docs information architecture (Diataxis) [candidate — t.b.d.]

Adopt a Diataxis-aligned structure under `docs/user/` with explicit routing boundaries:

- `docs/user/tutorials/` for learning-oriented walkthroughs
- `docs/user/how-to/` for goal-driven operational tasks
- `docs/user/reference/` for lookup-oriented contracts and factual interfaces
- `docs/user/explanation/` for rationale, concepts, and trade-offs

Scope in this phase is intentionally limited to structure and navigation guidance.
Existing documentation now lives under `docs/user/`.

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

### agent hooks support [shipped — v3.2.0]

GitHub Copilot agents support a repository-level hooks mechanism: shell commands defined in
`.github/hooks/<name>.json` that execute at key points during an agent session —
`sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, and `errorOccurred`.

vstack now provides installable repository hook templates for quality-gate patterns:

- **Pre-tool safety gate** (`preToolUse`) — block or log destructive operations before they run
- **Session audit log** (`sessionStart` / `sessionEnd` / `userPromptSubmitted` / `preToolUse` / `postToolUse`) — record session boundaries and lightweight prompt/tool telemetry
- **Log retention cleanup** (`sessionStart`) — prune old dated log directories based on retention settings
- **Auto-format on edit** (`postToolUse`) — optionally run `make format` in enforce mode
- **Markdown quality check** (`postToolUse`) — run markdown/work-item formatting checks for docs and templates
- **Post-commit security scan** (`postToolUse` / `sessionEnd`) — run staged secret checks with optional `gitleaks` in enforce mode

Implemented:

- `hook` is a first-class artifact type in the generator and CLI type registry
- Templates live in `src/vstack/_templates/hooks/<name>/hook.yaml` (source of truth)
- Generated output is written to `.github/hooks/<name>.json` at install time
- Hooks are registered in `.vstack/vstack.json` and tracked with checksums like other artifact types
- The per-agent `hooks` frontmatter field remains separate and still scopes hooks to one
  agent; repository hooks apply to all agent sessions

Shipped default hook set:

- `session-audit`
- `agent-call-audit`
- `log-retention-cleanup`
- `pre-tool-safety-gate`
- `post-edit-format`
- `post-edit-markdown-quality`
- `post-commit-security-scan`

Migration path:

- Existing repositories do not require a manual migration step for this feature
- Run `vstack install` (or `vstack init` in CI) to materialize managed `.github/hooks/*.json` output
- Use `.vstack/config.yaml` `exclude.hook` if your project does not want repository-level hooks

Ref: [GitHub — Customize agent workflows with hooks](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/use-hooks)

### new skills (next batch) [shipped — v3.3.0]

Two new skills now ship in the current baseline:

#### `space-setup`

Guides setup and maintenance of a Copilot Space for a project.

- Identify which project artifacts belong in the Space (architecture docs, design docs, README, ADRs, skills)
- Step-by-step setup via GitHub UI or `gh api`
- Refresh procedure when baseline docs change (after `vstack install` or a release)
- Quality check: detect stale or missing context entries

Ref: [GitHub — Copilot Spaces](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/copilot-spaces)

#### `copilot-ops`

Operational skill for Copilot governance and admin workflows. Covers audit-first operations across the Copilot admin surface:

- **Content exclusion** — query and set excluded paths at repo/org/enterprise scope; path-pattern conventions and anti-patterns
- **MCP governance** — list and manage allowed MCP servers; define allowlist/denylist policy defaults
- **Memory governance** — enable/disable memory per org or repo; view and delete repository memories
- **Usage and billing** — query seat usage, premium-request consumption, and alert thresholds; monthly review checklist
- **Observability** — pull adoption and usage metrics via API; define operational KPIs and escalation triggers

Ref: [GitHub — Administer GitHub Copilot for your team](https://docs.github.com/en/copilot/how-tos/administer-copilot)

### planner routing refinement [shipped — v3.4.0]

- Planner/orchestrator routing follow-up to the DAG work.

### team customization layer [candidate — t.b.d.]

This is a later major update, not a near-term roadmap item. The idea is valid, but it
adds another product layer on top of a system that is still proving itself in its
VS Code-first form.

Teams may eventually want to tune agents to company context, replace generic skills with
company-specific ones, and bundle those changes as a reusable custompack that travels
with the project. That remains a plausible direction, but only after the core model has
earned more real-world validation.

Why this is deferred:

- It adds a second overlay system on top of the base template model.
- It requires custompack install, status, and uninstall semantics.
- It introduces source-aware manifest tracking and merge rules.
- It increases maintenance cost for every future agent, skill, and workflow change.
- It can introduce breaking changes if the base model evolves.
- It should only be revisited if real project demand still exists after VS Code adoption is proven.

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
- Longer term, if still justified: `vstack install --profile company` for named install profiles

Ref: [GitHub — Customize Copilot for your project](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-copilot-overview)

### workflow contract source-of-truth [shipped — v3.1.0]

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

### parallel workflow via DAG model [shipped — v3.3.0]

**What is DAG?** (Directed Acyclic Graph)

A DAG is a directed graph with no cycles that represents task dependencies. In the context of vstack:

- Each workflow stage (product, architect, designer, engineer, tester, release) is a **node**
- An edge from stage A → B means "B depends on output from A" (e.g., engineer depends on designer)
- **Parallel execution** happens when stages have no direct or transitive dependency between them
- **Deterministic ordering** is preserved: a stage never starts until all its dependencies complete

**Current behavior:**

vstack now supports DAG dependencies through optional `depends_on` in `workflow.stages`.
When `depends_on` is omitted, behavior remains fully sequential and backward compatible.

Validation and safety guarantees:

- unknown dependency role references are rejected,
- self-dependencies are rejected,
- duplicate stage roles are rejected,
- cyclic dependency graphs are rejected.

Sequential compatibility mode (no `depends_on`):

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

**Current scope:**

1. Dependency schema support in `.vstack/config.yaml` via optional `depends_on` per stage.
1. DAG validation in CLI parsing and workflow graph checks.
1. Backward-compatible sequential defaults when `depends_on` is absent.
1. DAG-aware handoff target resolution for worker agents.

**Remaining work beyond this release:**

1. Planner-level parallel dispatch scheduling and layer execution policy.
1. Explicit runtime join/failure strategy controls for parallel stage groups.
1. Additional integration tests for parallel orchestration execution traces.

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

1. Implement planner runtime layer scheduling for parallel-ready stages.
1. Add explicit join policy knobs for DAG layer completion.
1. Expand orchestration integration tests for multi-stage parallel traces.
1. Add user-facing troubleshooting guidance for DAG misconfiguration recovery.

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

This is a future major update, not a near-term roadmap item. vstack is intentionally
VS Code-first, and the current model still needs to prove itself before we can judge
whether support for other IDEs is worth the added complexity.

IntelliJ is the first possible expansion target, but only after the VS Code model is
stable and the product direction still makes the investment worthwhile.

Why this is deferred:

- It requires separate template sets and generator targets per IDE.
- It likely needs IDE-specific frontmatter schemas and capability mapping.
- It increases maintenance burden across every future agent, hook, and workflow change.
- It raises the risk of breaking changes when the VS Code model evolves.
- The AI tooling landscape may shift before a second IDE target becomes strategically useful.

Current decision: keep this as a later, optional major update and revisit it only after
vstack has established traction in the VS Code workflow first.

### plugin/bundle distribution model [candidate — t.b.d.]

This is a possible VS Code-first distribution path, not a near-term commitment.
The goal is to evaluate whether vstack can be consumed as a Copilot agent plugin
while preserving the current template-driven model and low operational overhead.

Scope to evaluate:

- Plugin packaging and install flow for vstack-managed agents/skills
- Compatibility with existing `.vstack/` and `.github/` generation outputs
- Security and policy behavior in organizations with restricted Copilot settings
- Migration path that does not require shipping a dedicated VS Code extension

Reference:

- [VS Code Copilot agent plugins](https://code.visualstudio.com/docs/copilot/customization/agent-plugins)

### portable bundle format [candidate — t.b.d.]

A portable bundle packages a curated set of vstack artifacts — agents, skills, instructions,
prompts, and hooks — as a single versioned unit. The bundle can be distributed and installed
without coupling to any external registry or specific repository.

Scope to evaluate:

- A standard container format for an artifact set that the `install` pipeline can consume
  alongside the built-in templates
- Install, status, and uninstall operations that treat the bundle as one addressable unit
  tracked in `.vstack/vstack.json`
- Human-readable, offline-capable format compatible with the existing template-driven model
- Versioned manifest entry so bundle provenance and update eligibility are visible in
  `vstack status`

Out of scope for this candidate:

- No external registry, hosting service, or package index
- No dependency on any external repository or version-control system
- No new runtime dependencies beyond the existing Python toolchain

### artifact integrity and verification hardening [candidate — t.b.d.]

**Objective:** establish deterministic quality guarantees for template-driven artifact generation,
lower the risk of regressions slipping through the verify loop, and give contributors clear
guidance on which checks apply after each class of change.

**Phase A — implement now:**

- Add a change-trigger validation matrix to `CONTRIBUTING.md` that maps change types to required
  checks (e.g. template change → `python3 -m vstack install` + `make test-local`).
- Expand the prompt catalog with `repo-assessment` and `artifact-integrity` prompts so engineers
  can run structured repository and drift assessments on demand.

**Phase B — generated-artifact drift guard:**

- Baseline shipped (2026-05-13): golden fixture drift tests added for
  `instruction/security`, `agent/planner`, and `prompt/code-review` rendering in
  `tests/vstack/artifacts/test_generator.py`.

- Expansion shipped (2026-05-13): golden fixture coverage now includes additional
  artifact types with deterministic fixtures for `skill/concise` and
  `instruction/testing`.

- Expansion shipped (2026-05-13): golden fixture coverage expanded again with
  deterministic fixtures for `agent/product`, `prompt/api-design-review`, and
  `skill/verify`, ensuring at least two representatives per major artifact type.

- Baseline shipped (2026-05-13): defect-fixture harness now asserts predictable
  verification failures for malformed template input (schema violation and unknown
  placeholder registry checks).

- Add golden-fixture tests that render each template to a known-good output and assert that the
  result is byte-for-byte stable.

- Add a defect-fixture harness: deliberately malformed templates that must produce specific,
  predictable error messages rather than silent failures or partial output.

- Integrate drift detection into CI: fail the check run when regenerated artifacts differ from
  committed output (equivalent to `python3 -m vstack install && git diff --exit-code`).

**Phase C — layered verify profile:**

- Baseline shipped (2026-05-13): a fixture-only fast CI job now runs targeted
  generator fixture tests (`golden_fixture` + `defect_fixture`) for quick drift
  feedback on pull requests.

- Expansion shipped (2026-05-13): local fast-path target `make test-fixtures`
  now runs fixture-only tests (`golden_fixture` + `defect_fixture`) without
  coverage gating for deterministic feedback.

- Split the verify loop into a fast deterministic tier (lint, typecheck, unit tests) and a
  deeper targeted tier (integration tests, golden fixtures, contract checks).

- Allow contributors to run the fast tier on every save and the full profile before merge.

- Surface the tier split in `CONTRIBUTING.md` and the CI workflow matrix.

#### Next follow-up steps

Tracked as dedicated candidate items in the feature status table: template-change-aware fixture CI gate, fixture update policy in PR workflow, and deeper targeted verify tier.

**Expected outcomes:**

- Contributors always know which checks to run after any class of change.
- Regressions in artifact generation are caught before they reach main.
- Structured prompt artifacts enable repeatable repo-health reviews and drift audits.
- The verify loop is both faster for day-to-day work and more thorough at the release gate.

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
