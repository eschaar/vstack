Evaluate release gate readiness using required reports, artifacts, and sign-off evidence.

Use repository evidence only.

Output exactly in this format:

## Release Gate Status

- overall status: READY | NOT-READY
- scope reviewed
- evidence sources checked

## Missing or Stale Evidence

For each item:

- artifact
- issue: MISSING | STALE | INCOMPLETE
- impact
- owner role

## Sign-off Gaps

For each required role:

- role
- verdict: OK | NOK | NOT-RECORDED
- blocking reason

## Release Actions

Ordered actions to reach READY.

- action
- owner role
- verification step
