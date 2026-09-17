# UI States

States the dashboard needs to support, based on the shell built in SCRUM-76.

## Loading

Not built yet. Right now every page renders instantly since there's no real
data or camera feed being pulled in. Once the Session page talks to the
gesture recognition backend, it needs a loading state while the camera/model
starts up (spinner or skeleton, plus a message like "Starting camera...").

## Empty

Not built yet. Dashboard page will need an empty state for when there are no
past sessions yet ("No sessions yet — start a presentation to see it here").

## Error

Not built yet. Needs a state for when the camera can't be accessed, or the
gesture recognition backend isn't reachable. Should show a plain error
message and a retry option, not just a blank page or a console error.

## Active / gesture-detected

Not built yet. This is the main state for the Session page — camera feed
visible, current detected gesture shown, and slide controls responding to
gestures in real time.

## Navigation states

These exist already in the shell:

- Default: nav link not on the current page, plain text link.
- Active: nav link for the current page, underlined/highlighted (see
  `frontend/src/layout/Layout.css`, `.app-nav-link.active`).
- Focused: nav link focused via keyboard, shows the browser's default focus
  ring (see `docs/keyboard-nav-testing.md`).

## Accessibility personas

People the UI states above need to work for:

- **Low-vision users** — need enough color contrast and focus indicators
  that don't rely on color alone (the active nav state currently uses an
  underline plus color, not color alone, which is good).
- **Motor-impaired users** — need to be able to do everything with keyboard
  only, no drag gestures or precise mouse clicks required for basic
  navigation. Relevant since gesture control is the main feature but not
  everyone can use gestures reliably, so keyboard/mouse fallback for the
  dashboard itself matters.
- **Keyboard-only users** — same as above, tab order needs to make sense and
  every interactive element needs to be reachable and show visible focus.

This list is a starting point, not final — SCRUM-75 was meant to do a
deeper pass on this before SCRUM-76/77 started, but the shell got built
first since it was blocking SCRUM-77. Worth a follow-up ticket to expand
this properly once there's a UI with real states to test against.
