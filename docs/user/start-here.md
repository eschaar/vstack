# Start Here

Choose the path that matches your goal, then follow the checklist in order.

## Quick commands

```bash
# Check current manifest status
vstack manifest status --target .

# Update hooks only
vstack init --only hook

# Force one artifact (example: agent/engineer)
vstack install --force-name agent/engineer

# Force update one type (hooks)
vstack init --only hook --force

# Verify manifest health
vstack manifest verify --target .
```

## 1. New User Path

1. Learn the end-to-end flow in [First time using vstack](tutorials/first-time-using-vstack.md).
1. Run your first orchestrated workflow in [First planner run](tutorials/first-planner-run.md).
1. Learn shared team baselines in [Community patterns](explanation/community-patterns.md).
1. Run your baseline setup with [Fresh install](how-to/fresh-install.md).
1. Learn daily commands in [CLI commands](reference/cli-commands.md).
1. Configure defaults in [Configuration](reference/configuration.md).
1. If anything fails, use [Troubleshooting](how-to/troubleshooting.md).

## 2. Upgrade Path

1. Start with [Upgrade with checks](tutorials/upgrade-with-checks.md) for a walkthrough.
1. Use the operational guide in [Upgrade](how-to/upgrade.md).
1. Use [Partial upgrade](how-to/partial-upgrade.md) when you only need selected updates.
1. Rebuild generated artifacts if needed with [Reinitialize](how-to/reinitialize.md).
1. Confirm output health with [Artifact checks](reference/artifact-checks.md).
1. Validate command behavior with [CLI commands](reference/cli-commands.md).

## 3. Operations Path

1. Set operating behavior in [Configure workflow modes](how-to/configure-workflow-modes.md).
1. Choose execution style with [Choose agent, skill, or prompt](how-to/choose-agent-skill-or-prompt.md).
1. Tune project settings in [Configuration](reference/configuration.md).
1. Manage automation points in [Hooks](reference/hooks.md).
1. Review role-owned outputs and handoff artifacts in [Work items](reference/work-items.md).
1. Use [Troubleshooting](how-to/troubleshooting.md) for incidents and recovery.
1. If you need profile-scoped setup, use [Global install](how-to/global-install.md) and [Uninstall](how-to/uninstall.md).
