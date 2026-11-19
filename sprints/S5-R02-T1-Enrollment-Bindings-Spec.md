# S5-R02-T1 Gesture Enrollment and Binding UI Specification

## Purpose

Define the screens, states, API contracts, ownership, and test plan for custom
gesture enrollment and gesture-to-command binding in Sprint 5.

This supports S5-R02-T1 / SCRUM-93 and defines what SCRUM-94 builds and
SCRUM-95 tests.

## Current state (updated November 18)

| Piece | Status | Where |
|---|---|---|
| Binding validation | Done | `command_policy.py` (R01): only next, previous, pause, resume are bindable; "end" is not |
| Runtime binding change | Done, not used yet | `GestureCommandController.set_gesture_bindings()` |
| Default bindings | Done | `swipe_right` → next, `swipe_left` → previous |
| Enrollment capture | Done as a module, no endpoint | `gesture_enrollment.py` (R04): 8 guided stages, 8 samples each, JPEG + manifest |
| Training | Client only | `training_job_client.py` (R04, branch `feature/s5-training-job-client`) calls an ML service on port 5005 (R03) |
| Frontend ↔ backend | Done (PR #64) | `api_server.py` (Nathan): Flask on 127.0.0.1:5001, `/api/session`, `/api/calibration`, `/api/cameras`, Vite `/api` proxy |
| Camera in the web app | Done (PR #65) | `/api/camera` streams the backend's camera as MJPEG |

## What is live vs. mocked in Sprint 5

| Feature | Sprint 5 |
|---|---|
| Gesture bindings: view, change, save, reset, applied to recognition | **Live** |
| Enrollment screens and states | **Specified here; carried into Sprint 6** until R04/R03 endpoints exist |
| Training progress and results | **Carried into Sprint 6** until the ML service is available |

## 1. Gesture bindings

### Screen

A "Gesture Bindings" section on the Settings page, below Gesture Calibration.

- One row per gesture: the gesture name and a command selector.
- The selector offers only the bindable commands from the backend (next,
  previous, pause, resume). "End" is never offered.
- Save bindings and Reset to defaults buttons.
- A short note that "End session" stays a button, not a gesture, by design.

### States

| State | What the user sees |
|---|---|
| Loading | "Loading gesture bindings…" |
| Loaded | Current bindings in the selectors |
| Offline | "Can't reach SlideKick" note; selectors disabled |
| Saved | "Gesture bindings saved." (`role="status"`) |
| Invalid | The policy's error message (`role="alert"`); previous bindings stay active |
| Reset | Defaults shown; "Gesture bindings reset to defaults." (`role="status"`) |

### API contract (added to Nathan's `api_server.py`)

| Method and path | Body | Response |
|---|---|---|
| `GET /api/bindings` | — | `200 {bindings, bindable_commands, gestures}` |
| `PUT /api/bindings` | `{bindings: {gesture: command}}` | `200 {bindings}` or `400 {error}` with the policy's message; nothing saved on error |
| `POST /api/bindings/reset` | `{}` | `200 {bindings}` (the defaults) |

- `gestures` lists the gesture IDs recognition can produce (owner: R03).
- Saved bindings are applied right away through `set_gesture_bindings()`, the
  same way calibration applies while the camera runs.
- Writes require JSON, like the existing endpoints, so the existing
  host check and JSON rule protect them.

### Saved profile

`data/gesture_bindings.json`, loaded at startup:

```json
{
  "version": 1,
  "profile_id": "default",
  "bindings": { "swipe_right": "next", "swipe_left": "previous" }
}
```

If the file is missing or fails validation, SlideKick uses the defaults and
logs a warning.

## 2. Custom gesture enrollment

### Flow

1. **Name the gesture.** Lowercase letters, digits, and underscores, starting
   with a letter (same rule as `command_policy`'s gesture IDs). Error shown
   inline if invalid or already used.
2. **Guided capture.** 8 stages in order: neutral, slight left tilt, slight
   right tilt, closer, farther, reposition, reform, final confirmation.
   Each stage shows its instruction and progress (n of 8 samples), plus
   overall progress (n of 64).
3. **Review.** Summary of captured samples; Submit for training or Cancel.
4. **Training.** Status follows the training client: queued → validating →
   preparing → training → ready.
5. **Result.** Success: "Gesture ready" with a link to bind it. Failure: a
   plain reason and Retry or Cancel.
6. **Bind.** The new gesture appears in Gesture Bindings.

Cancel is available at every step and returns to the start with nothing
activated.

### States and messages

| State | Message | Announce |
|---|---|---|
| Collecting | "Stage 3 of 8: slight right tilt. Hold your hand in view." | status |
| Sample rejected | "That sample couldn't be saved. Try again." | alert |
| Training | "Training your gesture…" with the current step | status |
| Training failed | Reason from the service, plus Retry | alert |
| Cancelled | "Enrollment cancelled. Nothing was saved." | status |
| Offline | "Can't reach SlideKick" | alert |

### API needs from R04 (proposal to agree)

| Method and path | Purpose | Backed by |
|---|---|---|
| `POST /api/enrollment` | Start: `{gesture_name}` → `{enrollment_id, stages}` | `EnrollmentSession()` |
| `POST /api/enrollment/{id}/capture` | Capture one sample for a stage | `add_sample()` |
| `GET /api/enrollment/{id}` | Progress and status | session status |
| `POST /api/enrollment/{id}/complete` | Finish and write the manifest | `complete_session()` |
| `POST /api/enrollment/{id}/cancel` | Cancel | `cancel_session()` |
| `POST /api/training` and `GET /api/training/{job_id}` | Start and poll training | `TrainingJobClient` |

### Open question: who captures the frames?

`add_sample()` expects a base64 image "from the frontend", but the Python
camera loop already holds the webcam, and on Windows only one program can use
it at a time. Two options:

- **A (recommended):** the backend captures the frame from its own camera loop
  when the UI asks (`/capture`), so the browser never opens the camera. The
  backend already shares its frames with the browser through `/api/camera`,
  so this fits the existing design.
- **B:** the camera loop pauses and releases the webcam during enrollment, and
  the browser captures frames.

Needs a decision with R04 and Nathan before the capture endpoint is built.

## 3. Ownership

| Piece | Owner |
|---|---|
| Binding endpoints, saved profile, startup loading (SCRUM-94 backend fix) | R02 (Andres), reviewed by R01 (Joon) for policy use |
| Gesture Bindings and enrollment UI | R02 (Andres) |
| `api_server.py` and the frontend–backend connection | Nathan (SCRUM-174) |
| Enrollment and training endpoints | R04 (Eric) |
| ML training service and the gesture list | R03 (Diego) |
| Command policy | R01 (Joon) |

Nathan's API is merged, so the binding endpoints are added to `api_server.py`
next to the calibration endpoints and follow the same pattern.

**Sprint 5 scope:** gesture bindings are built and connected end to end.
Enrollment screens depend on R04 endpoints that don't exist yet and are carried
into Sprint 6.

## 4. Usability and accessibility test plan (run in SCRUM-95)

| ID | Task | Expected |
|---|---|---|
| TC-B01 | Open Settings and find Gesture Bindings | Current bindings shown |
| TC-B02 | Change swipe right to Previous and save | "Gesture bindings saved." announced |
| TC-B03 | Swipe right during a slideshow | Slide goes back |
| TC-B04 | Reset to defaults | Swipe right → next again |
| TC-B05 | Use only the keyboard | Selectors and buttons reachable and usable; focus visible |
| TC-B06 | Backend not running | Offline note; nothing can be saved |
| TC-E01 | Start enrollment with an invalid name | Inline error; can't continue |
| TC-E02 | Complete all 8 capture stages | Progress updates per stage |
| TC-E03 | Cancel during capture | "Nothing was saved." |
| TC-E04 | Training fails | Reason shown with Retry |
| TC-E05 | Use the enrollment flow with only the keyboard | Every step reachable; focus visible |

Accessibility checks for both: labels on every control, status messages via
`role="status"`, errors via `role="alert"`, no color-only states, visible focus.

## 5. Frontend integration checklist

- [x] Nathan's integration branch merged into develop (PR #64)
- [ ] Binding endpoints added and tested (pytest)
- [ ] Gesture Bindings section connected and tested (Vitest)
- [ ] Enrollment endpoints agreed with R04 (or mocks documented)
- [ ] Capture approach (A or B) decided
- [ ] Gesture list source agreed with R03
