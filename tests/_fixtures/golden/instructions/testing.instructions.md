---
name: testing
description: 'Test authoring conventions for any language or framework. Use when writing or reviewing tests, test plans, or test coverage decisions.'
applyTo: '**/*'
---
Use these testing conventions.

## Scope and intent

1. Write tests to verify observable behavior, not internal implementation details.
1. A test that passes when behavior is wrong, or fails when behavior is correct, has negative value.
1. Tests should read like documentation.

## Naming and structure

1. Name tests by subject, condition, and expected outcome.
1. Keep each test focused on one behavior.
1. Group related tests together; separate unrelated concerns.

## Coverage and completeness

1. Cover success paths, expected failure paths, and boundary conditions for every behavioral change.
1. Treat missing tests for changed behavior as a defect.
1. Cover behaviors that matter rather than lines that exist.

## Test quality

1. Make tests deterministic.
1. Keep tests independent.
1. Prefer clear, direct assertions.
1. Avoid logic in tests; split tests that need it.

## Test boundaries

1. Use unit tests for isolated logic; use integration tests when behavior crosses boundaries.
1. Mock or stub only what is necessary.
1. Test contracts and interfaces, not just internal units.

## Maintenance

1. Update tests in the same change as the behavior they cover.
1. Remove tests that no longer reflect real behavior.
1. Treat flaky tests as bugs.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"testing","artifact_type":"instruction","artifact_version":"20260502004","generator":"vstack","vstack_version":"<vstack-version>"} -->
