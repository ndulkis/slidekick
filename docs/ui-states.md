# UI States

This document defines the UI states for the SlideKick frontend. It is based
on the dashboard shell built in SCRUM-76 and the research/design work from
SCRUM-75.

The current frontend has three routes:

- Dashboard
- Session
- Settings

The Session page is the main gesture-control surface. This is where the user
needs the clearest feedback about camera status, gesture recognition, session
state, and presentation controls.

Accessibility personas and requirements that inform the states below live in
`docs/accessibility-personas.md`.

## Core session states

### Ready

The Ready state means SlideKick has completed enough setup for the user to
start a presentation session.

The Session page should eventually communicate:

- Camera availability
- Gesture recognition readiness
- Presentation connection status
- Whether the session can be started

Example:

> SlideKick Ready
>
> Camera: Ready
>
> Recognition: Ready
>
> Presentation: Connected

The user should have a clear action for starting the session.

The Ready state should not rely only on a green indicator. A text label or
other non-color indicator should also communicate the state.

### Active

The Active state means the presentation session is running and gestures can
trigger presentation actions.

The Session page should eventually show:

- Camera or camera status
- Recognition status
- Current detected gesture
- Presentation connection status
- Feedback for the presentation action
- A way to pause or end the session

Example:

> Gesture Recognition Is ON
>
> Swipe Right Detected
>
> Next Slide

Gesture feedback should be noticeable without taking over the interface or
making it difficult to follow the presentation.

### Paused

The Paused state means the session is still open, but gesture input should not
trigger presentation commands.

Example:

> Gesture Recognition Paused
>
> Gestures will not control your presentation.

The interface should provide a clear way to resume or end the session.

Paused needs to be visually and textually different from Active. A user should
not have to rely only on a color change to know whether gestures can currently
control the presentation.

### Error

The Error state means something required by the current workflow has failed.

Possible errors include:

- Camera unavailable
- Camera permission denied
- Gesture recognition backend unavailable
- Presentation disconnected
- Session startup failure

The UI should display a plain explanation of the problem instead of leaving the
page blank or requiring the user to check the developer console.

When possible, the error should also provide a recovery action.

Examples:

> Camera Not Available
>
> Check camera access and try again.
>
> Retry

or:

> Presentation Disconnected
>
> Reconnect the presentation before continuing.

Error information should not rely only on red coloring.

## Supporting states

### Loading

Loading is not implemented yet.

Right now the pages render immediately because there is no real camera or
recognition data being loaded.

Once the Session page communicates with the camera and gesture recognition
systems, the interface will need to show that startup work is happening.

Possible messages include:

> Starting camera...

> Starting gesture recognition...

A loading indicator should be accompanied by text so the user does not have to
interpret an animation by itself.

### Empty

Empty states are not implemented yet.

The Dashboard may eventually show previous sessions or other user data. If no
data exists, the page should explain why the area is empty instead of appearing
unfinished.

Example:

> No sessions yet.
>
> Start a presentation to see activity here.

### No Gesture Detected

During an Active session there may be long periods where no valid gesture is
being performed.

This should be treated as a normal state rather than an error.

The UI may display a quiet message such as:

> No Gesture Detected

The user should not receive repeated warnings simply because they are not
performing a gesture.

### Gesture Detected

When recognition reports a valid gesture, the interface should provide quick
feedback.

Example:

> Swipe Left Detected
>
> Previous Slide

The feedback should make it possible to understand both what SlideKick
recognized and what presentation action resulted from it.

## Navigation states

These already exist in the SCRUM-76 shell.

### Default

A navigation link that is not the current page appears as a normal text link.

### Active

The navigation link for the current page is visually marked using an underline
and color.

See:

`frontend/src/layout/Layout.css`

`.app-nav-link.active`

The underline is important because the active state does not depend only on
color.

### Focused

A navigation link reached using the keyboard displays the browser's default
focus outline.

The current keyboard behavior is documented in:

`docs/keyboard-nav-testing.md`

## Low-fidelity user flow

```text
Launch SlideKick
       |
       v
    Loading
       |
       v
Check camera, recognition, presentation
       |
       +------ Problem ------> Error
       |                        |
       |                    Retry / Setup
       |                        |
       +------------------------+
       |
       v
     Ready
       |
   Start Session
       |
       v
     Active
       |
       +---- Gesture Detected ----> Show Gesture/Action Feedback
       |                                  |
       |                                  v
       |                                Active
       |
       +---- Pause ----> Paused
       |                  |
       |                Resume
       |                  |
       +------------------+
       |
    End Session
       |
       v
     Ready
```
