# First planner run

This tutorial walks through your first end-to-end run with the `planner` agent in GitHub Copilot Agent mode.

## Goal

By the end, you will run one planner prompt from a configured repository and understand what outputs to expect.

## Prerequisites

1. Install the vstack CLI with `pipx`:

```bash
pipx install vstack
vstack --version
```

1. Open your repository root in VS Code.
1. Install project artifacts from repository root:

```bash
vstack install
vstack validate
```

1. Confirm `.github/agents/planner.agent.md` exists.

## Setup in VS Code

1. Open Copilot Chat.
1. Switch to Agent mode.
1. In the agent picker, select `planner`.

## Run your first prompt

Use a small, concrete prompt so the first run is easy to inspect:

```text
Run the workflow for this repository change.
```

## Expected output

On a healthy setup, planner output usually includes:

- a staged workflow response across role boundaries,
- explicit handoff points (for example from planning to implementation),
- references to generated role artifacts under `.github/`.

If output does not look role-structured, verify that Agent mode is enabled and `planner` is selected.

## Next steps

1. Practice role targeting with [Choose agent, skill, or prompt](../how-to/choose-agent-skill-or-prompt.md).
1. Learn upgrade checks with [Upgrade with checks](upgrade-with-checks.md).
1. Keep command behavior handy with [CLI commands](../reference/cli-commands.md).
