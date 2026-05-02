Construct a blameless incident timeline from the provided evidence.

Anchor claims to available logs, alerts, traces, and change events.
If evidence is missing, explicitly mark uncertainty.

Output exactly in this format:

## Incident Snapshot

- incident title
- impact window
- affected systems/users
- current status

## Timeline (UTC)

List timestamped events in order.

For each event:

- time
- event description
- evidence source
- confidence: high | medium | low

## Root Cause Analysis

- primary cause
- contributing factors
- what made detection/recovery slower

## What Worked / What Failed

Two short lists.

## Corrective Actions

For each action:

- action description
- owner role
- priority: P0 | P1 | P2
- due expectation (short horizon)

## Prevention Check

List the minimum controls needed to reduce repeat probability.
