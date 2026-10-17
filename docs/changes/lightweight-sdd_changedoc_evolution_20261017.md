# Lightweight SDD Through Changedoc Evolution

## Metadata

```yaml
status: CONCEPT
type: feature
reference: user-request-20261017-lightweight-sdd
last_modified: 2026-10-17
```

## Goal and Context

Make vstack more specification-driven by extending its existing changedoc and
role workflows, not by introducing a second specification system.

The user requested a proposal that demonstrates the intended approach itself:
requirements, acceptance criteria, execution planning, and verification in one
living change document. This document is that proposal, not authorization to
implement it.

The intended outcome is stronger agreement on what changes and how correctness
is demonstrated, without mandatory ceremony, additional dependencies, or fixed
role sequences for ordinary developer work.

### Constraints

- Reuse existing skills, roles, documentation, and lifecycle states.
- Keep the default workflow lightweight and VS Code-native.
- Respect explicit project policies, configured gates, and human approvals.
- Treat requirements as intent, not as a substitute for tests or review.
- Keep proposal validation separate from future implementation verification.

### Out of Scope

- New CLI commands, CI gates, dependencies, workflow configuration, or databases.
- Automatic specification parsing, approval signatures, or revision hashing.
- New roles, a mandatory task tracker, or external workflow compatibility layers.
- Mandatory documents, branches, or full pipelines for every task.
- Rewriting historical changedocs or changing installer ownership semantics.

## AS-IS

### Functional

- The [changedoc skill](../../src/vstack/_templates/skills/changedoc/template.md)
  requires AS-IS, TO-BE, impact, acceptance criteria, and test scenarios.
- Its [document template](../../src/vstack/_templates/agents/product/artifacts/changes/changedoc.md)
  has no explicit requirements, execution tasks, or verification outcome section.
- Changedoc status already distinguishes `CONCEPT`, `BUILD`, `IMPLEMENTED`,
  and `ARCHIVED`.
- The [planner](../../src/vstack/_templates/agents/planner/template.md) defaults
  to focused routing, but also broadly requires a changedoc in `BUILD` before
  implementation of existing-repository changes.
- The [product role](../../src/vstack/_templates/agents/product/template.md)
  similarly prescribes changedoc creation for existing repositories.
- Requirements, design, verification, and release responsibilities exist, but
  their connections are mostly narrative rather than criterion-specific.
- The [analyse skill](../../src/vstack/_templates/skills/analyse/template.md)
  supports technical investigation but has no explicit change-consistency path.
- [Inspect](../../src/vstack/_templates/skills/inspect/template.md) and
  [verify](../../src/vstack/_templates/skills/verify/template.md) focus on checks
  and findings. Their default baseline report policy needs alignment with
  lightweight evidence in an existing changedoc or response.

### Technical

- The [requirements skill](../../src/vstack/_templates/skills/requirements/template.md)
  supports functional requirements and measurable quality attributes.
- The [stage report contract](../../src/vstack/_templates/agents/_partials/stage-report-contract.md)
  reports readiness and blockers, without a required acceptance-evidence mapping.
- The [CLI catalog](../../src/vstack/cli/catalog.py) exposes artifact validation
  and installation checks, not semantic compliance checks for consumer software.
- [Installation](../../src/vstack/cli/install.py) seeds role artifact templates
  additively. Existing local copies are not automatically replaced.
- Role workflow configuration already defines dependencies and gates. This
  proposal must not introduce conflicting orchestration semantics.

## TO-BE

### Working Model

Use four questions throughout delivery:

1. What changes?
1. What makes the result acceptable?
1. How will we verify it?
1. What remains unresolved?

For changes needing a durable specification, answer them in one changedoc.
For small, clear tasks, an existing issue or conversation can supply sufficient
context. Do not create another document solely to satisfy the procedure.

Requirements describe obligations; acceptance criteria define observable
completion; test scenarios describe how to check it; verification records what
actually happened. Avoid repeating the same prose in every section.

### Proportional Structure

| Situation                                      | Recommended structure                                           |
| ---------------------------------------------- | --------------------------------------------------------------- |
| Small, clear, low-risk task                    | Existing issue or conversation with outcome and verification    |
| Change needing durable scope or handoff        | Changedoc with requirements, acceptance criteria, and scenarios |
| Change with meaningful execution dependencies  | Add a compact task list to that changedoc                       |
| Complex design, migration, or operational risk | Link focused supporting material and involve relevant roles     |

These are guidance, not new configured modes or size thresholds.
Use risk, ambiguity, handoffs, and the user's preference rather than line counts.
An explicit request for a changedoc is sufficient reason to create one.

Security-sensitive behavior, destructive operations, and compatibility changes
require appropriate clarification and verification regardless of task size.
Small scope does not justify bypassing existing safety or approval policies.

### Requirements

The local identifiers below help review this multi-surface change. They are not
a proposed requirement for all future tasks, and add no document-level ID.

| Requirement | Obligation                                                                                                                                                                                                                               |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R-1         | Extend the existing changedoc with change-local requirements, optional execution tasks, and verification outcomes. Do not require separate per-change spec or requirements files.                                                        |
| R-2         | Allow focused, low-risk work to use sufficient existing issue or conversation context without creating a changedoc or running every role. Explain escalation when context or risk warrants it.                                           |
| R-3         | Use local criterion references when they improve handoffs or evidence mapping. Preserve established references during revisions; do not require global IDs or renumber existing criteria casually.                                       |
| R-4         | Plan tasks only when useful. Record real prerequisites, not artificial dependencies created by list order or role names. Allow iterative work and multiple changes on one branch.                                                        |
| R-5         | Before implementation, establish clear scope, observable acceptance, and resolution of blocking questions. Ask only for decisions that materially affect correctness, risk, scope, or approval.                                          |
| R-6         | Report relevant verification as passed, failed, not run, or no longer current. Include the check and result or an explicit limitation; never equate a task checkbox or codecoverage with acceptance.                                     |
| R-7         | Reassess affected criteria and evidence after material scope or behavior changes. Seek renewed approval only when the approved scope, risk, or project policy requires it.                                                               |
| R-8         | Preserve baseline ownership and existing workflow policy. Update system-level baselines only when shared behavior or contracts change, and link instead of duplicating authoritative content.                                            |
| R-9         | Keep this increment template- and documentation-driven, with no new runtime tooling, dependencies, configuration, or automated enforcement.                                                                                              |
| R-10        | Keep existing changedocs and customized seeded templates usable. Do not overwrite local content or require historical backfill. Explain how to adopt the additional guidance.                                                            |
| R-11        | Clarify material ambiguity using repository evidence first, then focused questions. Record accepted answers in the existing intent source and review only relevant requirement-quality dimensions.                                       |
| R-12        | Offer a scoped, non-mutating consistency review of requirements, criteria, contracts, and useful tasks through an existing skill. Distinguish missing coverage, contradictions, and unsupported additions.                               |
| R-13        | Compare implemented behavior with agreed intent, not only the changed lines or task checkboxes. Bound remediation, preserve scope ownership, and stop when approval, missing evidence, or repeated lack of progress prevents completion. |
| R-14        | Select independently verifiable delivery slices when useful. Include relevant error, compatibility, data-lifecycle, and operational behavior without requiring a universal checklist or new documentation tree.                          |

### Clarification and Quality Review

Read existing decisions and code before asking questions. Identify the
highest-impact uncertainty, explain why it matters, and ask one question at a
time. Do not repeat answered questions or invent a fixed interview quota.
Record accepted answers in the current changedoc or issue; for conversation-only
work, confirm the updated intent in the conversation.

For the relevant scope, consider observable outcomes, terminology, boundary and
failure behavior, measurable quality attributes, and assumptions. Review the
quality of the requirements separately from testing the resulting implementation.
An optional short checklist belongs in the existing document or response, not a
mandatory new file. A successful wording review is not implementation evidence.

Keep user outcomes separate from implementation choices unless an existing
constraint requires a particular solution. For a larger feature, prefer useful,
independently verifiable slices; do not force that decomposition on a tightly
coupled migration or small fix.

### Consistency and Completion Review

Use `analyse` for an explicitly requested or risk-justified consistency review
before implementation. Read only relevant intent, baseline constraints,
contracts, and tasks. Identify contradictions, uncovered obligations, vague
criteria, and additions without a clear requirement or engineering rationale.
Report the source, consequence, and proposed next action in the current response
or document as authorized. Do not silently rewrite intent or create a mandatory
standalone analysis report.

Use `inspect` for assessment and `verify` for an authorized fix loop after
implementation. Assess actual in-scope behavior against acceptance, including
required work absent from the diff. Separate behavioral gaps, conflicting
behavior, unexplained additions, and evidence that could not be obtained.
An unexplained addition is a review question, not permission to delete code;
necessary implementation details need not each become a product requirement.

Fix within the authorized scope and rerun affected checks. Update a useful task
list rather than producing an append-only history of remediation phases.
Do not relax criteria to match the implementation. Stop and report the blocker
when progress repeats without new evidence, required checks cannot run, or
resolution needs a scope or policy decision. Honor any existing user/project
iteration budget. No new budget configuration is introduced.

### Readiness and Completion

Readiness is a short assessment, not a mandatory report or extra meeting:
scope is understood, acceptance is observable, and blocking questions are resolved.
Non-blocking assumptions may remain if they are explicit and do not conceal risk.

For a changedoc, retain the existing lifecycle:

- `CONCEPT`: proposal or discovery; not approved for implementation.
- `BUILD`: implementation authorized under the applicable project policy.
- `IMPLEMENTED`: agreed scope completed and verified with relevant evidence.
- `ARCHIVED`: closed and retained for history; not a synonym for successful delivery.

Do not treat these states as an ordered numeric threshold.
In particular, `ARCHIVED` does not authorize implementation.

Record missing checks and residual risks explicitly. A required failed or
unexecuted check prevents claiming full verification. Any exception must name
the limitation and its approval under the project's policy, rather than report
the criterion as passed. Product outcomes that require production observation
remain identified as follow-up outcomes, not falsely verified release checks.

After a relevant code or intent change, identify which evidence needs rerunning.
Do not invalidate unrelated work or restart the full pipeline automatically.
Use a reviewed commit when available, otherwise describe the reviewed working
tree and scope; no new revision-tracking mechanism is required.

### Ownership and Adoption

- Product owns scope and acceptance; other roles contribute within their domain.
- Engineer may maintain implementation tasks and verification notes without
  rewriting product intent. Escalate requirement changes to the scope owner.
- Tester records or reviews evidence when involved; release uses that evidence
  without requiring a duplicate report for every small change.
- Extend existing instructions in the relevant skills and roles. Do not add
  separate clarify, task, or convergence skills for this increment.
- Keep the exact shared stage report schema unchanged. Reference the changedoc
  through existing report fields rather than adding mandatory evidence fields.
- Treat existing consumer changedocs as valid. Supplement an older local
  template through guidance when creating a new document; do not overwrite it.

### Artifact Changes

Improve existing surfaces rather than introduce new skills, instructions, or
agents in this increment. Reuse a small shared partial only if implementation
reveals genuinely repeated procedural content; avoid a new abstraction upfront.

| Surface                                                                             | Proposed improvement                                                                                                                                                                              |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `changedoc` skill and product document template                                     | Add requirements, optional tasks, and evidence; keep clarification decisions in the same document.                                                                                                |
| `requirements` skill                                                                | Support change-local intent without always creating a system requirements baseline; clarify by impact and review testability and missing behavior.                                                |
| `analyse` skill                                                                     | Add a bounded consistency-review path; preserve its no-implementation boundary and allow findings in the existing response/document.                                                              |
| `inspect` and `verify` skills                                                       | Add intent-to-behavior assessment, explicit evidence gaps, proportionate report placement, and bounded remediation. Preserve report-only versus fix-loop behavior.                                |
| Product and planner agents                                                          | Select appropriate structure and relevant roles; carry resolved scope, blockers, and acceptance references in existing handoff fields.                                                            |
| Architect and designer agents                                                       | When involved, connect relevant constraints and contracts to acceptance; expose conflicts and relevant failure cases without demanding unrelated baseline expansion.                              |
| Engineer agent                                                                      | Implement useful verifiable slices, reuse existing behavior and helpers, and report scope deviations rather than silently widening acceptance.                                                    |
| Tester and release agents                                                           | Distinguish requirements quality from proven behavior; consume relevant evidence and report residual risk without manufacturing duplicate reports or approvals.                                   |
| [Testing instruction](../../src/vstack/_templates/instructions/testing/template.md) | Add only durable test policy: derive tests from observable criteria, cover relevant failure boundaries, and distinguish codecoverage from acceptance coverage. Keep workflow procedure in skills. |

Baseline reports remain authoritative when required by project policy or
cross-change reporting. For focused work without that requirement, evidence may
stay in the changedoc or response. Reconcile these choices explicitly in
`inspect` and `verify`; do not retain contradictory blanket report requirements.
No new always-on SDD instruction is needed.

## Impact (High Level)

- Architecture/boundaries: preserve the role model, artifact families, and
  baseline-first ownership. No additional source of truth.
- API/data/model: preserve CLI, manifest, workflow configuration, shared stage
  report schema, and changedoc metadata. Additional prose sections are additive.
- Security/privacy: retain project safety gates and approvals. Store sanitized
  evidence references, not secrets, credentials, or raw sensitive logs.
- Operations/observability: require measurable operational evidence when it is
  relevant to acceptance, not for every documentation or maintenance task.
- Compatibility: old documents require no migration. Existing configured gates
  and stage dependencies remain authoritative when a pipeline is used.
- Option B: future orchestration can consume explicit criteria and evidence
  references, but this increment does not claim machine-enforced compliance.
- Documentation: update the skill catalog, workflow/design guidance, and
  relevant product requirements/roadmap to describe the agreed behavior.
  Record a scoped ADR for the changedoc-as-spec and proportional-routing decision
  when approved; do not create an ADR for this unapproved proposal.
- Regeneration: update source templates and regenerate installed artifacts with
  `vstack install` during implementation; never manually patch generated output.

## Acceptance Criteria

| Criterion | Requirements  | Observable result                                                                                                                                                                                    |
| --------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-1      | R-1, R-3      | A representative feature uses one changedoc for requirements, criteria, optional tasks, and evidence, with unambiguous local references and no duplicate spec document.                              |
| AC-2      | R-2, R-4, R-9 | A clear low-risk fix proceeds from an issue or conversation with focused implementation and verification, without a new changedoc, task registry, or full role pipeline.                             |
| AC-3      | R-2, R-5, R-8 | An ambiguous or high-risk change identifies blockers and involves the relevant owner before affected implementation, while preserving configured approvals.                                          |
| AC-4      | R-4, R-8      | Independent tasks have no invented prerequisites; a configured multi-role pipeline still follows its declared dependencies and gates.                                                                |
| AC-5      | R-6           | Completion identifies evidence or an explicit gap for applicable criteria. Failed or unexecuted required checks are not reported as passed or fully verified.                                        |
| AC-6      | R-3, R-7      | A material requirement or behavior revision preserves existing references, identifies affected tasks/evidence, and triggers only the necessary rework and approval.                                  |
| AC-7      | R-8           | Changed system-level behavior updates the relevant baseline without copying it into a parallel specification tree; change-local details remain in the changedoc.                                     |
| AC-8      | R-9, R-10     | Adoption adds no dependencies, CLI commands, configuration keys, mandatory stage-report fields, or automatic gates. Existing local templates and historical documents remain intact.                 |
| AC-9      | R-1, R-2, R-5 | Changedoc skill, product/planner instructions, role guidance, and documentation agree on proportional scope and lifecycle; archived documents never authorize new implementation.                    |
| AC-10     | R-11          | A vague requirement triggers an evidence-informed material question; the answer updates existing intent, while a wording review is not presented as a passed behavioral test.                        |
| AC-11     | R-12          | A consistency review exposes a conflicting contract, an uncovered obligation, and an unexplained addition without changing code, rewriting acceptance, or requiring a new report file.               |
| AC-12     | R-6, R-13     | Completion assessment finds required behavior absent from the diff, reports unavailable evidence, and bounds fixes without silently weakening intent or deleting unexplained additions.              |
| AC-13     | R-8, R-14     | A larger change identifies useful verifiable slices and relevant failure boundaries; involved roles and the testing instruction reinforce this without imposing every role, checklist, or test type. |

## Execution Tasks

This is a proposed implementation breakdown, not a second role pipeline.
Tasks may share a branch; ordering below does not imply unstated dependencies.

| Task | Scope                                                                                                                                                                                    | Actual prerequisites               | Criteria                              |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------- |
| T-1  | Review this proposal, resolve material decisions, and record approval before moving to `BUILD`.                                                                                          | None                               | AC-1 through AC-13                    |
| T-2  | Extend changedoc/requirements guidance and the document template, including clarification, requirement quality, slices, and older-template adoption.                                     | T-1                                | AC-1, AC-7, AC-8, AC-10, AC-13        |
| T-3  | Align the role agents, analyse/inspect/verify skills, and testing instruction with the Artifact Changes table. Preserve configured gates, role boundaries, and the shared report schema. | T-1                                | AC-2 through AC-6, AC-8 through AC-13 |
| T-4  | Add focused template/instruction regressions and evaluate all scenarios below against rendered guidance, including report placement and no-progress handling.                            | T-2, T-3                           | AC-1 through AC-13                    |
| T-5  | Align baseline docs, record the approved ADR, regenerate managed output, and record final verification.                                                                                  | T-2, T-3; T-4 for final completion | AC-7, AC-8, AC-9                      |

T-2 and T-3 can progress independently against this approved contract.
Documentation and test drafting can accompany implementation; their final
verification needs the resulting templates, not a separate upfront sign-off.

## Test Scenarios

| Scenario                    | Exercise                                                                                                              | Expected result                                                                                                                              | Criteria     |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| TS-1: Ordinary feature      | Plan a bounded behavior change requiring a durable handoff.                                                           | One changedoc holds requirements, criteria, useful tasks, and evidence references; no parallel spec tree.                                    | AC-1, AC-7   |
| TS-2: Small fix             | Supply a clear low-risk bug report with expected behavior and a regression test.                                      | Focused work uses existing context and reports verification without mandatory new documents or role stages.                                  | AC-2         |
| TS-3: Ambiguous migration   | Omit a material data-retention or rollback decision.                                                                  | Affected work pauses for a focused decision; unrelated safe investigation can continue.                                                      | AC-3         |
| TS-4: Real dependencies     | Provide two independent tasks and one task that needs both.                                                           | Only the third task depends on the first two; explicit configured workflow gates remain in force.                                            | AC-4         |
| TS-5: Missing evidence      | Complete task checkboxes but omit a required contract test or provide a failing result.                               | Verification exposes the gap or failure and does not claim full completion.                                                                  | AC-5         |
| TS-6: Changed intent        | Revise one accepted behavior after tests passed.                                                                      | Existing criterion references remain stable; relevant evidence needs reassessment, while unrelated work remains valid.                       | AC-6         |
| TS-7: Older installation    | Use a customized local changedoc template and an old completed changedoc.                                             | Guidance supports new content without replacing the template or backfilling history.                                                         | AC-8         |
| TS-8: Lifecycle edge        | Attempt implementation from an archived changedoc or with an outstanding required approval.                           | No implementation authorization is inferred from status ordering or lightweight routing.                                                     | AC-3, AC-9   |
| TS-9: Baseline boundary     | Compare an internal refactor with an API behavior change.                                                             | Only affected authoritative baselines change; implementation detail is not copied into a global requirements document.                       | AC-7         |
| TS-10: Operational scope    | Compare a documentation edit with a latency-sensitive service change.                                                 | Documentation uses document checks; the service change supplies relevant measurable evidence.                                                | AC-2, AC-5   |
| TS-11: Clarification        | Supply a vague performance expectation with some answers already recorded in the repository.                          | Ask only the remaining material question, persist the answer, and distinguish requirement quality from runtime proof.                        | AC-10        |
| TS-12: Inconsistent scope   | Provide a conflicting API contract, an uncovered requirement, and an unrelated proposed task.                         | Analyse reports the conflicts and coverage gaps without edits or an additional mandatory report.                                             | AC-11        |
| TS-13: False completion     | Mark tasks complete while required behavior is absent from the diff; make one necessary test environment unavailable. | Inspect identifies the missing behavior and evidence limitation. Verify does not claim success or enter a repeated no-progress loop.         | AC-5, AC-12  |
| TS-14: Unexplained addition | Include an unrelated feature beside a necessary internal helper in the working tree.                                  | Request a scope decision for the unrelated feature; do not delete it automatically or require a separate product requirement for the helper. | AC-11, AC-12 |
| TS-15: Useful slices        | Plan a feature with independently useful outcomes and a relevant retry or concurrency failure case.                   | Identify verifiable slices and appropriate contract/failure checks; a small counterpart task gains no mandatory checklist or role rounds.    | AC-13        |

### Validation Approach

- Add focused regressions to existing
  [skill template tests](../../tests/vstack/skills/test_templates.py),
  [agent template tests](../../tests/vstack/agents/test_template_structure.py),
  and [installation tests](../../tests/vstack/cli/test_install.py) where behavior
  is affected. Update existing golden output if generated content changes.
- Prefer checks for lifecycle/routing contradictions and preserved contracts over
  brittle assertions of exact advisory wording.
- Review the scenarios against rendered guidance. Record observed outcomes;
  static template assertions alone do not prove an agent will follow instructions.
- Run targeted tests, artifact validation, and changed-Markdown checks first.
  Run the repository quality gate before implementation is declared complete.
- Keep any future automated consumer-spec checks as a separate proposal informed
  by adoption evidence.

## Verification

Implementation verification has not run. This document is a `CONCEPT`.
All AC-1 through AC-13 outcomes remain **not run** for the proposed product change.

Proposal review can confirm coverage and internal consistency, but cannot mark
these implementation criteria as passed. During implementation, record the
criterion, check, reviewed scope/revision, result, and remaining limitation here.
Use concise references to existing reports rather than duplicating their contents.

## Notes

### Decisions Proposed for Review

- Use changedoc as the change-local specification, not a new spec artifact type.
- Make structure proportional; keep safety obligations independent of size.
- Preserve existing lifecycle and workflow policy; add no enforcement tooling now.
- Evaluate usefulness in real tasks before proposing machine-readable contracts.

### Open Questions

No additional product choice is required to review this concrete proposal.
Its recommendations remain subject to approval, especially the focused-task
exception to today's broad changedoc requirement.

How reliably agents follow the lighter routing and evidence guidance is
unproven. Scenario evaluation must expose limitations rather than claim a
deterministic guarantee. Recurring failures would justify a narrower follow-up.

### Rollback

Revert the affected source guidance and regenerate managed artifacts if adoption
adds ceremony or causes unsafe omissions. Retain user documents and their added
sections; no data migration or destructive cleanup is needed.

### Scope Discipline

Use original vstack guidance aligned with its existing artifact boundaries.
Do not introduce external terminology, commands, copied templates, or a parallel
workflow to deliver the behavior described here.
