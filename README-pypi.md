<p align="center">
	<img src="https://raw.githubusercontent.com/eschaar/vstack/main/assets/branding/vstack.png" alt="vstack" width="260">
</p>

[![PyPI version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpypi.org%2Fpypi%2Fvstack%2Fjson&query=%24.info.version&label=PyPI&color=0B8A6F&cacheSeconds=300)](https://pypi.org/project/vstack/)
[![Python version](https://img.shields.io/badge/python-3.11--3.14-0B8A6F)](https://github.com/eschaar/vstack/blob/main/pyproject.toml)
[![Verify status](https://img.shields.io/github/actions/workflow/status/eschaar/vstack/verify.yml?label=verify&color=1D6FA5)](https://github.com/eschaar/vstack/actions/workflows/verify.yml)
[![Security checks](https://img.shields.io/github/actions/workflow/status/eschaar/vstack/security.yml?label=security&color=B15E00)](https://github.com/eschaar/vstack/actions/workflows/security.yml)
[![Runtime: PyYAML](https://img.shields.io/badge/runtime-PyYAML-5B6C8F)](https://github.com/eschaar/vstack/blob/main/pyproject.toml)
[![License: MIT](https://img.shields.io/github/license/eschaar/vstack?color=5F7A1F)](https://github.com/eschaar/vstack/blob/main/LICENSE)
[![GitHub Discussions](https://img.shields.io/badge/discussions-ask%20%26%20share-blueviolet?logo=github)](https://github.com/eschaar/vstack/discussions)

The VS Code-native AI workflow system for backend engineering.

vstack installs structured agents, skills, instructions, and prompts into `.github/` so GitHub Copilot Agent Mode can run repeatable backend workflows with clear role boundaries.

It provides six delivery roles for end-to-end software work: `product`, `architect`, `designer`, `engineer`, `tester`, and `release`, coordinated by `planner`.

## Quickstart

```bash
pipx install vstack
cd /path/to/your/project
vstack install
vstack validate
```

Then open Copilot Chat, switch to Agent mode, and select the `planner` agent.

## Quick upgrade

Patch or minor upgrade:

```bash
pipx upgrade vstack
cd /path/to/your/project
vstack init
```

Major upgrade:

```bash
pipx upgrade vstack
cd /path/to/your/project
vstack migrate
vstack init
```

If you see a legacy manifest schema warning:

```bash
vstack manifest upgrade
vstack init
```

## Try it now

In Copilot Chat after selecting `planner`:

```text
Run the workflow for this repository change.
```

## Full docs on GitHub

- User docs index: <https://github.com/eschaar/vstack/blob/main/docs/user/README.md>
- Install and upgrade: <https://github.com/eschaar/vstack/blob/main/docs/user/how-to/install-and-upgrade.md>
- Troubleshooting: <https://github.com/eschaar/vstack/blob/main/docs/user/how-to/troubleshooting.md>
- CLI commands reference: <https://github.com/eschaar/vstack/blob/main/docs/user/reference/cli-commands.md>
- Configuration reference: <https://github.com/eschaar/vstack/blob/main/docs/user/reference/configuration.md>
- Workflow modes explanation: <https://github.com/eschaar/vstack/blob/main/docs/user/explanation/workflow-modes.md>
- Full repository docs: <https://github.com/eschaar/vstack/tree/main/docs>
