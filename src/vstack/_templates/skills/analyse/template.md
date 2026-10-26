{{SKILL_CONTEXT}}

{{BASE_BRANCH}}

# analyse - Technical Analysis

Investigate impact, tradeoffs, feasibility, causes, risks, or change consistency.
Do not implement changes, rewrite acceptance, or run a verification fix loop.
Use `debug` for fixes, `performance` for profiling, `architecture`/`adr` for
decisions, and `verify` for implementation checks.

## Scope and evidence

Establish the question, scope, and known decisions from context. Ask only for
material missing information. Read relevant code, callers, contracts, baselines,
and data; do not launch a whole-repository audit by default.

Support findings with file locations, measured data, or explicit assumptions.
Inspect history and dependents when relevant; distinguish facts from hypotheses.

## Select relevant dimensions

| Analysis    | Questions                                                            |
| ----------- | -------------------------------------------------------------------- |
| Impact      | Dependents, blast radius, compatibility, migration, rollback?        |
| Tradeoff    | Complexity, performance, maintenance, cost, risk, effort per option? |
| Feasibility | Stack capability, limits, dependencies, blockers?                    |
| Cause       | Symptom, timeline, primary cause versus contributing factors?        |
| Risk        | Likelihood, impact, mitigation?                                      |
| Consistency | Do intent, acceptance, contracts, and useful tasks agree?            |

## Change-consistency review

Use before implementation when explicitly requested or justified by risk.
Read only relevant requirements, criteria, constraints, contracts, and tasks.
Identify:

- contradictions, including contracts conflicting with agreed behavior;
- uncovered obligations or vague, untestable criteria;
- proposed additions with no requirement or engineering rationale;
- artificial prerequisites inferred from task order or role names.

For each finding, give source, consequence, and proposed next action. Necessary
implementation details need not each be a product requirement. An unexplained
addition is a scope question, not permission to delete code. Do not silently
change intent, tasks, or implementation.

## Output

Return a compact response: question/scope, findings with evidence and impact,
recommendation, open questions, and confidence (`certain`, `probable`, `uncertain`).
For consistency reviews, use the response or an existing document when authorized;
no mandatory standalone report. A requested broader report may use the same
structure. Requirement quality and consistency findings are not behavioral proof.
