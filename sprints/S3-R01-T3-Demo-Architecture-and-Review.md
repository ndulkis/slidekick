# S3-R01-T3 — Architecture, Review, and Demo Recovery

**Prepared:** October 15, 2026 · **Target demonstration:** October 22, 2026  
**Status:** narrative and scripts prepared; peer reviews, commit attribution and live rehearsal pending.

## 1. Architecture narrative

The existing Observer Pattern is represented by `SessionController.events` and session state event publishing (`src/slidekick/observer.py`, `contracts.py`). The Python demo path uses a direct recognition callback (rather than dispatching camera events through that observer system):

```text
Camera / MediaPipe / swipe recognizer
  -> gesture or landmark event dictionary
  -> SessionCoordinator (SessionController state gate)
      -> GestureCommandController (gesture-to-command mapping)
          -> KeyboardPresentationAdapter (native keypress)
              -> focused presentation app

SessionController (Observer event publisher) -> session lifecycle observers
React SessionPage -> local simulated controls ONLY (no network transport)
```

`RUNNING` accepts known swipes; `PAUSED`, `IDLE` and `ENDED` reject commands. Lifecycle pause never blanks the slide. Unknown events produce no slide action. The camera continues tracking while paused, and a real slideshow must have focus to receive native keys.

## 2. Contribution verification (complete from Git/Jira evidence)

ZIP snapshot has no `.git` history. **Do not claim author identity, merged PRs or reviews from file presence alone.**

| Work item | Reviewable local artifact | Commit / PR / Jira evidence |
|---|---|---|
| S3-R01-T1 | `sprints/S3-R01-T1-Prototype-Gap-Analysis.md` | **Pending:** add issue and merged commit links. |
| S3-R01-T2 | `src/slidekick/session_coordinator.py`, `scripts/run_gesture_control.py`, `src/slidekick/recognition/camera.py`, new tests, integration document | **Pending:** add author, commit SHA, review URL. |
| S3-R01-T3 | this document; actual rehearsal log below | **Pending:** add reviewer and rehearsal evidence. |

## 3. Peer review record (to fill during review)

| Reviewer/date | Files checked | Findings | Resolution / PR link |
|---|---|---|---|
| **Not yet performed** | Coordinator, runner, camera, tests | Check lifecycle semantics, camera resource release, backend/UI simulation disclaimer, keyboard focus and API compatibility. | **Pending review**, not approved. |

Review prompts: does `RUNNING` alone permit actions; does PAUSED avoid sending `B`; is PAUSED → ENDED correctly rejected; do camera failures safely release capture; are fake adapters and event contracts representative; is the camera focus workflow viable; does web UI clearly remain simulated?

## 4. Demo script and recovery

**Setup:** activate Python environment, ensure requirements and camera model are installed, open slideshow, set focus. Run `PYTHONPATH=src python -m pytest -q tests/unit/test_session_coordinator.py tests/unit/test_demo_runner.py` and then `PYTHONPATH=src python scripts/run_gesture_control.py`.

| Sequence | Operator action | Expected visible evidence |
|---|---|---|
| 1 | Start runner | Terminal prints RUNNING, camera preview opens. |
| 2 | Refocus slideshow, swipe right | Next slide. |
| 3 | Swipe left | Previous slide. |
| 4 | Focus camera, press P; refocus slideshow, swipe | Terminal PAUSED, **no slide change**. |
| 5 | Focus camera, press R; refocus slideshow, swipe | Terminal RUNNING, slide changes again. |
| 6 | Focus camera, press E; swipe | ENDED, no gesture command. |
| 7 | Press S, refocus slideshow and swipe | RUNNING again, commands allowed. |
| 8 | Focus camera, press Q | Runner exits, session ends; slide deck stays open. |
| 9 | Open React Session page, if desired | Explicitly identify demo controls as simulated, not synchronized. |

**Recovery plan (proposed, not yet rehearsed):**

| Failure | Recovery step | Rehearsal result |
|---|---|---|
| Camera cannot open or disconnects | Check OS permission / camera device; stop and relaunch runner. | **Not performed** |
| Slides do not advance | Click slideshow to restore focus; retry with swipe; use keyboard/manual fallback. | **Not performed** |
| False-positive / missed gesture | Better lighting, move hand in view, retry carefully; use manual controls if needed. | **Not performed** |
| Session state confusion | In camera window: R if PAUSED, E if RUNNING, S if ENDED; otherwise quit/restart. | **Not performed** |
| Presenter becomes unresponsive | Quit camera window and control slides manually; reopen deck as needed. | **Not performed** |

## Readiness sign-off

- [x] Architectural boundaries explained and actual simulated UI disclosed.
- [x] Test suite includes mock-based lifecycle gating/error scenarios.
- [ ] Run tests on exact demo machine and log outputs.
- [ ] Inspect actual camera/slide behavior and rehearse at least one recovery, record date/result.
- [ ] Attach authentic Git commits, reviewer details, and PR links.
- [ ] Confirm official rubric, frontend scope, and team demo roles.
- [ ] Obtain team sign-off before October 22.

**Current assessment:** mock-based integration exists; hardware, cross-platform behavior, live recovery and rubric compliance **not verified**.
