# Security Report

**Branch:** `feature/publish_in_homebrew`\
**Date:** 2026-06-02\
**Scope:** Repository snapshot including the new `publish-homebrew` workflow job. Python source analysis unchanged; CI/CD workflow security assessment added.\
**Method:** OWASP Top 10 + STRIDE framing for a local CLI tool plus supply-chain controls for the new release pipeline job.

______________________________________________________________________

## Verdict

| Category                          | Findings                          | Blocking                                 |
| --------------------------------- | --------------------------------- | ---------------------------------------- |
| Static analysis (bandit)          | 1 LOW                             | No — informational; import advisory only |
| Dependency CVEs                   | 0 known CVEs in current local env | No                                       |
| Secrets in source                 | None                              | —                                        |
| Injection risk                    | None identified                   | —                                        |
| Auth / access control             | N/A (local CLI, no network)       | —                                        |
| CI/CD workflow (publish-homebrew) | See W-001 – W-004 below           | No — all informational or design notes   |

> **Ship readiness: PASS** — no blocking security findings; workflow security controls verified.

______________________________________________________________________

## OWASP Top 10 Assessment

This is a **local CLI tool** — no web server, no user sessions, no database, no network endpoints. Most OWASP categories are not applicable. Relevant categories are assessed below.

| #   | Category                  | Status | Notes                                                                       |
| --- | ------------------------- | ------ | --------------------------------------------------------------------------- |
| A01 | Broken Access Control     | N/A    | Local filesystem operations only                                            |
| A02 | Cryptographic Failures    | PASS   | No cryptographic operations in source                                       |
| A03 | Injection                 | PASS   | Subprocess uses fixed list args (no shell=True, no user-interpolated input) |
| A04 | Insecure Design           | PASS   | No privileged operations, no credential storage                             |
| A05 | Security Misconfiguration | PASS   | No config files with secrets; no exposed ports                              |
| A06 | Vulnerable Components     | PASS   | Local environment advisories remediated and re-verified                     |
| A07 | Auth / Identity Failures  | N/A    | No authentication surface                                                   |
| A08 | Software/Data Integrity   | PASS   | Checksums used for artifact validation in install/uninstall                 |
| A09 | Logging Failures          | PASS   | No sensitive data logged                                                    |
| A10 | SSRF                      | N/A    | No HTTP client usage                                                        |

______________________________________________________________________

## Static Analysis Findings (bandit)

```
bandit -r src/
Run started: 2026-05-14 14:22:20+00:00
Issues: 1  HIGH=0  MED=0  LOW=1
  [LOW] B404  vstack/constants.py:6 — Consider possible security implications associated with the subprocess module.
```

### S-001 — B404 subprocess import (LOW, informational)

**File:** `src/vstack/constants.py:6`

```python
import subprocess
```

Bandit flags any file that imports `subprocess`. This is a blanket informational note, not a finding tied to unsafe usage. The actual call site remains guarded (`# nosec B603 B607`) and uses a fixed arg list.

**Severity:** LOW — informational; not actionable.

______________________________________________________________________

## Dependency Audit (pip-audit)

Path note:

- CI workflow uses `pip-audit --requirement <(poetry export --without-hashes -f requirements.txt)`.
- In this local environment, `poetry export` is unavailable (`The requested command export does not exist`).
- Closest repo-used equivalent for local verification: direct `pip-audit` against the active virtualenv.

### Initial reproduction (before remediation)

```bash
source .venv/bin/activate
pip-audit
```

```text
Found 4 known vulnerabilities in 2 packages
pip 26.0.1     CVE-2026-3219
pip 26.0.1     CVE-2026-6357  fixed in 26.1
urllib3 2.6.3  CVE-2026-44431 fixed in 2.7.0
urllib3 2.6.3  CVE-2026-44432 fixed in 2.7.0
```

### Remediation applied

```bash
source .venv/bin/activate
python -m pip install --upgrade 'pip>=26.1' 'urllib3>=2.7.0'
```

Installed versions:

- `pip 26.1.1`
- `urllib3 2.7.0`

### Final verification

```
security check window (UTC): 2026-05-14T14:22:18Z → 2026-05-14T14:22:20Z
command: pip-audit
result: No known vulnerabilities found

note: pip-audit reports one non-blocking skip item for local package `vstack (0.0.0)` because it is not published on PyPI.
```

### S-002 — dependency advisories in local tooling environment (RESOLVED)

`pip-audit` initially reported advisories in local tooling packages (`pip`, `urllib3`). Those packages were upgraded in the active virtual environment and re-audited.

**Final status:** resolved.

______________________________________________________________________

## STRIDE Assessment

| Threat                 | Relevant surface                                  | Finding                               |
| ---------------------- | ------------------------------------------------- | ------------------------------------- |
| Spoofing               | No network/auth                                   | N/A                                   |
| Tampering              | Artifact checksums verified on uninstall          | PASS                                  |
| Repudiation            | No audit trail for local file ops                 | LOW — acceptable for a local dev tool |
| Information disclosure | No secrets stored, no network calls               | PASS                                  |
| Denial of service      | No resource-intensive loops exposed to user input | PASS                                  |
| Elevation of privilege | No sudo/elevated ops                              | PASS                                  |

______________________________________________________________________

## Secrets Scan

```
grep -r -E '(password|secret|api_key|token)\s*[=:]\s*["'\''][^"'\'']{8,}'  →  No matches in src/
```

No hardcoded secrets found.

______________________________________________________________________

## Summary of Advisory Items

| ID    | Severity      | Location / package                  | Action                                                                                                 |
| ----- | ------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------ |
| S-001 | LOW           | `src/vstack/constants.py`           | Keep B404 import advisory documented; no unsafe subprocess use                                         |
| S-002 | LOW           | `pip`, `urllib3` (dev env)          | **Resolved** by upgrading to `pip 26.1.1` and `urllib3 2.7.0`                                          |
| W-001 | PASS          | `publish-homebrew` feature flag     | Committed as `false`; enabled by explicit maintainer change only                                       |
| W-002 | PASS          | `publish-homebrew` actor check      | Mirrors `publish` job guard; no change needed                                                          |
| W-003 | PASS          | `publish-homebrew` sdist checksum   | Double-pinned: PyPI API vs downloaded tarball; formula embeds verified sha256                          |
| W-004 | INFORMATIONAL | `publish-homebrew` dispatch signing | Configure `HOMEBREW_TAP_DISPATCH_SECRET` and enforce verification in tap repo before enabling the flag |
| W-005 | PASS          | `publish-homebrew` curl dispatch    | No shell injection; JSON built via Python, passed as file to curl                                      |
| W-006 | PASS          | `publish-homebrew` token handling   | Token consumed from `secrets.*`; GitHub Actions masks it in logs                                       |

No remaining dependency CVEs were detected in the audited local environment. No security item blocks release.

______________________________________________________________________

## Workflow Security Assessment — `publish-homebrew` job

New job added to `.github/workflows/publish.yml` as part of Homebrew distribution support.

### W-001 — Feature flag gate (PASS)

`HOMEBREW_TAP_ENABLED: "false"` in workflow-level `env`. Job condition enforces
`env.HOMEBREW_TAP_ENABLED == 'true'`. The flag is committed as `false`, making the live job
inert until explicitly enabled by a maintainer commit.

### W-002 — Trusted actor validation (PASS)

The job repeats the same `TRUSTED_RELEASE_ACTORS` check already used in the `publish` job.
Untrusted release authors cannot trigger Homebrew dispatch.

### W-003 — Checksum verification (PASS)

The job fetches the sdist tarball from PyPI, computes `sha256sum` locally, and compares it
against the PyPI JSON API digest. The two values must match before the `repository_dispatch`
is sent. The formula in the tap repo will embed this verified sha256; Homebrew verifies it
again at install time (double-pinning).

### W-004 — Dispatch payload signing (INFORMATIONAL)

HMAC-SHA256 signing of the dispatch payload is implemented but gated behind the optional
`HOMEBREW_TAP_DISPATCH_SECRET` secret. If the secret is not configured the payload is sent
unsigned, and the tap repo's `formula-update.yml` should enforce signature verification before
accepting the event. Until the tap repo enforces signature checking, an attacker with
`HOMEBREW_TAP_TOKEN` access could send an unsigned `repository_dispatch` directly.

**Severity:** INFORMATIONAL — no exploit path exists within this repo; depends on tap repo
hardening. Action: configure `HOMEBREW_TAP_DISPATCH_SECRET` and enforce signature validation
in `formula-update.yml` before setting `HOMEBREW_TAP_ENABLED: "true"`.

### W-005 — Shell injection via environment variables (PASS)

The dispatch-body JSON is built by a Python script using `json.dumps` with explicit
`sort_keys=True` and `separators` — no shell interpolation of user-controlled values.
The curl step passes `--data-binary @dispatch-body.json` reading from a file, not from inline
shell expansion. No injection vector.

### W-006 — Token exposure (PASS)

`HOMEBREW_TAP_TOKEN` is consumed from `${{ secrets.HOMEBREW_TAP_TOKEN }}`. GitHub Actions
automatically masks registered secrets in log output. The token is never echoed or written
to disk.
