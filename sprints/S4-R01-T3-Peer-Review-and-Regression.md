# S4-R01-T3 Peer Review and Regression Evidence

**Jira:** SCRUM-169
**Owner:** Joon Rho, R01

## Status

| Item | State |
|---|---|
| Local regression run | Passing |
| CI run | Not attached yet |
| Pull request | Not linked yet |
| Independent peer review | Not done yet |

The task is not complete until the last three rows are filled in.

## Review request

The reviewer should not be the author. Eric or Nathan are the natural choices, since Eric owns the adapter the profiles feed and Nathan owns CI. Ask for the review on the pull request, so it is linked and timestamped on GitHub.

What to review, in commit order:

| Commit | Files |
|---|---|
| Profile loader | `src/slidekick/gesture_profile.py`, `profiles/default.json`, `tests/unit/test_gesture_profile.py` |
| Session layer | `src/slidekick/session_coordinator.py`, `tests/unit/test_session_apply_profile.py` |
| Pipeline tests | `tests/integration/test_gesture_profile_pipeline.py` |
| Documents | `docs/gesture-profile-architecture.md`, the two updated notes, `docs/sprint4/` |

Questions for the reviewer:

1. Is refusing `apply_profile` while RUNNING the right rule, or should a swap be allowed with a warning?
2. Is the strict schema right, meaning exactly three fields and the number 1 as the version?
3. Is there any route a bad profile could take to the keyboard that the checks miss?
4. Do the error messages give enough to fix a profile without exposing too much?
5. Do the contracts in the interface document match your part of the code?

## Review record

| Reviewer | Date | Files checked | Findings | Resolution | Decision |
|---|---|---|---|---|---|
| Not yet reviewed | | | | | Pending |

## Regression results

These runs were local. The environment was Python 3.12 and Node 22 on Linux with no display and no camera. CI uses Python 3.11 and Node 20, so the CI run is the one that counts for the pinned versions.

### Python

| Folder | Result | Before this work |
|---|---|---|
| `tests/unit` | 313 passed | 206 |
| `tests/recognition` | 29 passed | 29 |
| `tests/integration` | 37 passed | 27 |
| `tests/performance` | 5 passed, 1 skipped, 1 expected failure | same |
| `tests/smoke` | 1 passed | 1 |

The new tests are 117 cases in three files: 89 in the profile tests, 18 in the session tests and 10 in the pipeline tests. No existing test was changed or removed.

| Check | Result |
|---|---|
| `ruff check .` | All checks passed |
| `ruff format --check .` | 82 files already formatted |
| `bandit -r src/ windows_helper.py` | No issues identified |

### Frontend

No frontend file was changed. The checks were run to confirm the snapshot is healthy.

| Command | Result |
|---|---|
| `npm run lint` | 0 warnings and 0 errors on 31 files |
| `npm run typecheck` | Clean |
| `npm run test` | 88 passed in 11 files |
| `npm run build` | Built |

### Do the tests catch breakage

Six deliberate breakages were made in the new code, one at a time. Every one made tests fail, and restoring the code brought all 117 back. The list is in `evidence/s4_r01_mutation_check.txt`. The changes included allowing a profile change while RUNNING, accepting repeated JSON keys, skipping the file size limit and accepting unknown fields.

### Not run

`tests/environment` was left out because it checks the pinned Python version, `pip-compile` and git ignore rules, and the sandbox has none of those. It runs in CI.

## Not verified

- A live run with a camera, a real slideshow and real key presses.
- The merged develop branch. This work was built on a snapshot taken before the guided enrollment merge. Run the commands below on merged develop and compare.
- The profile UI and enrollment code, which were not in the snapshot.

## Commands to reproduce

```text
python -m pytest -q tests/unit tests/integration tests/recognition tests/performance tests/smoke
ruff check .
ruff format --check .
python -m bandit -r src/ windows_helper.py
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run test
npm --prefix frontend run build
```

## Links to fill in

| Item | Link |
|---|---|
| Pull request | |
| Commit hash for the assessed code | |
| CI run, passing | |
| Review thread | |
| Jira | SCRUM-167, SCRUM-168, SCRUM-169 |
