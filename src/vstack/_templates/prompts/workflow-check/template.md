Review workflow stage flow, gate usage, and handoff integrity across role artifacts.

Focus on evidence in workflow config, role templates, and docs.

Output exactly in this format:

## Flow Summary

- workflow scope
- current stage order
- gate model used

## Gate and Handoff Findings

For each finding:

- location: file path and section
- issue: one sentence
- impact: what can fail in execution
- fix: concrete correction

## Blocking Risks

List only issues that block reliable workflow execution.

- blocker
- owner role
- required action

## Recommended Next Steps

Provide an ordered short list of actions.

- action
- owner role
- expected result
