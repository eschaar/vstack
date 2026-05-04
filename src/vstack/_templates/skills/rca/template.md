{{SKILL_CONTEXT}}

# rca — Root Cause Analysis

Guide a systematic technical investigation and produce an RCA document linked
to the triggering issue. The goal is a specific, evidence-backed root cause —
not the proximate trigger.

## Out of scope

- Stakeholder communication and blameless post-mortems (use `postmortem`)
- Live incident triage (use `incident`)
- General code debugging (use `debug`)
- Security vulnerability analysis (use `security`)

**Golden rule: The root cause is the deepest systemic condition that, if fixed,
prevents this class of incident from recurring. It is never "human error".**

## Step 0: Gather Context

Before analysis, establish the facts:

> **Collect:**
>
> - Issue or incident ID and title
> - Severity (P1–P4 or SEV1–SEV3)
> - When did it start and end? (UTC timestamps)
> - What was the observable symptom?
> - What was done to resolve it?
> - Is there a linked issue file? (e.g. `issues/001-login-timeout.md`)

```bash
# Review recent changes in the window
git log --oneline --since="YYYY-MM-DD" --until="YYYY-MM-DD" 2>/dev/null | head -30

# Find relevant config or infra changes
git log --oneline --since="YYYY-MM-DD" -- '*.yaml' '*.yml' '*.toml' 2>/dev/null | head -20
```

Confirm output location before writing:

> **Output path:** Where should the RCA be written?
>
> Default: alongside the issue file, or `docs/` if no issue path is known.
> Suggested name: `{id}-{slug}-rca.md` (e.g. `001-login-timeout-rca.md`)
>
> **Options:** A) Use default | B) Specify a different path

## Step 1: What Happened

Describe the incident factually and concisely:

```text
What happened:
  [Factual description — what system, what failed, what was the user impact]

Severity:    [P1 | P2 | P3 | P4]
Start:       [YYYY-MM-DD HH:MM UTC]
End:         [YYYY-MM-DD HH:MM UTC]
Duration:    [N hours N minutes]
```

## Step 2: Root Cause — 5 Whys

Use the 5-Whys technique to reach the systemic condition:

```text
Why did [impact] happen?
  Because [immediate cause].

Why did [immediate cause] happen?
  Because [contributing factor].

Why did [contributing factor] exist?
  Because [deeper cause].

Why did [deeper cause] exist?
  Because [systemic gap].

Root cause:
  [One specific, systemic statement]

Evidence:
  [What confirms this conclusion]
```

## Step 3: Contributing Factors

List all conditions that made this possible — not just the trigger:

| Category      | Factor |
| ------------- | ------ |
| Code / logic  |        |
| Configuration |        |
| Deployment    |        |
| Monitoring    |        |
| Process       |        |
| External      |        |

## Step 4: Detection

How was this discovered, and could it have been caught faster?

```text
Detected by:       [alert | user report | manual check]
Time to detect:    [N minutes after impact start]
Detection gap:     [why not faster — threshold too high | missing alert | other]
```

## Step 5: Resolution

What was done to restore service?

```text
Resolution:        [what was done]
Time to resolve:   [N minutes after detection]
```

## Step 6: Action Items

Action items must be specific, owned, and time-bound:

| Item | Category   | Owner | Due |
| ---- | ---------- | ----- | --- |
|      | Prevention |       |     |
|      | Detection  |       |     |
|      | Response   |       |     |

## Step 7: Write the RCA Document

Write to the confirmed output path:

```markdown
# {id}: {title} — Root Cause Analysis

<!-- Suggested name: {id}-{slug}-rca.md -->

> **date:** YYYY-MM-DD
> **severity:** P{1–4}
> **status:** draft | in-progress | resolved
> **issue:** [{id}]({id}-{slug}.md)

## what happened

## root cause

## contributing factors

## detection

## resolution

## action items

| Item | Owner | Due |
| --- | --- | --- |

## lessons learned
```

## Output

```text
RCA Complete
════════════

Incident:    [ID / title]
Severity:    [P1–P4]
Root cause:  [one-line summary]
Action items:[N total]

Written to:  [path/to/{id}-{slug}-rca.md]
Status:      Draft — ready for review
```
