# ADR-003: Backend-First Verification (`verify` skill)

> Maintained by: **agents** role

**date:** 2026-03-27\
**status:** accepted

## context

Browser-driven testing (click everything in Chromium) is inappropriate for backend
services and libraries, which need: unit tests, integration tests, contract tests
(OpenAPI/Protobuf/Pact), API smoke tests, security scans, observability checks,
and build/packaging verification.

## decision

The `/verify` skill runs:

1. Lint & type-check
1. Unit tests (auto-detected framework)
1. Integration tests
1. Contract tests (OpenAPI validation, Protobuf compilation, Pact)
1. API smoke tests (if server can be started)
1. Security scan (npm audit, pip-audit, govulncheck)
1. Observability review
1. Build/packaging verification

Browser/E2E steps are explicitly omitted. If browser testing is needed, it can be
added as an optional adapter in a future iteration.

## alternatives considered

- Add browser testing as a conditional step — rejected as it re-introduces a browser binary dependency.
- Keep browser-driven QA — rejected as it's wrong for backend-only projects.

## rationale

Contract tests and observability checks provide much higher signal than UI clicks
for services that have no UI.

## impact on future orchestrated pipeline

The `tester` role in the future orchestrated pipeline uses this backend-first implementation.
No browser dependency means it runs without any binary setup.
