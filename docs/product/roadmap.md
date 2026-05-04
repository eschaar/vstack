# vstack — roadmap

> Maintained by: **product** role\
> Last updated: 2026-05-02

______________________________________________________________________

## feature status table

| Feature                                  | Status      | Notes                                                                                                   |
| ---------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------- |
| foundation                               | shipped     | Core template-driven install model is in place                                                          |
| backend-first verification               | shipped     | Verify/inspect focus on contracts, observability, security                                              |
| VS Code agent migration                  | shipped     | Native agent output format implemented                                                                  |
| role model + doc restructure             | shipped     | 6-role model and docs baseline established                                                              |
| new skill scaffolding                    | shipped     | 42-skill set with canonical naming                                                                      |
| agent skill wiring                       | shipped     | Role-to-skill mapping and handoffs are present                                                          |
| CLI modularisation (v2.0.0)              | shipped     | 12 focused CLI modules; BaseCommand + CommandContext contract                                           |
| manifest package (v2.0.0)                | shipped     | Dedicated `manifest/` package; atomic writes (ADR-016)                                                  |
| mypy type checking (v2.0.0)              | shipped     | Full mypy coverage enforced in CI; 100% test coverage gate                                              |
| manifest schema versioning (v2.0.0)      | shipped     | `manifest_version: 2`; upgrade path via `manifest upgrade` (ADR-014)                                    |
| checksum backfill (v2.0.0)               | shipped     | `manifest upgrade --backfill` adds SHA-256 for VSTACK-META-tagged files (ADR-017)                       |
| conservative install (v2.0.0)            | shipped     | Untracked files never overwritten; checksum-gated update (ADR-015, superseded by ADR-020)               |
| dry-run install                          | shipped     | `vstack install --dry-run` previews actions; type/name selectors in summary                             |
| project-scope directory (v3.0.0)         | shipped     | `.vstack/` directory: `config.yaml`, manifest, delta templates (ADR-019)                                |
| install/init command semantics (v3.0.0)  | shipped     | `install` = first-run setup; `init` = idempotent CI regeneration (ADR-020, breaking change)             |
| manifest relocation (v3.0.0)             | shipped     | `vstack.json` moves from `.github/` to `.vstack/`; migration via `manifest upgrade` (ADR-014)           |
| workflow contract source-of-truth        | candidate   | Defer until current template expansion is complete; then add machine-readable role workflow contract    |
| agent hooks support                      | candidate   | Generate `.github/hooks/<name>.json` from vstack templates; enforce quality gates at session boundaries |
| Copilot code review support              | candidate   | Add templates and policy defaults for requesting/configuring Copilot code review                        |
| GitHub tasks MCP-first mode              | candidate   | Add task profile for issues/PR/branch operations with MCP-first execution and safe fallback             |
| Copilot Spaces context pack              | candidate   | Add structured context packaging and refresh workflow for Copilot Spaces                                |
| content exclusion baseline               | candidate   | Ship policy templates/checklists for Copilot content exclusion at repo/org/enterprise scope             |
| MCP governance baseline                  | candidate   | Standardize MCP registry allowlist and server-access policy defaults                                    |
| Copilot Memory governance                | candidate   | Add memory enablement, review, and curation policy guidance for teams                                   |
| usage-based billing guardrails           | candidate   | Add budget/allowance/monitoring playbooks for Copilot metered usage                                     |
| Copilot admin observability pack         | candidate   | Define operational KPI and reporting cadence for adoption and usage dashboards                          |
| VS Code customization starter pack       | candidate   | Add installable templates for custom agents, instructions, prompts, and agent customization workflow    |
| template overlays + selective install    | candidate   | Combine upstream and company templates with source-priority rules and install by artifact type          |
| optional orchestrated role pipeline      | candidate   | Optional future model, only if coordination bottlenecks appear                                          |
| multi-IDE support (IntelliJ first)       | candidate   | Not planned before v1 stabilization                                                                     |
| heavy agent runtime framework            | not planned | Keeps runtime lightweight and transparent                                                               |
| cloud control plane dependency           | not planned | Keeps operation local/offline-capable                                                                   |
| VS Code extension packaging              | not planned | Not required for current install model                                                                  |
| browser automation as default dependency | not planned | Backend/microservice-first remains default                                                              |

______________________________________________________________________

## features

Legend: shipped = implemented and available; candidate = optional future feature (not committed); not planned = evaluated and intentionally excluded for now.

### foundation [shipped]

- template-driven generation with source under `src/vstack/_templates/` and install output under `.github/`
- 42 backend-oriented skills
- generated install manifest (`.vstack/vstack.json`) tracking installed artifacts
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

39 skills across 6 roles. Representative additions:

- `requirements`, `adr`, `analyse` (new)
- `gh-issues`, `codeql`, `dependabot`, `secret-scan`
- `gdpr`, `terraform`, `terragrunt`, `cloudformation`, `aws-cli`
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

### conservative install [shipped — v2.0.0]

- Untracked files are never overwritten by default (ADR-015)
- Checksum-gated `--update` mode: only rewrites clean tracked files
- `--force-name` / `--adopt-name` accept `type/name` selectors (e.g. `agent/engineer`)
- `--dry-run` previews all actions with a summary and preserved-selectors list

______________________________________________________________________

### optional orchestrated role pipeline [candidate]

Possible future workflow with explicit orchestration (only if real coordination bottlenecks appear):

- Each role makes its own model call
- Artifacts pass between roles via disk files
- User gates pause the pipeline at defined checkpoints
- Orchestrator role (product) manages pipeline state
- Parallel execution possible for multiple tester passes

See `docs/design/workflow.md` for current execution and the orchestrated future model.

### workflow contract source-of-truth [candidate]

Deferred until the current templates expansion is complete.

Planned direction:

- Keep one machine-readable workflow contract describing role inputs, outputs, gates, and handoffs.
- Use that contract to keep agent workflow sections and checks aligned.
- Keep `docs/design/workflow.md` as the human-readable explanation layer.

This reduces drift risk between agent behavior and workflow documentation while keeping skills and instructions generic.

### multi-IDE support [candidate]

IntelliJ is the first candidate beyond VS Code. Not planned until after v1 stabilization.

### agent hooks support [candidate]

GitHub Copilot agents support a repository-level hooks mechanism: shell commands defined in `.github/hooks/<name>.json`
that execute at key points during an agent session — `sessionStart`, `sessionEnd`, `userPromptSubmitted`,
`preToolUse`, `postToolUse`, and `errorOccurred`.

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
- Note: the per-agent `hooks` frontmatter field (already supported) is separate — it scopes hooks to one agent; repository hooks apply to all agent sessions

Ref: [GitHub — Customize agent workflows with hooks](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/use-hooks)

### Copilot code review support [candidate]

Relevance:

- Copilot code review is now a dedicated workflow with setup and configuration needs.
- Teams need clear defaults for when review is advisory versus blocking.
- Runner and policy setup should be documented as reusable project artifacts.

Planned direction:

- Add templates/checklists for enabling and configuring Copilot code review.
- Add policy defaults for review severity handling and escalation paths.
- Add runner guidance for repository/org-level rollout.

Ref: [GitHub — Code review](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review)

### GitHub tasks MCP-first mode [candidate]

Relevance:

- Copilot can perform GitHub tasks directly (issues, PRs, branches) with MCP integration.
- Teams need predictable, safe defaults for operational GitHub actions in agent workflows.
- MCP-first task execution can reduce glue scripting while preserving auditable actions.

Planned direction:

- Add a GitHub-tasks profile/skill with MCP-first behavior.
- Add safe fallback to `gh` CLI when MCP capability is unavailable.
- Add guardrails for sensitive actions (merge/close/delete) with explicit confirmation rules.

Ref: [GitHub — Copilot for GitHub tasks](https://docs.github.com/en/copilot/how-tos/copilot-on-github/copilot-for-github-tasks)

### Copilot Spaces context pack [candidate]

Relevance:

- Copilot Spaces provides curated context for higher-quality responses.
- Teams need a repeatable way to map project artifacts into Space-friendly context bundles.
- Without a packaging pattern, context quality drifts across repositories and teams.

Planned direction:

- Add a context-pack template that maps core docs/artifacts into a stable Space feed.
- Add refresh procedures so context remains synchronized with baseline docs and releases.
- Add quality checks for stale or missing context entries.

Ref: [GitHub — Copilot Spaces](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/copilot-spaces)

### content exclusion baseline [candidate]

Relevance:

- Copilot content exclusion is now a first-class admin control at repository, organization, and enterprise scope.
- Teams need consistent patterns for excluding sensitive paths (for example: secrets, generated artifacts, legal-restricted data).
- A policy baseline prevents ad hoc exclusions and avoids accidental over-exclusion that harms developer experience.

Planned direction:

- Add installable content-exclusion policy templates and review checklist artifacts.
- Provide path-pattern conventions and anti-patterns for repository and org scope.
- Add validation guidance and rollout checks to avoid silent misconfiguration.

Ref: [GitHub — Excluding content from GitHub Copilot](https://docs.github.com/en/copilot/how-tos/configure-content-exclusion/exclude-content-from-copilot)

### MCP governance baseline [candidate]

Relevance:

- MCP server usage now has organization/enterprise governance controls.
- Without governance defaults, teams can connect inconsistent or untrusted MCP servers.
- A baseline improves security posture and keeps tool access predictable across repositories.

Planned direction:

- Add a governance-focused instruction/template pack for MCP registry and access policy.
- Define default allowlist/denylist patterns and review ownership.
- Include onboarding checks for newly proposed MCP servers.

Ref: [GitHub — Managing MCP usage in your company](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-mcp-usage)

### Copilot Memory governance [candidate]

Relevance:

- Copilot Memory affects cloud agent, code review, and CLI behavior quality.
- Feature is preview and policy-sensitive, so teams need explicit enablement and curation rules.
- Memory hygiene avoids stale, misleading, or sensitive memories degrading output quality.

Planned direction:

- Add memory policy templates (enablement defaults, owners, and review cadence).
- Add curation guidance for viewing/deleting repository memories.
- Add short operational guidance for teams with mixed org/enterprise policy inheritance.

Ref: [GitHub — Managing and curating Copilot Memory](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/copilot-memory)

### usage-based billing guardrails [candidate]

Relevance:

- Copilot billing is moving to usage-based models; teams need predictable spend controls.
- Without guardrails, premium-request usage can spike unexpectedly.
- Operational usage visibility is required for sustainable adoption.

Planned direction:

- Add spend-control playbooks (budgets, allowance policies, and alert thresholds).
- Add monthly usage review checklist and optimization guidance for model/task selection.
- Add references for organization vs enterprise ownership boundaries.

Ref: [GitHub — Monitoring your GitHub Copilot usage and entitlements](https://docs.github.com/en/copilot/how-tos/manage-and-track-spending/monitor-premium-requests)

### Copilot admin observability pack [candidate]

Relevance:

- Copilot adoption at scale needs explicit operational KPIs and recurring review loops.
- Admin dashboards and reports exist, but teams need standardized interpretation and actions.
- Consistent observability improves rollout quality and policy compliance.

Planned direction:

- Add an admin operations pack for usage/adoption KPI definitions and cadence.
- Add a standard reporting checklist for org and enterprise owners.
- Add escalation triggers for unusual usage patterns and policy drift.

Ref: [GitHub — Administer GitHub Copilot for your team](https://docs.github.com/en/copilot/how-tos/administer-copilot)

### VS Code customization starter pack [candidate]

Relevance:

- Teams repeatedly ask how to create custom agents, custom instructions, prompts, and skills in VS Code.
- vstack already generates these artifact types, but onboarding the customization model can be clearer.
- A starter pack lowers adoption friction and keeps customization patterns consistent.

Planned direction:

- Add a dedicated starter package with guided templates for custom agents, custom instructions, prompts, and skills.
- Include step-by-step examples for common workflows (domain agent, policy instruction, task prompt).
- Add a focused skill/instruction pair that teaches and validates Copilot customization patterns inside VS Code.

Ref: [GitHub — Customize Copilot for your project](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-copilot-overview)

### template overlays + selective install [candidate]

Relevance:

- Teams often need a company-specific Copilot stack rather than the default vstack set.
- A practical model is: keep upstream vstack as baseline, then layer private templates and extensions on top.
- Adoption is blocked when teams cannot control which artifact types are installed (`agents`, `skills`, `prompts`, `instructions`) or which source wins on conflicts.

Planned direction:

- Add support for multiple template sources in priority order (for example: upstream vstack first, company repo second).
- Define deterministic conflict resolution rules: `prefer-local`, `prefer-upstream`, and explicit `replace`/`extend` behavior per artifact.
- Add install selectors for coarse-grained artifact types (`--types agents,skills,prompts,instructions`) and optional fine-grained name selectors.
- Add install profiles in config/manifest (for example: `baseline`, `company`, `minimal`) to make repeat installs deterministic.
- Keep checksum/manifests source-aware so updates can be applied safely per origin.

Initial UX target:

- `vstack install --source upstream=... --source company=... --prefer company`
- `vstack install --types agents,skills`
- `vstack install --profile company`

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
