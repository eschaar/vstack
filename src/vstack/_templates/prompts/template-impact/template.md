Assess impact of a template change on generated artifacts, tests, and release risk.

Use source-template and generated-artifact evidence.

Output exactly in this format:

## Change Surface

- template scope
- affected artifact types
- likely generated paths

## Impact Findings

For each finding:

- impacted path
- impact type: BEHAVIOR | DOCS | TESTS | TOOLING
- risk
- required validation

## Regression Risk

List highest-risk regressions first.

- scenario
- likelihood: HIGH | MEDIUM | LOW
- mitigation

## Verification Plan

- commands to run
- expected pass criteria
