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

A fix is available for all of them via `npm audit fix`. Fixed in Test 4.

## Test 3: CI Security Gate

Checked `.github/workflows/ci.yml`:

- Python scan (`pip_audit`, line 200) runs with no `|| true` or
  `continue-on-error`, so a vulnerability found here fails the build.
- Frontend scan (`npm audit`, line 214) runs as `npm audit || true`, so its
  result can never fail the build, no matter what it finds.

Finding: the CI security gate only enforces on the Python side. The frontend
dependency scan is informational only right now.

## Test 4: Remediation Testing

Run on November 5, 2026 on branch `feature/S4-R02-SOC2-C03-dependency-scan`.

1. `npm audit fix` updated 19 packages. Only `frontend/package-lock.json`
   changed; `package.json` did not, so no major-version bumps were needed.
2. Reran `npm audit`: 0 vulnerabilities (was 5: 3 high, 2 moderate).

| Package | Before | After |
|---|---|---|
| vite | 8.3.0–8.3.2 | 8.3.6 |
| source-map-js | 1.0.0–1.2.1 | 1.2.2 |
| undici | 7.0.0–7.30.0 | 7.30.1 |
| vitest / @vitest/mocker | ≤4.1.11 | 4.1.12 |

3. Regression checks after the update: type check, lint, and build pass;
   88/88 frontend tests pass (same as before the update).
4. No vulnerabilities required a breaking major-version upgrade.

## CI Security Gate Fix

Test 3 found that `npm audit || true` in `.github/workflows/ci.yml` line 214
meant the frontend scan could never fail the build. Fixed by changing it to
`npm audit --audit-level=high`, so high and critical findings fail CI. This
was done after Test 4, so the change doesn't block anyone's pull requests.

Verified on November 5, 2026 by running both commands against the frontend
lock file from before and after the Test 4 fix (`npm audit --package-lock-only`
in a scratch folder):

| Lock file | `npm audit \|\| true` (old) | `npm audit --audit-level=high` (new) |
|---|---|---|
| Before fix: 5 vulnerabilities (3 high) | exit 0, CI passes | exit 1, CI fails |
| After fix: 0 vulnerabilities | exit 0, CI passes | exit 0, CI passes |

Result: the old step passed even with 3 high-severity vulnerabilities. The new
step blocks them and passes once they're fixed. The frontend scan now enforces
the same way the Python scan does.
