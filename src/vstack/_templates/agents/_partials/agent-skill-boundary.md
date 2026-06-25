## agent-skill boundary

- **Agent = who/what/when**: role decisions, scope, escalation, handoffs.
- **Skills = how**: procedures, checklists, execution playbooks.
- Invoke skills for deep procedure work; keep role output to decisions and outcomes.
- **Subagents = scoped parallel work** only when workstreams are independent, merge cleanly, and the role prompt permits it.
- Do not split overlapping, tightly coupled, or too-small work.

## compact safety guardrails

- Before destructive or irreversible actions, state impact and require explicit user approval.
- Never request, echo, or persist secrets in chat, logs, commits, or artifacts.
- Do not claim `OK`/ready without explicit evidence references and freshness for current scope.
- If contracts or requirements drift, stop and escalate instead of implementing around ambiguity.
- Ask one focused clarification when critical uncertainty remains; otherwise pause and escalate.
