# ADR-023: Workflow contract as source of truth for pipeline configuration

> Maintained by: **architect** role

**date:** 2026-05-08\
**status:** accepted

## context

vstack's six-role agent model (ADR-009) defines a sequential pipeline:
`product → architect → designer → engineer → tester → release`. Each role produces
artifacts that become the input of the next role. The pipeline can be executed manually
(a user clicks a handoff button in VS Code) or, in future, automatically by an orchestrator
agent.

Before this change, pipeline configuration was scattered and partially hardcoded:

- **Stage order** was implicit in the order that `handoffs:` entries were written in each agent's
  `config.yaml`. There was no single file that described the full pipeline.
- **Handoff targets** were encoded inside each agent's own config as `agent: <name>`. If a team
  wanted to reorder stages or insert a custom role, they had to edit multiple agent configs.
- **Handoff prompts** were tightly coupled to the next stage's name: the product agent's prompt
  said "produce or update the architecture", making it incorrect if architect was moved later in
  the pipeline.
- **Gate policy** (required vs. optional stages) did not exist as a concept; every stage was
  implicitly required.

This created a structural problem for the planned `planner` orchestrator role (ADR roadmap):
an orchestrator needs a complete, deterministic, machine-readable description of the pipeline
to dispatch subagents in order. It cannot reconstruct the pipeline by reading handoff entries
spread across six separate agent configs.

A secondary problem was the absence of any distinction between *baseline* artifacts (living docs
that must be kept current throughout a project's lifetime) and *deliverable* artifacts (output
produced per session or release, such as reports and changelogs). Agents had no explicit
instruction to maintain their baseline docs — the responsibility was implied at best.

## decision

### 1. Workflow config block in `.vstack/config.yaml`

A `workflow:` block is added to the project config schema. It is seeded once by `vstack install`
with the default six-stage pipeline and is thereafter owned by the project. `vstack init` reads
this block on every run.

```yaml
workflow:
  version: 1
  stages:
    - role: product
      gate: required
      hitl: always
      handoffs:
        prompt: >
          Product outputs are approved. Assess the current state and produce
          or update the architecture as needed. If your domain is not affected
          by this change, assess and confirm explicitly, then pass to the next stage.
    - role: architect
      gate: required
      hitl: always
      handoffs:
        prompt: >
          Architecture outputs are approved. Produce design specifications as
          needed. If your domain is not affected, assess and confirm explicitly,
          then pass to the next stage.
    - role: designer
      gate: optional
      hitl: on-change
      handoffs:
        prompt: >
          Design outputs are approved. Implement code and tests as needed. If
          your domain is not affected, assess and confirm explicitly, then pass
          to the next stage.
    - role: engineer
      gate: required
      hitl: always
      handoffs:
        prompt: >
          Implementation is approved. Verify the implementation — run tests,
          security checks, and performance analysis as needed.
    - role: tester
      gate: required
      hitl: always
      handoffs:
        prompt: >
          Verification outputs are approved. Prepare the release — produce or
          update release artifacts and sign-offs.
    - role: release
      gate: required
      hitl: always
      handoffs:
        prompt: ""
```

The `version` key allows `vstack init` to detect schema drift after a vstack upgrade and
emit a warning, without blocking the run.

`gate` values: `required` (stage always runs), `optional` (stage may be skipped when its domain
is unaffected by the current change), and `skip` (stage is never executed — explicit opt-out).

`hitl` (human-in-the-loop) values control when the pipeline pauses for human approval before the
handoff is activated:

- `always` — pipeline always pauses; the human must explicitly approve before progression
  (default for `gate: required`)
- `on-change` — pipeline pauses only when the stage made changes; if the stage reports no
  changes the pipeline may continue automatically (default for `gate: optional`)
- `never` — pipeline continues without human approval; must be set explicitly as a conscious
  opt-out

Both fields are informational in the current release (Option A) and are reserved for enforcement
by the future orchestrator (Option B). The decision of whether changes occurred is always made
by the agent and confirmed by the human — never inferred automatically.

### 2. Handoffs generated from workflow config

Agent `config.yaml` files drop the top-level `handoffs:` block. In its place, each agent carries
a `defaults.handoffs.prompt` string — the text to send to the next stage. The generator reads the
workflow config to determine the next stage's role name and combines it with the agent's
`defaults.handoffs.prompt` to produce the full handoff block in the generated `.agent.md`.

```yaml
# agent config.yaml
defaults:
  handoffs:
    prompt: >
      Product outputs are approved. Assess the current state and produce or
      update the architecture as needed.
```

When the workflow config has a `handoffs:` list for a stage, those entries drive the generated
handoffs directly; the agent's `defaults.handoffs.prompt` overrides the prompt of the first
workflow-level handoff that has no explicit `agent:` override, allowing per-template
customisation without editing the central config.

When no workflow config is present (absent or empty `workflow:` block), the generator falls back
to a generic label ("Continue to next stage") and omits the `agent:` field, preserving v3 behavior
with no breaking change.

### 3. `baseline:` flag on output artifacts

Each agent `config.yaml` output entry gains an optional `baseline: true` flag. The generator
renders flagged items into a dedicated `### baseline docs you maintain` table inside the agent's
artifacts section. Agents are explicitly instructed to keep these files current.

Artifacts without the flag are treated as deliverables — produced per session, not maintained
indefinitely.

### 4. Project-level artifact overrides — deferred

An `agents:` overlay block in `.vstack/config.yaml` (allowing teams to promote deliverables to
baseline status or adjust artifact paths without forking templates) is **not implemented** in
this decision. It is reserved as a follow-on change once the workflow contract proves stable
in practice. Until then, teams that need per-project artifact customisation should fork the
relevant agent template.

## alternatives considered

**Keep handoffs fully in agent config.yaml.** The existing approach keeps each agent
self-contained, but makes the pipeline order implicit and couples prompt text to stage names.
An orchestrator would have to reconstruct the pipeline by following handoff chains — fragile and
order-dependent. Rejected because it does not support a configurable or orchestrated pipeline.

**Separate `workflow.yaml` file in `.vstack/`.** A dedicated file would have cleaner separation
of concerns. Rejected in favor of adding a `workflow:` block to the existing `config.yaml` to
keep project configuration in one place and reduce the number of files a team must manage.

**Pipeline order as a CLI argument.** Allows ad-hoc reordering without config changes. Rejected
because pipeline preferences are stable project decisions that should survive across all
invocations (CI, local, upgrade flows) without repeating flags.

**`depends_on` for parallel stages.** Would allow independent stages (e.g., security audit and
performance test) to run in parallel. Rejected for this release: sequential execution is correct
for the current input/output dependency model. Parallel stages require a `depends_on` mechanism
and dynamic prompt composition when multiple upstream stages complete simultaneously. Reserved
for a future ADR.

## rationale

The workflow config block is the minimum necessary change to make the pipeline machine-readable
without breaking existing consumers. Teams that do not configure a `workflow:` block get identical
behavior to v3. Teams that do configure it gain a single, explicit source of truth for stage
order, gate policy, and handoff text.

Separating `handoff_prompt` (agent-owned, role-specific knowledge) from handoff target and label
(pipeline-owned, derived from workflow order) is the correct ownership boundary. The agent knows
what it produced and what context the next stage needs; it does not know which role comes next.
The workflow knows the sequence.

The `baseline:` flag addresses a recurring problem in practice: agents produced docs but had no
explicit instruction to maintain them. Making baseline status an explicit, generated instruction
inside the agent reduces the chance of stale docs accumulating unnoticed.

## impact on orchestrated pipeline

This ADR is the direct prerequisite for the `planner` orchestrator role. The planner reads
`workflow.stages` to determine dispatch order, uses `gate` to decide whether to run or skip a
stage, uses `hitl` to decide whether to pause for human approval after each stage completes, and
uses `handoffs[].prompt` as the context passed to the next subagent. No further changes to the
workflow schema are required to implement sequential orchestrated dispatch. Parallel dispatch and
`depends_on` semantics are deferred to a follow-on ADR.
