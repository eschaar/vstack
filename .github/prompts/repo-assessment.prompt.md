---
description: 'Assess a repository for production-readiness gaps and prioritized improvements.'
name: repo-assessment
argument-hint: '[repository scope or component path]'
agent: engineer
tools:
  - read
  - search
---
Assess this repository for production-readiness gaps and prioritized improvements.

Base findings on evidence in source files, tests, CI config, docs, and manifests.
Prefer concrete findings over speculation.

Output exactly in this format:

## Critical Risks

List only issues that block safe production operation right now.

For each item:

- location: file or component reference
- risk: one sentence describing the production impact
- remediation: concrete action with owner role

## High-ROI Improvements

List high-value improvements that reduce operational risk or developer friction, ranked by impact versus effort.

For each item:

- area: the domain (security | reliability | observability | dx | performance | maintainability)
- finding: what is missing or suboptimal
- suggested action: one clear improvement step

## Testing and Verification Gaps

List untested behavioral paths or areas where coverage may give false confidence.

For each item:

- uncovered behavior: what scenario is missing
- risk if untested: what could go wrong in production
- suggested test type: unit | integration | contract | e2e

## Suggested Next Sprint Backlog

Provide a short, actionable next-sprint task list ordered from highest to lowest priority.

- task title
- owner role (product | architect | designer | engineer | tester | release)
- one-line rationale

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"repo-assessment","artifact_type":"prompt","artifact_version":"20260513001","generator":"vstack","vstack_version":"3.5.2"} -->
