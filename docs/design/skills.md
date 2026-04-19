# vstack — skills

> Maintained by: **designer** role\
> Last updated: 2026-04-16\
> VS Code docs: [agent skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)

## what are skills?

Skills are the HOW of vstack. Each skill is a reusable procedure that agents (the WHO) apply to a task. A skill defines steps, methodology, and expected outputs — it is agnostic to which role invokes it.

In VS Code, skills are [Agent Skills](https://agentskills.io/) — an open standard. Each skill is a directory with a `SKILL.md` file. Copilot loads a skill automatically when the task matches its `description`, or you invoke it manually with `/skill-name` in chat.

**Conceptual model:**

- **WHO** = agent role (product, architect, designer, engineer, tester, release)
- **HOW** = skill (verify, adr, design, explore, …)
- **WHAT** = input task + artifact files on disk

Canonical names are the source of truth. Historical or compatibility aliases should
remain exceptional and temporary. See `docs/architecture/adr/002-artifact-naming-and-compatibility-policy.md`.

## why skills (vs custom instructions)

Unlike custom instructions that primarily define coding preferences and guardrails,
skills package specialized, reusable workflows with optional scripts, examples,
and references.

Key benefits:

- Specialize Copilot for domain-specific tasks without repeating context.
- Reduce repetition by defining a capability once and reusing it automatically.
- Compose capabilities by combining multiple skills into one larger workflow.
- Keep context efficient through progressive disclosure (metadata first, then
  instructions, then resources on demand).

______________________________________________________________________

## current skills

| Skill           | Description                                                                                                                                         | Primary role(s)                                         | Output artifact                             |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------- |
| `vision`        | CEO/founder-mode plan review. Rethink from first principles, validate ambition, find the 10x solution.                                              | product                                                 | `docs/product/vision.md`                    |
| `requirements`  | Collaborative requirements gathering. Clarifies what must be built, defines success criteria and NFRs.                                              | product                                                 | `docs/product/requirements.md`              |
| `architecture`  | Engineering-lead plan review. Lock in service boundaries, data models, API contracts, test strategy.                                                | architect                                               | `docs/architecture/architecture.md`         |
| `adr`           | Architecture Decision Record writing. Documents a decision with context, alternatives, and rationale.                                               | architect                                               | `docs/architecture/adr/NNN-*.md`            |
| `design`        | Build a complete API or service design from scratch. Produces OpenAPI specs, error conventions, naming standards.                                   | designer                                                | `docs/design/design.md` / `openapi.yaml`    |
| `consult`       | DX triage and focused review. Routes to one path (API DX, CLI/tool DX, or developer workflow DX) and routes non-DX requests to specialized skills.  | designer                                                | focused DX report or routing recommendation |
| `concise`       | Runtime response-style controller. Switches response density (`normal`, `compact`, `ultra`) and reports active mode via `status` without reinstall. | all roles                                               | session style state + status output         |
| `code-review`   | Pre-landing code review. Finds bugs that pass CI but break in production — race conditions, security issues, performance landmines.                 | engineer                                                | inline findings                             |
| `security`      | OWASP Top 10 + STRIDE security audit. Finds auth bypasses, injection flaws, exposed secrets, broken access control.                                 | engineer                                                | security audit report                       |
| `explore`       | Repository and system discovery. Maps the architecture, identifies tech debt, produces an onboarding summary.                                       | engineer                                                | codebase map                                |
| `analyse`       | Cross-cutting technical analysis. Investigates impact, tradeoffs, root causes, or feasibility without implementing changes.                         | engineer, architect                                     | analysis report                             |
| `debug`         | Systematic root-cause debugging. Follows scientific method: observe → hypothesise → test → conclude → fix → prevent.                                | engineer                                                | root cause report + fix                     |
| `inspect`       | Read-only verification audit. Runs baseline plus optional extended checks and produces severity-ranked findings, with no code or commit changes.    | tester                                                  | read-only audit report                      |
| `performance`   | Performance profiling and regression detection. Establishes baselines, detects regressions, profiles bottlenecks.                                   | engineer, tester                                        | perf report                                 |
| `verify`        | Verification fix-loop with mode routing (quick/standard/exhaustive). Runs targeted checks, fixes by severity, and re-verifies impacted paths.       | engineer, tester                                        | fixes + verification report                 |
| `cicd`          | Write GitHub Actions CI/CD workflow configuration. Covers build, test, lint, security scan, container publish, deploy.                              | release                                                 | GitHub Actions workflow                     |
| `container`     | Write and review Dockerfile, docker-compose, and container config. Covers multi-stage builds, non-root users, layer optimisation.                   | engineer                                                | Dockerfile + compose                        |
| `release-notes` | Prepare release artifacts: write release notes, own CHANGELOG updates, produce `docs/releases/{date}.md`.                                           | release                                                 | CHANGELOG + release doc                     |
| `pr`            | Commit, push, and open a pull request from the current branch to main.                                                                              | release                                                 | commit + PR                                 |
| `docs`          | Post-release documentation alignment for README/API docs/migrations and related artifacts (no CHANGELOG ownership).                                 | product, architect, designer, engineer, tester, release | updated docs artifacts                      |
| `guardrails`    | Activate safety guardrails for the session. Requires explicit confirmation before any destructive action.                                           | —                                                       | (mode activation)                           |
| `migrate`       | Database migration review and authoring. Forwards/backwards compatibility, zero-downtime strategies, rollback plans, data integrity, index safety.  | engineer, tester                                        | reviewed/corrected migration SQL            |
| `openapi`       | Write and review OpenAPI 3.1 specifications. Resource naming, HTTP semantics, status codes, error conventions, pagination, security schemes.        | designer, engineer                                      | `openapi.yaml`                              |
| `refactor`      | Structured refactoring without behavior change. Identify smells, plan incremental steps, execute, verify correctness.                               | engineer                                                | refactored code + green tests               |
| `onboard`       | Generate a contributor onboarding guide. Prerequisites, setup, tests, env vars, architecture overview, good first issues.                           | product                                                 | `CONTRIBUTING.md` + README dev section      |
| `dependency`    | Dependency health audit. Vulnerability scanning, outdated packages, licence compliance, transitive risk, pinning policy, supply chain hygiene.      | engineer, tester                                        | dependency audit report                     |
| `incident`      | Incident analysis and blameless post-mortem writing. Timeline reconstruction, 5-Whys root cause, contributing factors, action items.                | tester, engineer                                        | `docs/postmortems/YYYY-MM-DD-*.md`          |

______________________________________________________________________

## file locations

| Path                                              | Purpose                                                                    |
| ------------------------------------------------- | -------------------------------------------------------------------------- |
| `src/vstack/_templates/skills/<name>/config.yaml` | Source of truth — skill frontmatter fields                                 |
| `src/vstack/_templates/skills/<name>/template.md` | Source of truth — skill instructions body                                  |
| `src/vstack/_templates/skills/_partials/*.md`     | Shared partials injected via `{{TOKEN}}`                                   |
| `.github/skills/<name>/SKILL.md`                  | Generated output — what VS Code loads                                      |
| `.github/vstack.json`                             | Generated install manifest and artifact index (including installed skills) |

**Never edit `.github/skills/` directly.** Regenerate after every change:

```bash
vstack install
```

______________________________________________________________________

## template.md structure

Skill templates use the same split model as agents:

- `config.yaml` contains skill metadata/frontmatter fields.
- `template.md` contains only skill instructions body.

The generator reads `config.yaml` and emits recognised fields as frontmatter in generated `SKILL.md`.

```markdown
{{SKILL_CONTEXT}}

## Your skill instructions here
```

```yaml
name: architecture
version: 1.0.1
description: |
  Engineering-lead plan review. Lock in the execution plan — service boundaries,
  data models, API contracts, error handling, test strategy, ...
argument-hint: '[plan or system to review]'
```

The `{{SKILL_CONTEXT}}` token is replaced with the shared `_partials/skill-context.md` at generation time.

### authoring-only guidance vs runtime guidance

Authoring guidance belongs in this document (or README), not in every runtime skill body.
Keep generated `SKILL.md` files focused on execution steps.

Put in docs (author-facing):

- writing standards for skill templates
- minimum skill contract/checklists for authors
- rationale and design principles for maintainers

Put in runtime skills (model-facing):

- actionable procedure for the current task
- concrete commands and expected output structure
- explicit escalation and failure behavior

______________________________________________________________________

## frontmatter fields

| Field                      | Type               | Required | Notes                                                                                                                |
| -------------------------- | ------------------ | -------- | -------------------------------------------------------------------------------------------------------------------- |
| `name`                     | string             | **yes**  | Lowercase kebab-case. Must match the directory name. Max 64 chars. Also the `/slash-command` name in chat.           |
| `description`              | string             | **yes**  | What the skill does and when to use it. Copilot uses this for auto-loading decisions. Max 1024 chars (vstack limit). |
| `license`                  | string             | no       | Optional license name or reference to bundled license file.                                                          |
| `compatibility`            | string             | no       | Optional environment requirements. Max 500 chars.                                                                    |
| `metadata`                 | mapping (raw YAML) | no       | Optional arbitrary key/value metadata.                                                                               |
| `argument-hint`            | string             | no       | Shown after `/skill-name` in the chat input. E.g. `[plan or system to review]`.                                      |
| `user-invocable`           | bool               | no       | `true` (default) = appears in the `/` slash command menu. Set `false` for background-only skills.                    |
| `disable-model-invocation` | bool               | no       | `true` = Copilot will never auto-load this skill; only accessible via `/skill-name`.                                 |

`version` is maintained in `config.yaml` for vstack install/update tracking and is not emitted into generated `SKILL.md` frontmatter.

`allowed-tools` is currently not emitted by vstack because support is inconsistent across target agents.

`name` must satisfy the Agent Skills naming rules enforced by vstack: lowercase kebab-case, no leading/trailing hyphen, max 64 characters.

### how user-invocable and disable-model-invocation interact

| `user-invocable` | `disable-model-invocation` | In `/` menu | Auto-loaded                    |
| ---------------- | -------------------------- | ----------- | ------------------------------ |
| `true` (default) | `false` (default)          | ✅          | ✅ General-purpose skills      |
| `false`          | `false`                    | ❌          | ✅ Background knowledge skills |
| `true`           | `true`                     | ✅          | ❌ On-demand only              |
| `false`          | `true`                     | ❌          | ❌ Disabled                    |

______________________________________________________________________

## how Copilot loads skills

1. **Discovery** — Copilot reads `name` + `description` from frontmatter to decide if the skill is relevant.
1. **Instructions loading** — The `SKILL.md` body is loaded into context when the skill is selected (auto or manual).
1. **Resource access** — Any extra files in the skill directory (scripts, examples) are only loaded when referenced in the body.

This three-level loading keeps context lean — many skills can be installed without overhead.

______________________________________________________________________

## minimum skill body contract

We hanteren dit als minimum voor elke skill body:

1. What it helps accomplish
1. When to use it
1. Step-by-step procedure
1. Expected input/output examples
1. References to scripts/resources
1. Out-of-scope + escalation/failure rules
1. Common edge cases (sterk aanbevolen)

Recommended additions for production-grade skills:

1. **Assumptions/prerequisites** (required tools, environment, permissions).
1. **Completion checklist** (definition of done).
1. **Fallback behavior** when required context is missing.
1. **Explicit file references** to scripts/resources using relative paths from skill root (for example: `scripts/run.sh`, `references/REFERENCE.md`).

Recommended skill directory layout:

- `SKILL.md` (generated from `config.yaml` + `template.md`)
- `scripts/` (executable helpers)
- `references/` (on-demand deep documentation)
- `assets/` (templates, sample data, static resources)

This aligns with progressive disclosure: keep `SKILL.md` focused (instructions body under about 5000 tokens; target under 500 lines), and move detailed material into `references/`, `scripts/`, or `assets/`.

## search and context hygiene

Skill templates should avoid scanning dependency/generated trees unless explicitly requested.
Prefer commands that exclude:

- `.venv/`, `venv/`, `env/`
- `node_modules/`
- `__pycache__/`
- `dist/`, `build/`
- `.git/`

Example grep pattern:

```bash
grep -r -n "pattern" . \
  --exclude-dir=.venv \
  --exclude-dir=venv \
  --exclude-dir=env \
  --exclude-dir=node_modules \
  --exclude-dir=__pycache__ \
  --exclude-dir=dist \
  --exclude-dir=build \
  --exclude-dir=.git
```

______________________________________________________________________

## adding a new skill

1. Create `src/vstack/_templates/skills/<name>/config.yaml` with `name`, `version`, and `description`.
1. Create `src/vstack/_templates/skills/<name>/template.md` with a body that includes `{{SKILL_CONTEXT}}`.
1. Add `<name>` to `EXPECTED_CANONICAL_NAMES` in `src/vstack/cli/constants.py`.
1. Regenerate: `vstack install`
1. Verify: `python3 -m pytest tests/ -q`
1. Update the skills table above.

______________________________________________________________________

## validation

```bash
vstack verify   # check all skill templates
python3 -m pytest tests/ -q  # full test suite
```
