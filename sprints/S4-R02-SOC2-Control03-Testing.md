# S4-R02 SOC 2 Control 03 Testing

## Purpose

Verify SOC 2 Control 03 (dependency vulnerability management) using the
scanners and tests already set up in Sprints 2 and 3. Four tests: Python
dependency scan, frontend dependency scan, CI security gate, remediation
testing.

## Test 1: Python Dependency Scan

Command (same as CI, `.github/workflows/ci.yml` lines 194-200):

```
python -m pip install pip-audit==2.7.3
python -m pip_audit -r requirements.lock --desc on
```

Result: No known vulnerabilities found.

## Test 2: Frontend Dependency Scan

Command (same as CI, `.github/workflows/ci.yml` line 214):

```
npm audit
```

Result: 5 vulnerabilities found (3 high, 2 moderate), all in dev dependencies
(not shipped to users):

| Package | Severity | Issue |
|---|---|---|
| vite | high | cross-origin script execution, file access outside server.fs.allow, Windows editor-launch command issues |
| undici | high | denial of service (several), TLS cert validation bypass, cache poisoning |
| source-map-js | high | denial of service via source-map section offsets |
| @vitest/mocker (vitest) | moderate | code injection via mock registration, Windows path traversal |

A fix is available for all of them via `npm audit fix`. Not run yet —
remediation and retest planned for next session.

## Test 3: CI Security Gate

Checked `.github/workflows/ci.yml`:

- Python scan (`pip_audit`, line 200) runs with no `|| true` or
  `continue-on-error`, so a vulnerability found here fails the build.
- Frontend scan (`npm audit`, line 214) runs as `npm audit || true`, so its
  result can never fail the build, no matter what it finds.

Finding: the CI security gate only enforces on the Python side. The frontend
dependency scan is informational only right now.

## Test 4: Remediation Testing

Needed because Test 2 found issues to fix. Not run yet. Plan for next
session:

1. Run `npm audit fix`
2. Rerun the frontend test suite to confirm nothing broke
3. Rerun `npm audit` to confirm the count drops to zero
4. Note any vulnerability that can't be fixed without a breaking
   major-version bump

## Follow-up: CI Security Gate

Test 3 found that `npm audit || true` in `.github/workflows/ci.yml` line 214
means the frontend scan can never fail the build. Proposed fix for next
session: remove `|| true`, or use `npm audit --audit-level=high` so CI fails
on real vulnerabilities instead of only logging them.
