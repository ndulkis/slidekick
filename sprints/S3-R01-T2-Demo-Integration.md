# S3-R01-T2 — Demo Integration

**Prepared:** October 15, 2026 · **Status:** code implemented; webcam/presentation app integration not yet verified live.

## Integration architecture

`run_camera()` → emitted gesture/landmark dictionary → `SessionCoordinator.handle_event()` → (`SessionState.RUNNING` required) → `GestureCommandController` → `KeyboardPresentationAdapter` → key press in focused slideshow.

- `src/slidekick/session_coordinator.py` composes the existing session state machine and gesture controller; it does not reimplement recognition or the adapter.
- `scripts/run_gesture_control.py` creates and starts the session, prints lifecycle feedback, receives camera keys, and surfaces presentation errors.
- `src/slidekick/recognition/camera.py` accepts optional `key_handler` while maintaining compatibility with the original single-argument call; failure to open/read camera raises an error and resource cleanup occurs in `finally` for recognition-loop failures.
- `frontend/src/pages/SessionPage.tsx` is a **simulation**, not connected to the Python coordinator.

## Lifecycle and control rules

| State | Swipe command? | Action |
|---|---|---|
| IDLE | No | S starts session (runner starts automatically). |
| RUNNING | Yes | P pauses; E ends. |
| PAUSED | No | R resumes; E displays instruction to resume first. |
| ENDED | No | S restarts; Q quits camera window. |

`pause()` / `resume()` mean **recognition command gating**. Neither sends the `B` keystroke used by `PresentationAdapter.pause_presentation()` / `resume_presentation()` to blank/unblank slides. Session end does not send ESC; the operator keeps manual control of the slideshow. Camera continues to process frames during PAUSED (events are discarded by the coordinator). Q or closing the camera window exits the runner, safely finalizing RUNNING sessions. The current approved model does not allow ending directly from PAUSED.

## Reproducible demonstration

Run from the repository root, with its Python environment active:

```bash
export PYTHONPATH=src
python -m pytest -q tests/unit/test_session_coordinator.py tests/unit/test_demo_runner.py
python scripts/run_gesture_control.py
```

On the actual demo machine, allow camera permissions and open a slideshow. **Focus the slideshow before issuing swipes**; clicking the camera preview to type P/R/E can steal focus. Refocus the slideshow before testing swipes. The camera window handles P/R/E/S when it has focus; Q closes it. Present right swipe (next), left swipe (previous), pause (no slide change), resume (commands return), end (commands disabled), optional restart (commands return), Q (cleanup). The camera's Space key still arms existing Sprint 2 evaluation sampling; avoid it during the demo unless recording is intended.

## Failures and feedback

- Camera cannot open: runtime error and nonzero runner exit; check permissions and device access. Prolonged frame-read failure: runtime error and camera release/GUI teardown. Camera model load errors may propagate; check `models/gesture_recognizer.task` if startup fails.
- Adapter raises or returns `False`: `PresentationCommandError` with `last_error` available for observers; runner prints an actionable error and can keep processing. A successful command clears the error.
- Non-gesture, unknown, and malformed recognition events: ignored without key presses.
- Invalid session transition: the existing `InvalidTransitionError` remains authoritative; interactive E while paused explains required R first.
- Focus loss: manual refocus/retry. A successful pyautogui key invocation **cannot prove** the slideshow advanced.

## Verification evidence

`tests/unit/test_session_coordinator.py` and `tests/unit/test_demo_runner.py` cover lifecycle gating, invalid transitions, mapped swipes, unexpected events, exceptions, failure returns, and camera-window key actions with fake adapters. Execute broader tests per `scripts/verify.sh`; platform environment tests and real hardware remain separate checks. No API server or bidirectional React connection was added.

## Ownership and follow-up

Integration: `session_coordinator.py`, runner, camera callback handling. Recognition owner to verify event emission and quality; frontend owner to decide if a transport mechanism is required; adapter owner to verify target slideshow and native errors. Do not claim live camera or browser connectivity until demonstrated and measured.
