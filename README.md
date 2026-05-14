<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/branding/vstack_dm.png">
    <img src="assets/branding/vstack.png" alt="vstack" width="400">
  </picture>

[![PyPI version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpypi.org%2Fpypi%2Fvstack%2Fjson&query=%24.info.version&label=PyPI&color=0B8A6F&cacheSeconds=300 "Latest PyPI release")](https://pypi.org/project/vstack/)
[![Python version](https://img.shields.io/badge/python-3.11--3.14-0B8A6F "Supported Python versions")](pyproject.toml)
[![Verify status](https://img.shields.io/github/actions/workflow/status/eschaar/vstack/verify.yml?label=verify&color=1D6FA5 "Build and test status")](https://github.com/eschaar/vstack/actions/workflows/verify.yml)
[![Security checks](https://img.shields.io/github/actions/workflow/status/eschaar/vstack/security.yml?label=security&color=B15E00 "Security workflow status")](https://github.com/eschaar/vstack/actions/workflows/security.yml)
[![Runtime: PyYAML](https://img.shields.io/badge/runtime-PyYAML-5B6C8F "One runtime dependency: PyYAML")](pyproject.toml)
[![License: MIT](https://img.shields.io/github/license/eschaar/vstack?color=5F7A1F "Project license")](LICENSE)
[![GitHub Discussions](https://img.shields.io/badge/discussions-ask%20%26%20share-blueviolet?logo=github "GitHub Discussions")](https://github.com/eschaar/vstack/discussions)

</div>

> **The VS Code-native AI workflow system for backend engineering.**

vstack is a VS Code-native AI engineering workflow system for backend services,
libraries, APIs, and adjacent platform work. It installs structured agents,
skills, instructions, and prompts into `.github/` so GitHub Copilot Agent Mode
has a clear operating model instead of ad hoc chat prompts.

What gets built is determined by the product vision. vstack fixes the delivery
roles and boundaries: `product`, `architect`, `designer`, `engineer`, `tester`,
and `release`, coordinated by `planner`.

vstack started as a rethink inspired by [gstack](https://github.com/garrytan/gstack),
but was rebuilt around a template-driven, VS Code-first workflow model.

______________________________________________________________________

## ❔ Why vstack

- Fixed role model with explicit ownership boundaries
- Template-driven install model from `src/vstack/_templates/`
- Backend-first verification, security, and release discipline
- One runtime dependency: [PyYAML](https://pypi.org/project/PyYAML/)
- Works at project scope or globally in the VS Code user profile

______________________________________________________________________

## 🚀 Quickstart

```bash
# 1. Install the CLI once, globally
pipx install vstack

# 2. Move to your repository root
cd /path/to/your/project
vstack install

# 3. Confirm setup
vstack validate
```

When you omit `--target`, vstack uses the current working directory.

Then open Copilot Chat and choose the `planner` agent in the agent picker.

For a direct specialist check, choose the `tester` agent and ask:

```text
Verify this repository and summarize findings.
```

______________________________________________________________________

## ⬆️ Quick upgrade

### Patch or minor (same major)

```bash
pipx upgrade vstack
cd /path/to/your/project
vstack init
```

### Major (for example `v2 -> v3`)

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

______________________________________________________________________

## 🧪 Try it now

Open Copilot Chat, switch to Agent mode, and select the `planner` agent.

Prompt to run:

```text
Run the workflow for this repository change.
```

______________________________________________________________________

## 📚 User documentation

- [Start here](docs/user/start-here.md)
- [User docs index](docs/user/README.md)
- [Install and upgrade guide](docs/user/how-to/install-and-upgrade.md)
- [Troubleshooting](docs/user/how-to/troubleshooting.md)
- [CLI commands reference](docs/user/reference/cli-commands.md)
- [Configuration reference](docs/user/reference/configuration.md)
- [Hooks reference](docs/user/reference/hooks.md)
- [Prompts overview](docs/user/reference/prompts-overview.md)
- [Skills overview](docs/user/reference/skills-overview.md)
- [Instructions overview](docs/user/reference/instructions-overview.md)
- [Workflow modes explanation](docs/user/explanation/workflow-modes.md)

______________________________________________________________________

## 🤝 Contributing and project docs

- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Architecture docs](docs/architecture/overview.md)
- [Design docs](docs/design/overview.md)
- [Product docs](docs/product/vision.md)
