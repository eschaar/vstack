{{SKILL_CONTEXT}}

# requirements - Requirements Gathering

Define what must be built and observable acceptance before engineering. Product
owns scope; architecture, design, roadmap planning, and implementation belong to
their respective roles.

## Choose the intent source

- System-level intent: `docs/product/requirements.md` on the branch.
- Change-local intent: the existing changedoc, not a separate specification.
- Small, clear, low-risk task: sufficient existing issue or conversation context.

Update shared baselines only when shared behavior or contracts change. Preserve
project gates and approvals regardless of task size; do not mandate every role.

## Clarify from evidence

1. Read relevant vision, requirements, roadmap, code, and recorded decisions first.
1. Identify the highest-impact uncertainty. Ask one focused question only when
   it materially affects correctness, scope, risk, or approval; no interview quota.
1. Record accepted answers in the existing intent source, or confirm them in chat.
   Do not repeat answered questions. State remaining assumptions and their risks.

## Define requirements

Capture only relevant dimensions:

| Dimension           | Record                                                                              |
| ------------------- | ----------------------------------------------------------------------------------- |
| Problem             | Who is affected, unmet need, and consequence                                        |
| Functional behavior | Must/should/won't-have outcomes, conditions, boundaries, and failure behavior       |
| Quality attributes  | Measurable performance/load, availability, security, scaling, or compliance targets |
| Constraints         | Required technology, integration, budget, deadline, and team limits                 |
| Acceptance          | Observable completion and how to check it                                           |
| Open questions      | Blocking decision, owner, and when needed                                           |

Use "The system must [behavior] under [condition]" where helpful. Keep outcomes
separate from technical choices unless a constraint requires them. Review
terminology, completeness, testability, and assumptions only for relevant scope.
A wording review is not proof that implementation works.

Prefer independently verifiable delivery slices when useful; do not force them
on small fixes or tightly coupled migrations. Reference relevant contracts and
data-lifecycle/operational constraints rather than copying them.

## Output and readiness

For system baselines, organize findings as Problem, Users, Functional Requirements,
Non-Functional Requirements, Constraints/Assumptions, Acceptance, and Open Questions.
For change-local work, maintain the corresponding existing sections.

Use stable local references when useful; no global IDs or duplicate prose.
Summarize scope, criteria, and blockers for the relevant owner. Implementation
requires understood scope, observable acceptance, resolved blocking questions,
and approval under project policy. After material revisions, reassess affected
tasks/evidence and renew approval only when scope, risk, or policy requires it.
