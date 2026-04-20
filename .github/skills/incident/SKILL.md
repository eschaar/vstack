---
name: incident
description: 'Incident analysis and post-mortem writing. Guides a structured investigation from timeline reconstruction through root cause identification to a blameless post-mortem document with action items. Use when asked to "write a post-mortem", "incident review", "root cause analysis for this outage", "what went wrong?", or "blameless post-mortem". Produces a docs/postmortems/{date}-{slug}.md.'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
argument-hint: '[incident or outage to analyse and document]'
user-invocable: true
disable-model-invocation: false
---
## Skill Context

This skill is part of **vstack** — a VS Code-native AI engineering workflow system.

### AskUserQuestion Format

When you need clarification, use this exact format — never invent or guess:

> **Question:** [The specific question]
> **Options:** A) … | B) … | C) …
> **Default if no response:** [What you'll do]

Never ask more than one question at a time without waiting for the answer.

# incident — Incident Analysis & Post-Mortem

Guide a structured incident investigation and produce a blameless post-mortem
document. The goal is learning and prevention — not blame.

## Out of scope

- Live incident response / on-call triage (this skill is for retrospective analysis)
- Root-cause debugging of code bugs (use `debug`)
- Security audit of vulnerabilities (use `security`)
- Performance benchmarking (use `performance`)

**Golden rule: Incidents are system failures, not human failures. Every finding
must be framed as a system improvement opportunity, never as individual blame.**

______________________________________________________________________

## Step 0: Gather Incident Context

Before analysis, collect all available evidence:

> **Questions to answer:**
>
> - When did the incident start and end? (UTC timestamps)
> - What was the user-visible impact? (errors, latency, data loss, downtime)
> - What services were affected?
> - Who detected it and how? (alert, user report, monitoring)
> - What was done to resolve it?
> - Is there a severity classification? (P0/P1/P2 or SEV1/SEV2/SEV3)

```bash
# Gather git history around the incident window
git log --oneline --since="YYYY-MM-DD" --until="YYYY-MM-DD" 2>/dev/null | head -30

# Check recent deploys
git log --oneline --merges --since="YYYY-MM-DD" 2>/dev/null | head -20

# Find relevant config or infra changes
git log --oneline --since="YYYY-MM-DD" -- '*.yaml' '*.yml' '*.toml' '*.env*' 2>/dev/null | head -20
```

Document:

```text
Incident ID:   [INC-NNNN or date-slug]
Severity:      [P0 | P1 | P2 | SEV1 | SEV2 | SEV3]
Start:         [YYYY-MM-DD HH:MM UTC]
End:           [YYYY-MM-DD HH:MM UTC]
Duration:      [N hours N minutes]
Detected by:   [alert | user report | manual check]
Services:      [list of affected services]
Impact:        [user-facing description]
```

______________________________________________________________________

## Step 1: Reconstruct the Timeline

Build a precise, chronological timeline of events. Include:

- System events (deploys, config changes, traffic spikes)
- Detection events (alerts fired, pages sent)
- Response actions (who did what, when)
- Resolution events (rollback, fix deployed, service restored)

```text
Timeline (all times UTC):

HH:MM — [event description] — [who / what system]
HH:MM — [event description] — [who / what system]
...

Key markers:
  Impact start:      HH:MM
  Detection:         HH:MM  (+N min after impact start)
  Response start:    HH:MM  (+N min after detection)
  Mitigation:        HH:MM  (+N min after response)
  Full resolution:   HH:MM
  Total duration:    N hours N minutes
```

______________________________________________________________________

## Step 2: Identify Contributing Factors

List ALL factors that contributed to the incident — not just the "trigger".
Incidents are never caused by a single thing. Use the 5-Whys technique:

**5-Whys template:**

```text
Why did [impact] happen?
  Because [immediate cause].

Why did [immediate cause] happen?
  Because [contributing factor 1].

Why did [contributing factor 1] exist?
  Because [deeper cause].

Why did [deeper cause] exist?
  Because [systemic gap].

Why did [systemic gap] exist?
  Because [root systemic condition].
```

Categorize contributing factors:

| Category      | Factor                                                   |
| ------------- | -------------------------------------------------------- |
| Code / logic  | [e.g. missing error handling, race condition]            |
| Configuration | [e.g. incorrect timeout, missing feature flag]           |
| Deployment    | [e.g. no canary, missing rollback plan]                  |
| Monitoring    | [e.g. alert threshold too high, missing metric]          |
| Process       | [e.g. no review for config changes, unclear runbook]     |
| External      | [e.g. upstream dependency failure, cloud provider issue] |
| Knowledge     | [e.g. undocumented behaviour, tribal knowledge gap]      |

______________________________________________________________________

## Step 3: Determine Root Cause

The root cause is the deepest systemic condition that, if addressed, would
prevent this class of incident from recurring.

**Root cause is NOT:**

- "Human error" (humans make mistakes — the system must be resilient to them)
- "We forgot to test X" (why was it possible to ship without testing X?)
- The deployment that triggered it (that is the trigger, not the cause)

```text
Root cause:
  [One clear, specific statement of the systemic condition]

Evidence:
  [What evidence supports this conclusion]

Class of incident:
  [Deploy regression | Configuration drift | Dependency failure |
   Capacity / traffic | Data corruption | Security breach | Other]
```

______________________________________________________________________

## Step 4: Assess Impact

Quantify the impact precisely:

```text
User impact:
  Affected users:     [N users | N% of traffic | all users]
  Error rate:         [N% of requests returned errors]
  Latency increase:   [p99 increased from Nms to Nms]
  Data loss:          [none | N records | describe scope]
  Feature unavailable:[list features]

Business impact:
  Revenue:            [estimated impact if known]
  SLA breach:         [yes — N minutes over limit | no]
  Customer comms:     [status page update | direct notification | none]

Detection gap:
  Time to detect:     [N minutes]
  How detected:       [alert | user complaint | manual]
  Why not faster:     [threshold too high | missing alert | other]
```

______________________________________________________________________

## Step 5: Write Action Items

Action items must be:

- **Specific** — not "improve monitoring" but "add alert on p99 > 500ms for /checkout"
- **Owned** — assigned to a person or team
- **Time-bound** — target date or sprint
- **Categorized** — prevention, detection, or response improvement

```text
Action items:

Prevention (stop this from happening again):
  [ ] [specific action] — owner: [name/team] — due: [date/sprint]

Detection (catch it faster next time):
  [ ] [specific action] — owner: [name/team] — due: [date/sprint]

Response (resolve it faster next time):
  [ ] [specific action] — owner: [name/team] — due: [date/sprint]
  [ ] Write or update runbook for this failure class — owner: [name/team] — due: [date/sprint]

Process (improve how we handle incidents):
  [ ] [specific action] — owner: [name/team] — due: [date/sprint]
```

______________________________________________________________________

## Step 6: Produce the Post-Mortem Document

Write the post-mortem to `docs/postmortems/YYYY-MM-DD-<slug>.md`:

```markdown
# Post-Mortem: [Short Title]

**Date:** YYYY-MM-DD
**Severity:** [P0 | P1 | P2]
**Duration:** N hours N minutes
**Status:** [Draft | In Review | Closed]
**Author(s):** [names]

---

## Summary

[2–3 sentences: what happened, what was the impact, how was it resolved.
Written for a non-technical audience.]

## Impact

| Dimension | Details |
|---|---|
| Duration | N hours N minutes (HH:MM–HH:MM UTC) |
| Users affected | [N users / N% of traffic] |
| Error rate | [N%] |
| SLA breach | [yes / no] |
| Data loss | [none / description] |

## Timeline

| Time (UTC) | Event |
|---|---|
| HH:MM | [event] |
| HH:MM | [event] |
| ... | ... |

## Root Cause

[One paragraph. Specific, systemic, blameless.]

## Contributing Factors

- [factor 1]
- [factor 2]
- [factor 3]

## What Went Well

- [thing 1 — e.g. alert fired within 2 minutes]
- [thing 2 — e.g. rollback completed in 4 minutes]
- [thing 3]

## What Went Poorly

- [thing 1 — e.g. no runbook for this failure mode]
- [thing 2]

## Action Items

| # | Action | Category | Owner | Due |
|---|---|---|---|---|
| 1 | [action] | Prevention | [owner] | [date] |
| 2 | [action] | Detection | [owner] | [date] |
| 3 | [action] | Response | [owner] | [date] |

## Lessons Learned

[2–4 sentences summarizing the key takeaways for the team and organization.
What does this incident teach us about our system, processes, or culture?]
```

______________________________________________________________________

## Output

```text
Incident Analysis Complete
══════════════════════════

Incident:   [ID / title]
Severity:   [P0 | P1 | P2]
Duration:   [N hours N minutes]
Root cause: [one-line summary]

Contributing factors: [N identified]
Action items:         [N total — N prevention, N detection, N response]

Post-mortem written:  docs/postmortems/YYYY-MM-DD-<slug>.md
Status:               [Draft — ready for team review]
```

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"incident","artifact_type":"skill","artifact_version":"1.0.0","generator":"vstack","vstack_version":"0.0.0.post3.dev0+df3fe6e"} -->
