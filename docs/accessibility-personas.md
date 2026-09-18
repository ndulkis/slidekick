# Accessibility Personas

This document defines the accessibility personas and related requirements for
the SlideKick frontend. It is based on the research/design work from SCRUM-75
and informs the UI states defined in `docs/ui-states.md`.

These personas are used to identify accessibility needs that should be
considered as the SlideKick interface grows. They are not intended to represent
every possible user.

## Student presenter

A student may use SlideKick while presenting a class project.

Needs:

- Quick setup
- Clear indication that SlideKick is ready
- Clear indication that gesture recognition is active
- Immediate feedback after a gesture
- Simple pause and resume controls
- Errors that explain what to do next

Possible problems:

- The presenter may be rushed during setup
- The presenter may forget whether recognition is Active or Paused
- Accidental movement could be mistaken for a gesture
- The presenter may not understand why a gesture did not trigger an action

## Low-vision user

A user may have difficulty reading small text or distinguishing interface
elements with low contrast.

Needs:

- Readable text
- Sufficient contrast
- Visible keyboard focus
- Status labels in addition to color
- Clear separation between important interface regions

The cyberpunk visual style should not reduce readability. Neon effects,
background effects, or low-contrast text should not be more important than
communicating system state.

## User with color-vision differences

A user may not reliably distinguish status colors such as red, green, or
yellow.

Needs:

- Text labels for important states
- Icons or other indicators in addition to color
- Error messages that explicitly identify the problem
- Active and Paused states that remain distinguishable without color

For example, displaying only a green circle for Ready and a red circle for
Error would not be enough.

## Motor-impaired user

A user may not be able to perform every supported gesture consistently or may
have difficulty using precise mouse interactions.

This persona is especially important on the Session page because gesture
control is SlideKick's main feature.

Needs:

- Keyboard and mouse alternatives for important actions
- Ability to pause or resume gesture recognition without performing another
  gesture
- Large and clear controls
- Feedback showing whether a gesture was accepted
- Calibration or settings that can help accommodate different gesture
  performance

Gesture input should enhance presentation control without becoming the only way
to operate important SlideKick controls.

## Keyboard-only user

A user may navigate the application without using a mouse.

Needs:

- Logical Tab order
- Every important interactive control reachable by keyboard
- Visible focus indication
- Standard keyboard behavior
- Clear current-page indication

The current SCRUM-76 shell already supports keyboard navigation through the
Dashboard, Session, and Settings navigation links. Detailed findings are in
`docs/keyboard-nav-testing.md`.

Keyboard testing will need to be repeated once the Session page contains real
buttons and controls.

## Onboarding and calibration needs

SlideKick should not assume that a first-time user already knows whether the
camera, recognition system, and presentation connection are working.

Before beginning a session, the interface should eventually help the user
confirm:

1. The camera is available.
2. Gesture recognition is ready.
3. The presentation connection is ready.
4. The user understands which gestures are currently available.
5. The user knows how to pause or stop gesture control.

Calibration may also need to explain whether the user's hand is visible and
whether gestures are being recognized reliably.

The exact calibration process depends on the recognition system and has not
been implemented yet.

## UX acceptance criteria

The following criteria should guide implementation of the Session interface:

- A user can determine whether the session is Ready, Active, Paused, or in an
  Error state from visible interface text.
- Important states do not rely only on color.
- Active clearly communicates that gestures can trigger presentation actions.
- Paused clearly communicates that gestures will not trigger presentation
  actions.
- Recognized gestures produce visible feedback.
- Gesture feedback identifies the detected gesture or resulting action.
- Error states explain the problem in user-facing language.
- Recoverable errors provide a next action when possible.
- Important session controls are reachable without requiring a gesture.
- Keyboard focus remains visible on interactive controls.
- Navigation order follows the visible interface order.
- Cyberpunk styling does not make status information difficult to read.
- The interface handles missing camera, recognition, or presentation state
  without displaying an unexplained blank screen.

## Accessibility checklist

### Visual

- [ ] Important states do not rely only on color.
- [ ] Ready, Active, Paused, and Error use visible text labels.
- [ ] Text remains readable against the selected background.
- [ ] Important information uses an appropriate text size.
- [ ] Icons are paired with text when the icon alone may be unclear.
- [ ] Cyberpunk visual effects do not reduce readability.
- [ ] Flashing effects are avoided.

### Keyboard and focus

- [x] Main navigation can currently be reached using Tab.
- [x] Current navigation links show visible keyboard focus.
- [x] Enter activates the current navigation link.
- [ ] Future Session controls can be reached using the keyboard.
- [ ] Start, Pause, Resume, and End controls have visible focus.
- [ ] Focus order remains logical as new controls are added.
- [ ] Skip-to-content behavior is reconsidered as page content grows.

### Interaction

- [ ] User can pause gesture control without performing a gesture.
- [ ] User can resume gesture control without performing a gesture.
- [ ] Recognized gestures produce visible feedback.
- [ ] Presentation actions produce understandable feedback.
- [ ] No-gesture behavior is treated as normal rather than an error.
- [ ] Errors provide a recovery action when possible.

### Session page

- [ ] Camera status is visible.
- [ ] Recognition status is visible.
- [ ] Presentation connection status is visible.
- [ ] Active and Paused are clearly distinguishable.
- [ ] Gesture feedback does not hide important controls.
- [ ] Important session actions have keyboard or mouse alternatives.
