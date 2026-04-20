# vstack

Inspired by gstack, vstack is intentionally rebuilt around a VS Code-native,
template-driven workflow model.

vstack is a VS Code–native AI engineering workflow system. It provides structured
skills — executable by GitHub Copilot in Agent Mode — for planning, reviewing,
verifying, and releasing software.

What gets built (microservice, API, package, app, fullstack system) is determined
by the product vision. vstack adapts to that vision through 6 fixed roles:
**product, architect, designer, engineer, tester, release.**

______________________________________________________________________

## install

Requires **Python 3.11-3.14**.

```bash
pip install vstack
```

Then install vstack artifacts into your project:

```bash
vstack install --target /path/to/your/project
```

Or into the VS Code user profile (available in all projects for agents/prompts/instructions/skills):

```bash
vstack install --global
```

No extra VS Code settings needed. Agents are auto-discovered from `.github/agents/`
in the workspace and from the user profile agents directory. Skills installed globally
are available under the VS Code user profile skills directory.

______________________________________________________________________

## agent and skill usage

### Agents vs. skills: what is the difference?

- **Agents** (like `@product`, `@tester`) are the main interface. Use them for all primary flows. Agents automatically select the right skills for their role and context.
- **Skills** (like `/verify`, `/security`) can be invoked directly if you want to force a specific check. This is optional and usually not needed.

#### Invocation examples

| Goal                  | Agent invocation | Optionally: direct skill invocation |
| --------------------- | ---------------- | ----------------------------------- |
| Gather requirements   | `@product`       |                                     |
| Architecture review   | `@architect`     |                                     |
| API design            | `@designer`      |                                     |
| Code review           | `@engineer`      | `/code-review`                      |
| Verification/QA       | `@tester`        | `/verify`                           |
| Security check        | `@tester`        | `/security`                         |
| Performance benchmark | `@tester`        | `/performance`                      |
| Prepare release       | `@release`       |                                     |

> **Note:** You can also force a skill via an agent, e.g. `@tester /security` for a security check by the tester agent.

#### Subagent pattern

The product agent can invoke other agents as subagents to orchestrate a complete flow:

```text
@product Deliver a requirements-to-release plan for a new payments service
```

This automatically triggers:

- @product → requirements
- @architect → architecture
- @designer → API contract
- @engineer → implementation
- @tester → verification
- @release → release gating

#### Use case 1: New API from idea to release

1. `@product` — (agent, requirements and acceptance)
1. `@architect` — (agent, architecture review)
1. `@designer` — (agent, OpenAPI spec)
1. `@engineer` — (agent, implementation)
1. `@tester` — (agent, full QA)
1. `@tester /security` — (agent with explicit skill invocation, security check)
1. `@release` — (agent, release gating)

#### Use case 2: Security regression in authentication

1. `@tester /security` — (agent with explicit skill invocation)
1. `@engineer` — (agent, bugfix)
1. `@tester` — (agent, re-verification)
1. `@release` — (agent, release)

#### Use case 3: Refactor and performance improvement

1. `@engineer` — (agent, refactor)
1. `@tester /performance` — (agent with explicit skill invocation)
1. `@engineer` — (agent, optimization)
1. `@tester` — (agent, confirm performance gain)
1. `@release` — (agent, release)

______________________________________________________________________

## Using vstack in Copilot Agent Mode

### 1. Open Copilot Chat

`Ctrl+Shift+I` (or `Cmd+Shift+I`) — or click the Copilot icon in the sidebar.

### 2. Switch to Agent Mode

In the Copilot Chat panel, click the mode selector (shows "Ask" by default) and
switch to **Agent**.

### 3. Invoke a role

```text
@product Review my plan for the new payments service
@architect Review the API contracts in src/api/
@tester
@tester Run a security audit
```

Each role agent uses the appropriate skills automatically.
You can also ask a role to use a specific skill:

```text
@tester use the verify skill with regression focus and report findings
@tester run the security skill on the auth module
```

### 4. Available roles and their primary skills

| Role      | Invocation   | Primary skills                                          | Default concise mode |
| --------- | ------------ | ------------------------------------------------------- | -------------------- |
| product   | `@product`   | vision, requirements, onboard, docs                     | compact              |
| architect | `@architect` | architecture, adr                                       | normal               |
| designer  | `@designer`  | design, openapi, consult, docs                          | compact              |
| engineer  | `@engineer`  | code-review, debug, refactor, migrate, dependency, docs | compact              |
| tester    | `@tester`    | verify, inspect, security, incident, dependency, docs   | ultra                |
| release   | `@release`   | release-notes, pr, docs                                 | compact              |

Full skill index: [docs/design/skills.md](docs/design/skills.md)

______________________________________________________________________

## model guidance

| Use case                 | Recommended model                    |
| ------------------------ | ------------------------------------ |
| `@product`, `@architect` | Claude Sonnet 4.6 or Claude Opus 4.6 |
| `@tester`, `@engineer`   | Claude Sonnet 4.6                    |
| `@release`               | Claude Sonnet 4.6                    |
| Complex debugging        | Claude Opus 4.6 or GPT-5.3 Codex     |
| Quick tasks              | Any model                            |

Claude Sonnet 4.6 is the best balance of speed, quality, and cost for most runs.
Use Claude Opus 4.6 for architecture reviews or complex debugging.

In Copilot Chat, click the model selector to switch.

______________________________________________________________________

## tips

**Give the agent your project context:**

```text
/verify Please first read CONTRIBUTING.md for test commands
```

**Scope the agent's focus:**

```text
/code-review Review changes in src/api/ only
/security Audit the authentication module in src/auth/
```

**Controlling response verbosity:**

Every role agent supports the `concise` skill. Switch response density without regenerating any artifacts:

```text
/concise normal    — full explanations (architect default)
/concise compact   — shorter prose, same technical accuracy (most role default)
/concise ultra     — maximum brevity, facts and commands only (tester default)
/concise status    — show active mode, session override, and agent default
/concise on        — alias for compact
/concise off       — alias for normal
```

The mode is session-scoped — no reinstall needed. Security warnings and destructive
action prompts always use `normal` regardless of active mode.

**Typical workflow for a new feature:**

```text
1. /vision       — validate the approach
2. /architecture — lock down the technical design
3. (implement)
4. /verify       — test and validate
5. /release      — cut the release
```

______________________________________________________________________

## development

Requires **Poetry** and **Python 3.11-3.14**.

```bash
git clone https://github.com/your-org/vstack
cd vstack
poetry install
```

### quick commands (make)

```bash
make help
make bootstrap
make install
make check
make vstack-install
make ci
```

### development tasks

```bash
poetry run vstack validate      # validate templates without writing files
poetry run vstack install       # install all artifacts -> .github/
poetry run vstack verify        # full validation suite
make test-local                 # run pytest on current interpreter
make test                       # run tests on py311-py314 via tox
make tox                        # run tests on py311-py314 (when installed)
```

### local multi-python testing (pyenv + tox)

This repository keeps its local interpreter order in `.python-version` so `tox`
can resolve the supported runtimes consistently.

Install and activate the supported Python runtimes with `pyenv`:

```bash
pyenv install 3.11.14
pyenv install 3.12.12
pyenv install 3.13.12
pyenv install 3.14.3
pyenv local 3.14.3 3.13.12 3.12.12 3.11.14
```

That command writes the repo-local `.python-version` file.

Run cross-version tests locally:

```bash
make tox      # pytest on py311, py312, py313, py314
make tox-all  # all tox envs: tests + lint + type
```

**Editing templates:** source of truth is always `src/vstack/_templates/<type>/<name>/{config.yaml,template.md}`. Never edit generated files in `.github/`.

```bash
vim src/vstack/_templates/skills/verify/template.md
vim src/vstack/_templates/agents/engineer/template.md
vim src/vstack/_templates/instructions/python/template.md
poetry run vstack validate
poetry run pytest
```

______________________________________________________________________

## project structure

```bash
vstack/
├── src/vstack/              ← Python package (source of truth)
│   ├── frontmatter/         ← parser, builder, schema
│   ├── artifacts/           ← GenericArtifactGenerator
│   ├── skills/              ← SKILL_SCHEMA, SKILL_TYPE
│   ├── agents/              ← AGENT_SCHEMA, AGENT_TYPE
│   ├── instructions/        ← instruction artifact config + generator
│   ├── prompts/             ← prompt artifact config + generator
│   ├── cli/                 ← commands, parser, constants
│   └── _templates/
│       ├── skills/<name>/config.yaml        ← skill frontmatter fields
│       ├── skills/<name>/template.md        ← skill instructions body
│       ├── skills/_partials/               ← shared partials
│       ├── agents/<name>/config.yaml       ← agent frontmatter fields
│       ├── agents/<name>/template.md       ← agent instructions body
│       ├── instructions/<name>/config.yaml ← instruction frontmatter
│       ├── instructions/<name>/template.md ← instruction body
│       ├── prompts/<name>/config.yaml      ← prompt frontmatter
│       └── prompts/<name>/template.md      ← prompt body
├── docs/
│   ├── architecture/
│   │   ├── architecture.md  ← system structure
│   │   └── adr/             ← architecture decision records
│   ├── design/
│   │   ├── design.md        ← generator and builder internals
│   │   ├── skills.md        ← full skill index
│   │   └── workflow.md      ← execution model
│   └── product/
│       ├── requirements.md
│       ├── roadmap.md       ← milestones
│       └── vision.md
├── tests/
│   └── vstack/
└── Makefile                ← generic local dev tasks
```

______________________________________________________________________

## troubleshooting

**Agents not appearing:**

1. Run `poetry run vstack install --global` (or `vstack install --global`)
1. Ensure templates exist under `src/vstack/_templates/agents/`
1. Reload VS Code: `Ctrl+Shift+P` → `Developer: Reload Window`

**Best-practice local workflow:**

1. `make bootstrap` once per machine/repo clone
1. `make check` before every commit
1. `make ci` to mirror the quality gate locally

**Agent is not running commands:**
Make sure you are in **Agent Mode** — not Ask or Edit mode.

**Agent search is noisy (dependency folders):**
Use workspace-local exclusions in VS Code to keep context focused.

```json
{
	"search.exclude": {
		"**/.venv": true,
		"**/venv": true,
		"**/env": true,
		"**/node_modules": true,
		"**/__pycache__": true,
		"**/dist": true,
		"**/build": true,
		"**/.git": true
	},
	"files.watcherExclude": {
		"**/.venv/**": true,
		"**/venv/**": true,
		"**/env/**": true,
		"**/node_modules/**": true,
		"**/__pycache__/**": true,
		"**/dist/**": true,
		"**/build/**": true,
		"**/.git/**": true
	}
}
```

______________________________________________________________________

## roadmap

See [docs/product/roadmap.md](docs/product/roadmap.md)

______________________________________________________________________

## license

MIT. See [LICENSE](LICENSE).
