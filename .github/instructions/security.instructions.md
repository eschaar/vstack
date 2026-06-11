---
name: security
description: 'Security policy for all code, configuration, and infrastructure. Use when writing or reviewing any code, configuration, or workflow file.'
applyTo: '**/*'
---
Use these security policies.

## Secrets and credentials

1. Never hardcode secrets, tokens, passwords, or private keys in source code, config files, tests, or commit messages.
1. Read secrets from environment variables or a secret store at runtime; document required variables.
1. Treat accidental exposure as a revocation event; rotate immediately.

## Input and trust boundaries

1. Validate and sanitize all input that crosses a trust boundary: HTTP requests, CLI arguments, environment variables, files, and inter-service messages.
1. Never trust client-supplied values for authorization decisions.
1. Reject or escape input before it reaches queries, shell commands, template engines, or logs.

## Authentication and authorization

1. Default to deny; require explicit grants for protected resources or operations.
1. Verify identity and permission separately.
1. Use established, maintained libraries; do not implement custom cryptography or auth schemes.

## Dependencies and supply chain

1. Pin dependency versions in manifests; do not use unbounded version ranges in production code.
1. Minimise the dependency surface.
1. Treat updates that add new transitive dependencies as requiring explicit review.

## Error handling and observability

1. Never expose internal stack traces, system paths, or configuration details to external callers.
1. Do not log sensitive data: passwords, tokens, PII, or session identifiers.
1. Fail closed on security errors.

## Destructive and privileged operations

1. Require explicit confirmation before irreversible or destructive operations.
1. Apply least privilege.
1. Keep privileged logic minimal, auditable, and separate from business logic.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"security","artifact_type":"instruction","artifact_version":"20260502003","generator":"vstack","vstack_version":"3.5.1"} -->
