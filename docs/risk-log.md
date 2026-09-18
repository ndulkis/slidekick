# Sprint 1 Risk Log

| ID | Risk | Impact | Likelihood | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-01 | Recognition is a placeholder, not a real model | High | High | Keep the recognition contract stable so a real model can drop in without touching the controller or UI | R01/ML | Open |
| R-02 | UI-to-Python transport is undefined | High | High | Hold the boundary at typed events for now and validate controller and adapter logic independently until transport is scoped | R01/Backend | Open |
| R-03 | Keyboard automation behaves differently across operating systems | Medium | Medium | Keep the adapter abstracted behind `PresentationAdapter` and document that current testing is host-only | R01/QA | Open |
| R-04 | Scope creep past the MVP boundary | Medium | Medium | Defer camera capture, model training, and extra adapters until the contract is formally approved | PM | Monitoring |

## Risk Details

### R-01: Recognition is a placeholder, not a real model

- **Description:** The recognition layer currently returns deterministic placeholder gestures instead of running actual inference. Nothing in Sprint 1 proves the system can recognize a real gesture from camera input.
- **Impact:** Any confidence in gesture accuracy is unearned until a real model is wired in. Downstream layers (controller, adapter) are only validated against clean, predictable input.
- **Mitigation:** Keep `RecognitionEvent` (gesture, confidence, source) as the fixed contract so a real model can be swapped in later without changes to the controller or UI.
- **Contingency:** If model integration slips, the placeholder keeps the vertical slice demoable and the contract intact for a later sprint.
- **Owner:** R01/ML
- **Status:** Open

### R-02: UI-to-Python transport is undefined

- **Description:** The React UI currently calls a local placeholder function directly. There is no defined transport for the browser to actually reach the Python controller and adapter.
- **Impact:** The full stack (UI through recognition through controller through adapter) has not been proven end to end. Integration risk shifts to whichever sprint picks up transport.
- **Mitigation:** Treat this as an explicit deferral rather than an oversight. Controller and adapter logic are tested in isolation so they're ready once transport is added.
- **Contingency:** If transport isn't scoped in time for a later sprint, the browser-only demo still stands as evidence the contract logic works.
- **Owner:** R01/Backend
- **Status:** Open

### R-03: Keyboard automation behaves differently across operating systems

- **Description:** `KeyboardPresentationAdapter` uses `pyautogui` to send keystrokes. Key simulation and focus behavior can vary between Windows, macOS, and Linux.
- **Impact:** A reviewer or grader on a different OS than the one used for development could see the adapter fail or behave inconsistently.
- **Mitigation:** Keep the adapter behind the `PresentationAdapter` interface so the rest of the system doesn't depend on OS-specific behavior, and note in setup docs that testing has only been done on one host OS.
- **Contingency:** If cross-OS failure comes up during review, it's a known limitation with a documented workaround, not a broken contract.
- **Owner:** R01/QA
- **Status:** Open

### R-04: Scope creep past the MVP boundary

- **Description:** It would be easy to start pulling in camera capture, real ML inference, or additional presentation adapters before the current contract is even approved.
- **Impact:** Time spent on out-of-scope work delays the vertical slice and risks missing the Sept 17 deadline for a working, reviewable path.
- **Mitigation:** Hold the line at the MVP scope defined in the architecture decision note: UI shell, placeholder recognition, controller mapping, and keyboard adapter only.
- **Contingency:** Anything beyond that boundary gets logged as a future task instead of pulled into Sprint 1.
- **Owner:** PM
- **Status:** Monitoring
