---
description: 'Audit dependencies for vulnerabilities, outdated versions, licence risks, and supply chain hygiene.'
name: dependency-audit
argument-hint: '[dependency manifest, lockfile, or package scope]'
agent: tester
tools:
  - read
  - search
---
Audit the provided dependency manifest or lockfile for vulnerabilities, outdated packages, licence risks, and supply chain hygiene.

Prefer evidence from the manifest itself; flag items that need external verification.

Output exactly in this format:

## Vulnerabilities

List dependencies with known CVEs or security advisories.

For each item:

- package name and version
- CVE or advisory reference if known
- severity: critical | high | medium | low
- recommended action (upgrade, replace, or accept with rationale)

## Outdated Packages

List dependencies significantly behind latest stable releases where risk is meaningful.
Do not list low-impact minor version differences.

For each item:

- package name: current version → latest stable
- risk of staying on current version in one sentence

## Licence Risks

List licences that may conflict with the project's distribution model.

For each item:

- package name
- licence identifier
- conflict or concern in one sentence

## Pinning and Version Policy

- all direct dependencies pinned: yes | no | partial
- unpinned transitive dependencies with risk: list or none
- version ranges that allow breaking upgrades: list or none

## Supply Chain Hygiene

List packages with unusual provenance concerns: abandoned maintainers, single-maintainer projects, recent ownership transfers, or typosquatting risk.

## Recommended Actions

Ordered action list by priority (critical first).

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"dependency-audit","artifact_type":"prompt","artifact_version":"20260502009","generator":"vstack","vstack_version":"3.6.0"} -->
