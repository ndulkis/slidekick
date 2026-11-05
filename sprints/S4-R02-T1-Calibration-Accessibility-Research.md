# S4-R02-T1 Accessible Calibration and Error Message Research

## Purpose

Research how SlideKick's gesture calibration and error messages should work so
they're usable by the people in `docs/accessibility-personas.md`. The findings
define what SCRUM-87 builds (calibration and profile UI) and what SCRUM-89
tests.

This supports S4-R02-T1 / SCRUM-86. It fills in the "Onboarding and
calibration needs" section of the personas doc, which noted that the
calibration process hadn't been designed yet.

## Who needs calibration

From `docs/accessibility-personas.md`:

| Persona | Calibration need |
|---|---|
| Motor-impaired user | Swipes may be shorter, slower, or less steady than the defaults expect. Needs adjustable thresholds and a non-gesture way to do everything. |
| Keyboard-only user | Every calibration control must work with the keyboard, with visible focus. |
| Low-vision user | Readable values and messages, not just a slider position or color. |
| User with color-vision differences | Errors and "too strict / too loose" feedback can't rely on red/green alone. |
| Student presenter | Quick setup with sensible defaults and an easy way to undo changes before presenting. |

## Findings

### 1. Gesture input needs a non-gesture alternative and an off switch

WCAG 2.5.4 Motion Actuation (Level A) applies to "explicit eye, face, or hand
gestures to a camera". Anything a gesture does must also be possible with
normal controls, and the user must be able to turn off the motion response to
prevent accidental actions.

SlideKick already meets this on the Session page (Start/Pause/Resume/End
buttons, Sprint 3). Calibration should keep it that way: calibrating must
never be required to use the app.

### 2. Accessibility tools expose sensitivity as plain settings

Apple's Mac accessibility settings, which Apple notes are useful with head or
eye tracking, let people adjust dwell time (how long before an action runs)
and pointer reaction time. The pattern: a few clearly named settings with safe
defaults, not raw recognition values.

For SlideKick, that means labels like "How far to swipe", not
`min_displacement = 0.10`.

### 3. Calibration needs a live check, not just settings

Ultraleap's hand-tracking setup recommends a visualizer to confirm tracking
works before use, and gives placement guidance for the camera. The useful
pattern for SlideKick is "adjust, then try a gesture and see if it's
recognized" in the same place.

This needs the frontend connected to the recognition backend, which doesn't
exist yet (see Limitations).

### 4. Sliders must be keyboard-accessible and announce readable values

The WAI-ARIA slider pattern uses arrow keys to change the value and
`aria-valuetext` when the raw number isn't meaningful (e.g. "Medium (0.20)"
instead of "0.2"). The native `<input type="range">` has built-in keyboard
support, and MDN notes `aria-valuetext` can be added to it.

### 5. Errors must say what's wrong and how to fix it, in text

- WCAG 3.3.1 Error Identification (Level A): errors are described in text.
- WCAG 3.3.3 Error Suggestion (Level AA): if a fix is known, suggest it.
- WCAG 4.1.3 Status Messages (Level AA): messages like "Settings saved" must
  be announced by screen readers without moving focus (`role="status"`;
  urgent errors use `role="alert"`).

This matches the error approach already in `docs/ui-states.md` and the Sprint
3 Session page.

### 6. Camera errors are specific and need manual recovery

The browser camera API (`getUserMedia`) reports distinct errors. After a user
blocks the camera, the browser won't ask again, so the app has to explain how
to re-allow it in browser settings rather than retrying.

## Mapping backend calibration to user controls

The backend `GestureCalibration` class (`src/slidekick/recognition/
swipe_recognizer.py`) already defines and validates these settings. Proposed
user-facing controls:

| User control | Backend setting(s) | Default | Why a user changes it |
|---|---|---|---|
| Swipe distance | `min_displacement`, `ideal_displacement` | 0.10 / 0.20 of frame width | Limited range of motion |
| Swipe speed | `min_swipe_duration` to `max_swipe_duration` | 0.10–1.75 s | Slower or faster movement |
| Recognition strictness | `confidence_threshold` | 0.55 | Fewer accidental gestures (tremor) or fewer missed gestures |
| Time between gestures | `swipe_cooldown` | 1.5 s | Prevent double slide changes |

Direction consistency, axis purity, and the stationary re-arm settings stay at
defaults. They're harder to explain and not needed for the personas above.

The backend validates ordering (e.g. minimum distance must be below ideal
distance). The UI should only offer ranges that pass that validation, so users
can't create an invalid profile.

## Proposed error messages

| Situation | Message | Recovery | Announce as |
|---|---|---|---|
| Camera blocked (`NotAllowedError`) | Camera access is blocked. | Allow the camera in your browser's site settings, then reload. | alert |
| No camera (`NotFoundError`) | No camera was found. | Connect a camera and try again. | alert |
| Camera in use (`NotReadableError`) | The camera is being used by another app. | Close the other app, then try again. | alert |
| No hand detected | No hand detected. | Move your hand into view of the camera. | status |
| Gesture not recognized | Gesture not recognized. | Try a longer swipe, or lower Recognition strictness in Settings. | status |
| Setting out of range | Swipe distance must be between X and Y. | The value is reset to the nearest allowed value. | alert |
| Profile not saved | Your calibration couldn't be saved. | Try again. Your previous settings are still in use. | alert |

"No hand detected" and "gesture not recognized" are normal during use and
shouldn't use alert-level announcements (consistent with "No gesture detected"
in `docs/ui-states.md`).

## Profile

For Sprint 4, a profile is one saved set of the four calibration values above,
stored locally in the browser, with Reset to defaults.

Saving a profile in the frontend is not the same as applying it to
recognition. Until the frontend is connected to the backend, the UI must not
suggest the saved settings change how gestures are recognized.

## Recommendations for SCRUM-87

1. Add a "Gesture Calibration" section to the Settings page with the four
   controls above, using native range inputs with visible labels, current
   values, and `aria-valuetext`.
2. Save and load one local profile, with Reset to defaults.
3. Announce "Settings saved" / "Settings reset" with `role="status"`; show save
   failures with `role="alert"`.
4. Show a clear note that settings aren't applied to recognition yet (until
   the backend connection exists).
5. Keep calibration optional; nothing else in the app should depend on it.

For SCRUM-89 testing: keyboard-only use of every control, screen reader
announcements for values and save/reset, and the error messages above.

## Limitations

- No live "try a gesture" check is possible until the frontend is connected to
  the recognition backend. That connection is team work outside this ticket.
- Camera error messages can only be shown once the frontend accesses the
  camera; for now they define the wording for later.
- Default ranges for each slider should be confirmed with R03 (recognition)
  before SCRUM-87 sets them.

## Sources

- W3C, Understanding SC 2.5.4 Motion Actuation:
  https://www.w3.org/WAI/WCAG22/Understanding/motion-actuation.html
- W3C, Understanding SC 3.3.3 Error Suggestion:
  https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html
- W3C, Understanding SC 3.3.1 Error Identification:
  https://www.w3.org/WAI/WCAG20/Understanding/error-identification
- W3C, Understanding SC 4.1.3 Status Messages:
  https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html
- W3C ARIA Authoring Practices, Slider pattern:
  https://www.w3.org/WAI/ARIA/apg/patterns/slider/
- MDN, ARIA slider role:
  https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles/slider_role
- MDN, MediaDevices.getUserMedia() exceptions:
  https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
- Apple, Mac accessibility (Dwell options):
  https://support.apple.com/guide/mac-help/mchl654a7cc7
- Ultraleap, Testing hand tracking:
  https://docs.ultraleap.com/TouchFree/touchfree-user-manual/testing-hand-tracking.html
- Ultraleap, Camera placement:
  https://docs.ultraleap.com/TouchFree/touchfree-user-manual/camera-placement.html
