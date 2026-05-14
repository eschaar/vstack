# Choose agent, skill, or prompt

Use this guide to decide how to run work in Copilot Chat with vstack.

## Quick decision rules

Use an agent when:

- you want role-based ownership and structured handoffs,
- you are running end-to-end work across multiple stages,
- you want behavior aligned with the project role model.

Use a skill when:

- you need one focused capability (for example `verify`, `debug`, or `openapi`),
- you already know the scope and want a direct playbook,
- you do not need full multi-role orchestration.

Use a prompt when:

- you need lightweight, one-off guidance,
- you want to adapt wording for a specific context quickly,
- you are not changing the role model or skill inventory.

## Practical examples

| Situation                                                                  | Best fit          | Why                                                    |
| -------------------------------------------------------------------------- | ----------------- | ------------------------------------------------------ |
| Plan and execute a feature across design, implementation, and verification | Agent (`planner`) | Planner coordinates role flow and handoffs.            |
| Fix failing checks before merge                                            | Skill (`verify`)  | Verify provides targeted fix-loop behavior.            |
| Investigate a production bug cause                                         | Skill (`debug`)   | Debug is optimized for root-cause-first investigation. |
| Ask for a one-off API naming suggestion                                    | Prompt            | Fast and local, no orchestration needed.               |
| Generate release artifacts from completed work                             | Agent (`release`) | Release role owns release gating outputs.              |

## Escalation pattern

Start small, then escalate only when needed:

1. Start with a prompt for low-risk, narrow tasks.
1. Move to a skill for repeatable specialist work.
1. Move to an agent when ownership boundaries and workflow handoffs matter.

## Related docs

- [Start Here](../start-here.md)
- [First planner run](../tutorials/first-planner-run.md)
- [Skills overview](../reference/skills-overview.md)
- [Prompts overview](../reference/prompts-overview.md)
- [Work items](../reference/work-items.md)
