{{SKILL_CONTEXT}}

# lazy - Minimal Safe Implementation

Deliver the required outcome with the least net-new code that is still correct,
secure, and maintainable.

This skill is engineer-first: be lazy about writing code, never lazy about
understanding behavior and risk.

## Use this when

- A request looks likely to be over-engineered.
- You can probably solve the task by reuse, deletion, or composition.
- You want the smallest safe implementation that still passes quality gates.

## Non-negotiables

Never trade these away for fewer lines:

- Correctness at trust boundaries
- Input validation and authorization checks
- Data-loss prevention and migration safety
- Error handling and observability
- Accessibility and contract compatibility

If the smallest approach violates any item above, move one rung up and choose the
next safest option.

## Ladder: stop at the first rung that holds

Run this ladder after understanding the touched flow.

1. **Avoid**: Does this change need to exist at all?
1. **Delete**: Can existing code be removed to meet the goal?
1. **Reuse local**: Is there already an implementation in this repo?
1. **Use contracts**: Can existing API/schema/workflow contracts solve it without new logic?
1. **Use stdlib/native**: Can standard library or platform primitives solve it?
1. **Use existing dependency**: Can an already installed dependency solve it safely?
1. **Thin glue**: Can a tiny adapter wire existing parts together?
1. **Write new code**: Only the minimum required behavior.

## Execution protocol

## Step 0 - Comprehension first

Before coding, map what will actually be touched:

- Entry points (CLI/API/handler)
- Call path and side effects
- Trust boundaries
- Existing tests covering the path

If you cannot describe the flow, do not start writing code.

## Step 1 - Evaluate the ladder with evidence

For each rung, capture one short proof:

```text
Rung 1 (Avoid): [pass/fail] - evidence
Rung 2 (Delete): [pass/fail] - evidence
...
Chosen rung: [N]
```

Prefer direct repository evidence over assumptions.

## Step 2 - Implement the smallest safe change

Implementation rules:

- Keep the public contract unchanged unless explicitly requested.
- Prefer local edits over new modules.
- Prefer composition over abstraction.
- Add comments only where intent is non-obvious.
- Do not add dependencies unless existing options are insufficient.

## Step 3 - Verify proportionally, never skip regression safety

Always run the targeted checks for changed behavior. For risky paths, run broader checks.

Minimum verification:

- Updated or new tests for the changed behavior
- Relevant lint/type checks for touched files
- Reproducer or scenario proving the old issue is fixed (if bug-related)

## Step 4 - Report the value of laziness

Return what was avoided, not only what was added:

```text
## Lazy Execution Report

Task:
[one-line objective]

Chosen rung:
[rung number + name]

What we avoided:
- [dependency/module/abstraction not introduced]
- [code path removed or reused]

Changes made:
- [file]: [minimal change summary]

Safety checks kept:
- [validation/auth/error handling/accessibility checks preserved or added]

Verification:
- [commands]
- [result summary]

Residual risk:
- [none or explicit risk + follow-up]
```

## Escalate instead of forcing a tiny solution

Stop and escalate when:

- The smallest option conflicts with architecture or approved design.
- The change requires a new public contract.
- Security or compliance requirements require a broader implementation.
- The task is under-specified and any minimal patch would be guesswork.
