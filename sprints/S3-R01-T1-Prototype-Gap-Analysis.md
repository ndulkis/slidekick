# S3-R01-T1 — Prototype Gap Analysis

**Snapshot:** `slidekick-develop (3).zip` · **Prepared:** October 15, 2026 · **Demo:** October 22, 2026  
**Scope:** repository evidence, not a formal rubric evaluation. **Official midterm rubric unavailable.**

## Goals and use-case coverage

| Goal/use case | Repository evidence | Assessment |
|---|---|---|
| UC10 start session | `src/slidekick/session_controller.py`, `docs/session-state-model.md` | Implemented state transition; now invoked by Python camera runner. |
| UC6 pause recognition | `session_controller.py`, `session_coordinator.py` | Implemented command gating; camera remains on, recognition still computes. |
| UC7 resume recognition | same | Implemented command gating. |
| UC8 finalize session | same | RUNNING → ENDED implemented; PAUSED → ENDED remains deliberately invalid. |
| UC1/UC2 swipe navigation | `recognition/camera.py`, `recognition/swipe_recognizer.py`, `gesture_command_controller.py`, `presentation_adapter.py` | Right/left swipe mapped to next/previous while RUNNING; real slideshow not tested here. |
| UC3 numeric slide jump | `gesture_command_controller.py` default bindings | Not implemented; no numeric binding or jump adapter operation. |
| Presentation feedback | `frontend/src/pages/SessionPage.tsx` | Simulated only; browser-to-Python transport does not exist. |
| Gesture recognition quality | `sprints/S2-R03-T3-Sample-Analysis.md` | 32/36 correct (88.9%); 2/12 negative trials false positive (16.7%). Small sample, not acceptance proof. |

## Prioritized gaps and decisions

| Priority | Gap / risk | Evidence | Owner/component | Next action / disposition |
|---|---|---|---|---|
| P0 | Session not authoritative over presentation commands | Original `scripts/run_gesture_control.py` called gesture controller directly | Python integration / R01 | **Addressed in T2:** `SessionCoordinator` gates commands and runner uses it. Verify live. |
| P0 / rubric-dependent | UI not connected to backend | `SessionPage.tsx` has simulation controls; no transport | Frontend + backend owners | Keep clearly labeled simulated; agree whether live UI is required by rubric. |
| P1 | No pause/resume command gating | Original runner lacked lifecycle integration | Python integration / R01 | **Addressed in T2**; tests for paused, resumed and ended. |
| P1 | Numeric slide jump absent | `gesture_command_controller.py`, `presentation_adapter.py` | Recognition + adapter owners | Defer unless rubric requires it; design gesture/command contract first. |
| P1 | Recognition false positives and missed left swipes | `sprints/S2-R03-T3-Sample-Analysis.md` | Recognition owner | Run more negative trials; evaluate tuning without assuming improvements. |
| P1 | Camera and slide-control failures | `recognition/camera.py`, adapter execution | Camera + integration owners | **Partially addressed in T2:** camera open/read failure reported and resources released; command errors surfaced. Live recovery unverified. |
| P1 | Slideshow focus not discoverable | keyboard adapter sends keys to focused app | Integration + demo operator | Rehearse focus and manual fallback. |
| P2 | Docs outdated about integration/Python prerequisite | `README.md`, `docs/build.md`, `.python-version` | Documentation | Update quick-start, avoid contradictory version claims. |
| P2 | Full-stack build not established on all machines | `scripts/verify.sh`, `frontend/package.json` | Platform + frontend | Run `npm --prefix frontend ci`, check exact locked tool versions and CI. |

## Evidence and measurement caveats

The Sprint 2 analysis contains **36** evaluation trials, including **12** `no_gesture` trials. Its reported estimated mean motion-to-detection delay of **253 ms** is **heuristic**, not measured end-to-end gesture-to-slide latency. Do not present it as verified command latency. Current isolated Python tests exercise mocked adapters, not webcam or presentation focus.

## Readiness / open checks

**Code integration:** implemented with automated mock-based tests. **Live reliability:** not verified. **Frontend:** simulation; no backend feed. **Rubric alignment:** pending receipt of official midterm grading criteria. Confirm responsible teammate assignments, sample dataset acceptance threshold, demo machine Python/Node installation, camera permissions, slideshow focus, and recovery rehearsal results before October 22.

**Blocking communications to send:** (1) decide live-connected UI requirement, (2) agree numeric jump scope, (3) request rubric, (4) schedule live demo rehearsal. These are recommendations, not evidence that messages were sent.
