# vstack — vision

> Maintained by: **product** role\
> Last updated: 2026-03-28

## what is vstack

vstack is a VS Code–native AI engineering workflow system. It provides a set of
structured skills — executable by GitHub Copilot in Agent Mode — for planning,
reviewing, verifying, and releasing software.

What gets built is determined by the product vision: a microservice, an API, a
package, an app, or a fullstack system. The designer role adapts to frontend, backend,
or fullstack scope. The tester role adjusts its checks accordingly.
vstack itself has no opinion on what you build — only on how you build it well.

Each skill is a procedure. Each role is a persona. Together they form a repeatable
engineering pipeline that works inside VS Code without any external binary requirements.

______________________________________________________________________

## why it exists

Most AI workflow systems are built around a fixed assumption of what you're building —
typically a fullstack app with a browser-driven QA loop. That assumption is baked in
and hard to override.

vstack is different:

- The **product role** defines the vision: what kind of system, what scope, what success looks like.
- Roles downstream (architect, designer, engineer, tester, release) read that
  vision and adapt their work to it.
- Browser automation, frontend concerns, and mobile targets are available but not assumed.
- **VS Code + Copilot Agent Mode** is the runtime, and `vstack` CLI is the standard install path.
- No proprietary platform or closed runtime is required.

The result is a workflow system that fits microservices, packages, APIs, apps, and
fullstack products equally — driven by the product vision, not by tooling assumptions.

______________________________________________________________________

## design principles

1. **Vision-driven scope.** The product role defines what gets built — microservice,
   package, API, app, or fullstack system. All other roles adapt to that vision.
   No product type is assumed or privileged by the tooling.

1. **VS Code native.** Skills are generated from templates and installed into `.github/agents/`
   and `.github/skills/` by `vstack install --target <project>` (primary, project-local path).
   For cross-workspace usage, use `vstack install --global`.
   No extension required.

1. **Templates over hand-editing.** Source of truth lives under `src/vstack/_templates/`:
   `skills/<name>/template.md` and `agents/<name>/{config.yaml,template.md}`.
   Generated files are overwritten on each build. Edit templates, then regenerate.

1. **Minimal runtime dependencies.** The runtime core is Python 3 stdlib only
   (no Bun/Node runtime required). Developer workflow may use Poetry and dev tooling
   (ruff, mypy, pytest) for quality checks.

1. **Role model.** Six fixed roles (product, architect, designer, engineer, tester,
   release) define who produces what. Each role owns a specific set of
   artifacts. Agents communicate through files on disk.

1. **Pipeline-ready.** Today each skill runs in a single model call. If needed later,
   the system can move to an orchestrated multi-role pipeline by adding a runner,
   without rewriting skills.

______________________________________________________________________

## who uses it

An engineer or small team that wants:

- A repeatable, role-based engineering workflow in VS Code
- AI-assisted planning, architecture reviews, verification, security audits, and releases
- A system that adapts to what they're building — not the other way around
- Extensible via Markdown templates, with no proprietary lock-in

______________________________________________________________________

## scope

Scope is not fixed by vstack — it is set by the product vision for each project.

**Supported product types:**

- Microservices and backend APIs (REST, gRPC, event-driven)
- Internal libraries and packages (Python, Go, TypeScript/Node, Java)
- Fullstack applications (frontend + backend)
- Standalone apps

**Adapts per vision:**

- Designer role: backend-mode (API specs, data contracts) or frontend-mode (UI/UX, components)
- Tester role: contract + integration tests for services; E2E for apps with a UI
- Tester role: security + performance auditing, regardless of product type

**Tooling non-goals (independent of product scope):**

- No browser binary required by default
- No VS Code extension packaging
- No cloud service dependencies
- No external runtime Python packages
