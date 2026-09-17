# Environment Verification

Proof that each teammate's dev environment works. Do this once after setup, and again after any change to the Dockerfile, `requirements.lock`, or `package-lock.json`.

## How to verify

```bash
lando start
lando npm ci
lando verify      # must end with "All checks passed"
```

If it fails, apply the fix `lando doctor` prints (usually `lando rebuild -y` or `lando npm ci`) and run it again.

## Status

| Teammate | Date | OS | Commit | `lando verify` | Notes |
| --- | --- | --- | --- | --- | --- |
| _Name_ | _YYYY-MM-DD_ | _macOS 15 / Windows 11 / Ubuntu 24.04_ | _short SHA_ | _9/9 passed_ | _any fix needed_ |

## Proof

Add a section with the summary block from the end of `lando verify`.

### Name — YYYY-MM-DD

<details>
<summary><code>lando verify</code> output</summary>

```
Summary
  ✓ Environment doctor
  ✓ Python lint
  ✓ Python formatting
  ✓ Environment tests
  ✓ Unit tests
  ✓ Smoke tests
  ✓ Frontend lint
  ✓ Frontend tests
  ✓ Frontend build

All checks passed. Your environment matches CI.
```

</details>

Problems hit and how you fixed them:

- _e.g. Node was 22 instead of 20; fixed with `lando rebuild -y`._
