# ADR-024: Subagent Orchestration via VS Code Native Subagents

> Maintained by: **architect** role

**date:** 2026-05-09\
**status:** accepted\
**supersedes:** [ADR-004](004-option-a-to-b-pipeline.md)

## context

[ADR-004](004-option-a-to-b-pipeline.md) deferred pipeline orchestration to a future
"Option B" model, citing the absence of platform support for an agent invoking another
agent inside VS Code Copilot. The planned fallback was a `scripts/runner.py` process runner
outside the editor.

As of May 2026, VS Code Copilot ships native subagent support:

- The `runSubagent` tool lets a coordinator agent invoke a named custom agent as a
  subagent, pass it a prompt, and receive the result back in the same session context.
- The `agents:` frontmatter property in `.agent.md` restricts which custom agents a
  coordinator is allowed to invoke.
- The `user-invocable: false` property hides worker agents from the dropdown while
  keeping them available as subagents.
- Nested subagents are supported up to depth 5 (opt-in via
  `chat.subagents.allowInvocationsFromSubagents`).

The workflow contract established in [ADR-023](023-workflow-contract.md) already captures
the pipeline order (`workflow.stages`), gate policy (`gate`), human-in-the-loop policy
(`hitl`), and handoff prompts (`handoffs[].prompt`) in `.vstack/config.yaml`. All inputs
the orchestrator needs are already present.

## decision

Implement the orchestrated pipeline using the VS Code coordinator/worker subagent pattern.
Add a `planner` agent as the coordinator. The six role agents (`product`, `architect`,
`designer`, `engineer`, `tester`, `release`) continue to exist as both user-invocable
standalone agents and as subagent workers callable by the planner.

### planner agent responsibilities

1. Read the workflow contract from `.vstack/config.yaml` (`workflow.stages`).
1. Dispatch each stage in sequence by invoking the role agent as a subagent with the
   stage's `handoffs[].prompt` as the prompt.
1. After each stage completes, apply `hitl` policy:
   - `always` — pause and present the result to the user for explicit approval before
     continuing.
   - `on-change` — pause only if the subagent reports making changes; continue
     automatically if it reports no changes.
   - `never` — continue automatically without user confirmation.
1. Apply `gate` policy before dispatching:
   - `required` — always dispatch the stage.
   - `optional` — skip the stage if the subagent's domain is not affected by the current
     change; the planner assesses this from context.
   - `skip` — never dispatch the stage.

### agent frontmatter

The planner agent file includes:

```yaml
tools: ['agent', 'read_file', 'semantic_search', 'file_search']
agents: ['product', 'architect', 'designer', 'engineer', 'tester', 'release']
user-invocable: true
```

The role agents remain `user-invocable: true` so teams can still invoke them directly
without the planner. The planner is additive — it does not replace direct invocation.

### handoff prompt composition

The planner passes the stage's `handoffs[].prompt` text from `config.yaml` as the
subagent prompt. This is the same text that was previously rendered into each agent's
`handoffs:` frontmatter block. The workflow contract is therefore the single source of
truth for both the planner-driven pipeline and the manual handoff buttons.

## alternatives considered

**`scripts/runner.py` process runner (original ADR-004 plan).** A Python script outside
the editor invokes agents via the VS Code CLI or a subprocess. Rejected because the
platform now provides the same capability natively, with better context passing, model
selection, and user visibility. A process runner would also violate ADR-006 (no runtime
dependency).

**MCP server as orchestrator.** An MCP server exposes a `run_pipeline` tool that drives
stage dispatch. Rejected because it requires an external process and a network transport,
adds a runtime dependency, and provides no user experience benefit over native subagents.

**Planner-only, no direct role invocation.** Make the role agents non-user-invocable
(`user-invocable: false`) and require all use to go through the planner. Rejected because
direct invocation is the primary use pattern for teams that want focused single-role
assistance without running a full pipeline.

**Separate orchestrator skill instead of a new agent.** A skill that can be added to any
agent to give it planner behaviour. Rejected because the planner has a distinct identity,
a specific tool set, and a workflow-contract dependency that makes it a natural agent, not
a reusable skill.

## rationale

Using VS Code native subagents keeps the orchestrator inside the editor context, preserving
workspace access, model selection, and the user review loop. No external process, no new
runtime dependency (ADR-006 preserved). The coordinator/worker pattern documented by
Microsoft maps directly onto vstack's role model: one coordinator (planner), six workers
(the existing role agents).

The workflow contract from ADR-023 already carries everything the planner needs. Implementing
the planner is a template authoring task — no changes to the vstack Python package, CLI, or
generator are required.

## impact on the pipeline

The planner agent is the concrete realisation of the Option B orchestrated pipeline
described in ADR-004. The original decision to keep stage boundaries explicit and
artifacts canonical (ADR-004, "Preparation done now") is validated: those properties are
exactly what makes the subagent handoff model work without additional scaffolding.

Parallel stage execution (e.g. simultaneous security and performance tests inside
`tester`) remains deferred. It requires a `depends_on` model and prompt composition when
multiple upstream results arrive simultaneously. This is reserved for a follow-on ADR.
