Assess whether this change set is ready to release.

Review product, architecture, design, test, security, and performance evidence.
Prefer evidence-based findings tied to concrete artifacts.

Output exactly in this format:

## Release Gate Verdict

- Verdict: READY | READY-WITH-CONDITIONS | NOT-READY
- Confidence: high | medium | low
- Scope assessed: one sentence

## Blocking Issues

List only release-blocking items.

For each item:

- artifact or file reference
- why this blocks release in one sentence
- concrete unblock action
- owner role (product | architect | designer | engineer | tester | release)

## Conditions Before Release

List non-blocking but mandatory follow-ups to ship safely.

## Evidence Reviewed

List the exact artifacts checked (reports, docs, CI evidence, manifests).
For each expected artifact that is missing, flag it explicitly as: MISSING — [artifact name].

## Recommended Next Action

One clear next step for the team.
