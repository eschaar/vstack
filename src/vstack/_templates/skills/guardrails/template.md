{{SKILL_CONTEXT}}

# guardrails — Safety Mode

Activate careful mode for this session. Two behaviors are now enabled.

## Out of scope

- Code review or security audit (use `code-review` or `security`)

______________________________________________________________________

## Behavior 1: Careful Mode (always active after invoking this skill)

**Before executing any of the following commands, get explicit confirmation:**

| Command                        | Risk                         | What to confirm             |
| ------------------------------ | ---------------------------- | --------------------------- |
| `rm -rf`                       | Permanent file deletion      | Files to delete             |
| `DROP TABLE` / `DROP DATABASE` | Permanent data loss          | Table/database name         |
| `git push --force`             | Overwrites remote history    | Branch and remote           |
| `git reset --hard`             | Discards local changes       | What will be lost           |
| `git clean -fd`                | Removes untracked files      | Files to remove             |
| `kubectl delete`               | Removes Kubernetes resources | Resource name and namespace |
| `fly destroy`                  | Destroys Fly.io app          | App name                    |
| `docker rm -f`                 | Forcefully removes container | Container                   |
| Any `--force` flag             | Bypasses safety check        | Why force is needed         |
| Production config changes      | Affects live traffic         | Explicit approval           |
| Database migrations            | May modify data schema       | Review migration SQL        |

**Procedure for each dangerous command:**

1. Stop.
1. Explain exactly what the command does and what will be permanently lost.
1. Ask for explicit confirmation.
1. Only proceed if the user says yes.
1. Never use workarounds to avoid this confirmation.

______________________________________________________________________

## How to Deactivate

Explicitly ask to "disable guardrails".

______________________________________________________________________
