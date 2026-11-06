# S4-SOC2-C01-T4 Assessment Evidence and Results

**Jira:** SCRUM-173, with test work for SCRUM-171
**Control:** SOC 2 Control 01, Keyboard Command Authorization, aligned to CC6.1
**Owner:** Joon Rho, R01
**Date:** November 4, 2026

## Result

**Needs CI and review evidence before it can be called a pass.**

AC-01 to AC-05 pass on the assessed files. AC-05 failed on the original code and passes after remediation. AC-06 needs a CI run, a pull request and an independent review, none of which exist yet. The window focus risk stays open and is documented below.

## What was assessed

The repository snapshot `slidekick-develop` as uploaded, with the Control 01 changes applied. The snapshot is not a git checkout, so there is no commit hash. The assessed files are identified by SHA 256 in `evidence/assessed_file_hashes.txt`. Replace this with the commit and pull request once the branch is pushed.

| Item | Value |
|---|---|
| Local run | Python 3.12.3 on Linux, fake `pyautogui`, no display, no camera |
| CI target | Python 3.11 on ubuntu latest |
| Keyboard | Never touched. Every test uses the fake keyboard library from `tests/conftest.py` |

## Criteria matrix

| ID | Criterion | Original code | After remediation | Tests | Evidence |
|---|---|---|---|---|---|
| AC-01 | Allowlist and gesture to action contract documented, every configured action approved | Not met. No contract, no check | **Pass** | 8 | `command-authorization-contract.md`, `command_policy.py` |
| AC-02 | Unsupported, empty, non string and injected looking commands give zero key calls | Met in behavior, not proven | **Pass** | 35 | `control01_tests_verbose.txt` |
| AC-03 | Approved actions press only their documented key | Met | **Pass** | 9 | `control01_tests_verbose.txt` |
| AC-04 | READY, PAUSED and ENDED give zero adapter calls, RUNNING routes once | Met on the coordinator path | **Pass** | 27 | `control01_tests_verbose.txt` |
| AC-05 | Invalid mappings rejected before use, no arbitrary key can be introduced | **Failed.** Bad mappings loaded and `end` could press escape | **Pass** | 46 | `baseline_probe_output.txt`, `new_tests_vs_original_failures.txt` |
| AC-06 | Tests pass locally and in the relevant GitHub Actions job, with commit and PR identified | Not met | **Pending.** Local pass only | all | `ci_equivalent_summary.txt`, CI run still needed |

Test counts are the new tests in `tests/unit/test_control01_keyboard_command_authorization.py`. AC-02 includes one extra controller level test that also supports AC-04. The file has 125 tests, all passing.

READY in the criteria is the `IDLE` state in the code. IDLE, PAUSED and ENDED were each tested with both gestures, and RUNNING was tested with both gestures dispatching once.

## Before and after

The 125 new tests were run against the original controller to prove they catch the gaps.

| Run | Result |
|---|---|
| New tests on original controller | 46 failed, 79 passed |
| New tests on remediated controller | 125 passed |

The 46 failures break down like this.

| Cause | Tests |
|---|---|
| Malformed gesture ids, command targets and non mapping profiles loaded without error | 33 |
| Dispatch corruption tests that rely on the new internal field, so they fail structurally on the original | 5 |
| Shared default dictionary could be edited, plus 3 later tests that failed only because an earlier test had already edited it | 4 |
| `end` reachable from a gesture | 1 |
| Bindings could be edited from outside | 1 |
| No atomic update method existed | 2 |

The hands on probe in `baseline_probe.py.txt` shows the same thing with real controller calls. Before, binding a gesture to `end` pressed escape. After, the mapping is refused and nothing is pressed.

## Suites run

| Suite | Result |
|---|---|
| `tests/unit` | 206 passed |
| `tests/recognition` | 29 passed |
| `tests/integration` | 27 passed |
| `tests/performance` | 5 passed, 1 skipped, 1 expected failure |
| `tests/smoke` | 1 passed |
| `ruff check` and `ruff format --check` | Clean |
| `bandit` on `src/` and `windows_helper.py` | No issues |

The skipped and expected failure tests were already in the suite. The expected failure is the known 120 FPS recognition issue and is unrelated.

`tests/environment` was not counted. Four of its tests fail in this sandbox because it runs Python 3.12 instead of the pinned 3.11, has no `pip-compile`, and is not a git checkout. They run in CI.

## Test to criterion map

| Draft test | Where it lives |
|---|---|
| T01 existing adapter allowlist | `test_ac01_adapter_command_set_matches_policy` and `test_ac03_adapter_presses_only_the_documented_key`, plus the existing adapter tests, reused and untouched |
| T02 negative commands | `test_ac02_adapter_rejects_bad_commands_with_zero_keyboard_calls` |
| T03 controller and profile mapping | `test_ac05_*` and `test_controller_ignores_unbound_and_non_gesture_events_with_zero_calls` |
| T04 session lifecycle matrix | `test_ac04_*` |
| T05 validation across controller and two other layers | Not done here. Belongs to S4-R01-T2, since no profile loading layer exists yet |
| T06 CI and independent review | Pending |

Gap G4, the end to end boundary, is covered by `test_ac03_gesture_to_key_end_to_end`, which runs a real recognition event through the coordinator, controller and real keyboard adapter to the fake keyboard library.

## Remediation status

Findings F1 to F3 were fixed. F4 and F7 are residual. F6 is handed to Eric. See `S4-SOC2-C01-T3-Remediation-Log.md`.

## Residual risk

| Risk | Why it remains | Owner |
|---|---|---|
| Window focus, G5 | An approved key can still land in the wrong window. Allowlisting does not address it | Eric |
| Controller called without the coordinator, F4 | The session gate lives in the coordinator only | Joon, revisit if more callers appear |
| Helper has no caller authentication | Loopback bind and POST only. See the CC6.6 assessment | Eric |
| Gesture id registry | Only the shape of an id is checked | Diego |

## Still needed to close AC-06

1. Push the branch and open a pull request. The patch is in `control01.patch`.
2. Get one independent reviewer. The Sprint 3 test change and the end decision are the parts worth a second look.
3. Paste the GitHub Actions run URL for the unit test, integration and security steps here.
4. Record the commit hash in place of the file hashes.
5. Move SCRUM-170 to SCRUM-173 forward in Jira. This session had read only access, so no ticket was changed.
