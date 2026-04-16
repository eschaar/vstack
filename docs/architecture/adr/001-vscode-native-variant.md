# ADR-001: VS Code–Native Variant

> Maintained by: **agents** role

**date:** 2026-03-27\
**status:** accepted

## context

An AI engineering workflow system with a template-driven skill architecture was available
as inspiration, but was optimised for full-stack app development with headless browser
automation — unsuitable for backend/microservice workflows where browser automation is
irrelevant.

VS Code + GitHub Copilot is a dominant development environment that lacked an equivalent
system. Modern models (Claude Sonnet/Opus 4.6, GPT-5.3 Codex) can execute multi-step
workflows via VS Code Agent Mode.

## decision

Create `vstack` as a VS Code-native AI engineering workflow system that:

- Implements a template-driven skill architecture
- Removes any browser binary dependency from core
- Targets backend/microservice development
- Generates GitHub Copilot-compatible agent files
- Does not depend on any upstream project at runtime

## alternatives considered

1. Contribute backend skills to an existing tool's upstream — rejected because the VS Code
   integration goal requires structural changes the upstream may not want.
1. Entirely new architecture from scratch — rejected as the template + resolver pattern
   is well-suited and proven.

## rationale

Minimize dependency while enabling VS Code deployment. The template system is portable
and the only significant addition is the VS Code output format.

## impact on future orchestrated pipeline

Current single-call architecture is identical to a single-call execution model.
No new risk introduced for the pipeline migration path.
