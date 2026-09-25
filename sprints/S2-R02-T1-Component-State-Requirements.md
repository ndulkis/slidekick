# S2-R02-T1 Session Interface Component and State Requirements

## Purpose

Define the implementable component and state requirements for the SlideKick Session screen for Sprint 2.

This document does not redefine global UI states or accessibility personas. It references the existing project documentation:

- `docs/ui-states.md` for shared UI states such as Ready, Active, Paused, Error, Loading, Empty, No Gesture Detected, Gesture Detected
- `docs/accessibility-personas.md` for accessibility requirements and personas
- `docs/observer-event-contract.md` for the RecognitionEvent contract consumed by the Session UI

This work supports S2-R02-T1 / SCRUM-79 and prepares the component structure needed for SCRUM-80 implementation and SCRUM-81 component testing.

## Session Screen Responsibilities

The Session screen is the primary live-control surface for SlideKick.

It should provide:

- camera visibility or camera status
- current session status
- recognition feedback
- recognition confidence feedback as planned for Sprint 2
- current or most recent detected gesture/command
- pause/resume controls
- error/status feedback
- a clear indication of whether SlideKick is ready to accept gestures

The Session screen should consume recognition data through the existing RecognitionEvent contract rather than defining a separate recognition event format.

## Current RecognitionEvent Contract

As currently defined in `docs/observer-event-contract.md` and the implementation associated with PR #10, RecognitionEvent contains only a `gesture` field.

The current application-level gesture values are:

- `next`
- `previous`
- `end`

The documentation contract also includes `none` as a possible no-gesture value.

The current implementation shape is:

```python
class GestureType(str, Enum):
    NEXT = "next"
    PREVIOUS = "previous"
    END = "end"


@dataclass
class RecognitionEvent:
    gesture: GestureType
```

### RecognitionEvent Input

| Field | Current UI Use | Example |
|---|---|---|
| `gesture` | Display or react to the current recognized presentation command | `next` |

The current RecognitionEvent contract does not contain `confidence` or `source`.

The Session UI should map the current application-level gesture values into the existing UI states documented in `docs/ui-states.md`.

## Recognition Layer Boundary

The lower-level MediaPipe recognition prototype currently uses a different event schema.

For example:

```json
{
  "event_type": "gesture",
  "gesture": "swipe_left",
  "timestamp": "..."
}
```

Values such as `swipe_left` and `swipe_right` belong to this lower-level recognition schema and should not be treated as `RecognitionEvent.gesture` values.

At the time of this document, the lower-level MediaPipe event schema and the application-level RecognitionEvent / PresentationController flow are not yet connected.

Therefore, Session UI examples in this document use the application-level values `next`, `previous`, and `end`.

## Forward-Looking Sprint 2 Assumption: Confidence Feedback

SCRUM-80 requires the Sprint 2 Session UI to include recognition/confidence feedback, but the current RecognitionEvent contract does not expose a confidence value.

For this document:

- confidence is treated as a planned Session UI requirement, not an existing RecognitionEvent field;
- no current code contract is assumed to provide confidence;
- component tests may use a mocked confidence value to design and validate the visual state;
- integration of real confidence data will require either an extension to the recognition/application contract or another defined source of confidence data.

This assumption should remain explicit until the project defines and implements the real confidence-data contract.

No `source` field is assumed or required by this Session UI design.

## Component Breakdown

### 1. SessionPage

Top-level container for the Session route.

**Responsibilities**

- compose all Session UI components
- receive or subscribe to session/controller state
- receive recognition events
- coordinate status shown by child components
- provide the overall layout

**Referenced UI states**

- Loading
- Ready
- Active
- Paused
- Error

**Mock-testable**

Yes.

The page can be rendered with mocked session and recognition state without requiring a physical camera.

### 2. CameraPreview

Displays the camera area used during an active SlideKick session.

For Sprint 2, this component does not need to own recognition logic. It should display the camera surface or a status/fallback representation supplied by the application.

| State from `docs/ui-states.md` | Expected rendering |
|---|---|
| Loading | Camera initialization/loading indicator |
| Ready | Camera is available and ready before active recognition |
| Active | Camera preview available while the session is running |
| Paused | Preview remains visible or displays paused treatment |
| Error | Camera unavailable/permission/device error feedback |
| Empty | No camera source is available |

**Mock-testable**

Yes, for all visual states.

Tests can supply a mocked camera status or placeholder stream state. A real webcam is not required to verify loading, ready, paused, empty, or error rendering.

**Requires real hardware**

Actual camera permission, device initialization, and video-stream behavior require host-machine testing.

### 3. SessionStatusBadge

Provides a concise visual indication of the current session state.

| State from `docs/ui-states.md` | Expected label/behavior |
|---|---|
| Loading | Session starting |
| Ready | Ready |
| Active | Active |
| Paused | Paused |
| Error | Error |

**Mock-testable**

Yes.

This component should be fully testable by supplying a session status prop or mocked controller state.

### 4. GestureFeedback

Displays recognition feedback from the latest RecognitionEvent.

The component should not create new gesture-processing states. It should map recognition results to the existing gesture-related UI states.

| State from `docs/ui-states.md` | Expected rendering |
|---|---|
| No Gesture Detected | Neutral/no-current-gesture feedback |
| Gesture Detected | Display recognized application-level gesture/command |
| Error | Recognition unavailable or invalid recognition state |
| Loading | Recognition subsystem initializing, if applicable |

**Current data used**

- `RecognitionEvent.gesture`

**Example**

| Input | UI state | Display |
|---|---|---|
| No current recognition event / documented `none` state | No Gesture Detected | No gesture detected |
| `gesture = next` | Gesture Detected | Next |
| `gesture = previous` | Gesture Detected | Previous |
| `gesture = end` | Gesture Detected | End |
| recognition unavailable | Error | Recognition unavailable |

**Mock-testable**

Yes.

Recognition events can be created as test fixtures and passed directly to the component.

### 5. ConfidenceIndicator

Displays confidence feedback associated with gesture recognition.

Confidence feedback is part of the planned Sprint 2 Session UI, but confidence is not currently available on RecognitionEvent.

Until a real confidence contract exists, this component should be treated as a UI requirement that can be developed and tested using controlled/mock values.

**Required behavior**

- display confidence when a confidence value is available
- avoid showing misleading confidence when no value exists
- remain understandable without relying on color alone
- provide a text or accessible value for assistive technology

| State from `docs/ui-states.md` | Expected rendering |
|---|---|
| No Gesture Detected | No active confidence value or neutral state |
| Gesture Detected | Display confidence only if confidence data is available |
| Loading | Confidence unavailable while recognition initializes |
| Error | Confidence unavailable |

**Mocked design examples**

| Mocked input | Display |
|---|---|
| gesture detected, mocked confidence 0.92 | 92% |
| gesture detected, no confidence available | confidence unavailable/neutral |
| no current gesture | neutral/no confidence |
| recognition error | confidence unavailable |

These examples describe component test inputs, not the current RecognitionEvent schema.

**Mock-testable**

Yes.

This component can be tested with mocked numeric values even though the current application contract does not yet provide them.

### 6. PauseResumeControl

Allows the user to pause or resume an active Session.

This control should reflect session state rather than maintain an independent UI state model.

| State from `docs/ui-states.md` | Expected behavior |
|---|---|
| Active | Show Pause action |
| Paused | Show Resume action |
| Ready | Disabled or hidden until session begins |
| Loading | Disabled |
| Error | Disabled when session operation is unavailable |

**Mock-testable**

Yes.

Tests can verify:

- correct button label for Active/Paused
- disabled behavior for Loading/Error
- correct callback invoked on user interaction

Controller-side session behavior should be tested separately.

### 7. GestureFeedbackToast

Provides short-lived feedback when a valid gesture is recognized.

This is separate from the persistent GestureFeedback area only if the screen design requires transient feedback.

| State from `docs/ui-states.md` | Expected behavior |
|---|---|
| Gesture Detected | Display recognized application-level gesture/command briefly |
| No Gesture Detected | No toast |
| Error | Do not use gesture toast for general application errors |

**Current data used**

- `RecognitionEvent.gesture`

**Mock-testable**

Yes.

Tests can inject a RecognitionEvent such as `gesture = next` and verify that feedback appears.

If the implemented screen does not include transient feedback, this component can be omitted and the same information can remain in GestureFeedback.

### 8. SessionMessage

Displays persistent informational or error feedback associated with the Session screen.

| State from `docs/ui-states.md` | Expected rendering |
|---|---|
| Loading | Initialization/status message if needed |
| Ready | Optional ready/setup guidance |
| Error | Camera, recognition, or session error message |
| Empty | Missing/unavailable input message if applicable |

**Mock-testable**

Yes.

Error and status messages can be supplied directly as props or mocked controller state.

## Proposed Component Hierarchy

```text
SessionPage
├── SessionStatusBadge
├── CameraPreview
├── GestureFeedback
│   └── ConfidenceIndicator
├── GestureFeedbackToast
├── PauseResumeControl
└── SessionMessage
```

GestureFeedbackToast is optional if transient recognition feedback is not part of the implemented Session screen.

## State Ownership

Components should not independently invent application states.

The Session UI should receive state from the application/controller layer and render the matching states already documented in `docs/ui-states.md`.

| State/Data | Expected owner | Session UI responsibility |
|---|---|---|
| Ready / Active / Paused | Session/controller state | Render status and correct controls |
| Loading | Controller/camera/recognition initialization | Render loading feedback |
| Error | Relevant application subsystem | Render accessible error feedback |
| Gesture Detected | `RecognitionEvent.gesture` | Display recognized application command |
| No Gesture Detected | Recognition/session state | Display neutral recognition feedback |
| `gesture` | RecognitionEvent | Display next, previous, or end |
| Confidence | Not currently defined in RecognitionEvent | Display only through mocked/planned Sprint 2 interface until contract exists |

The frontend should avoid duplicating controller or recognition logic.

## Mocked Component Test Coverage

The following requirements are realistic targets for SCRUM-81 component tests and SCRUM-105 CI automation.

| Component | Mock test | Requires real hardware |
|---|---|---|
| SessionPage | Render Ready, Active, Paused, Error | No |
| CameraPreview | Loading, Ready, Active, Paused, Error, Empty rendering | Actual webcam stream only |
| SessionStatusBadge | Correct status label for each session state | No |
| GestureFeedback | next, previous, end, and No Gesture Detected | No |
| ConfidenceIndicator | Mock confidence values and unavailable state | No |
| PauseResumeControl | Label, enabled/disabled state, callbacks | Controller integration only |
| GestureFeedbackToast | Appears for mocked RecognitionEvent | No |
| SessionMessage | Error/status text | No |

## Initial Test Cases

These are suitable starting cases for SCRUM-81 and SCRUM-105.

**Session status**

```gherkin
Given session state = Ready
Then the Session status displays Ready

Given session state = Active
Then the Session status displays Active
And the Pause action is available

Given session state = Paused
Then the Session status displays Paused
And the Resume action is available
```

**Camera state**

```gherkin
Given camera state = Loading
Then CameraPreview displays loading feedback

Given camera state = Error
Then CameraPreview displays camera error feedback
```

**Recognition feedback**

```gherkin
Given no current RecognitionEvent
Then the interface renders the documented No Gesture Detected state

Given RecognitionEvent:
  gesture = next

Then the interface renders Gesture Detected
And displays Next

Given RecognitionEvent:
  gesture = previous

Then the interface renders Gesture Detected
And displays Previous
```

**Planned confidence feedback**

The following is a mocked UI test, not an example of the current RecognitionEvent contract:

```gherkin
Given:
  gesture = next
  mocked confidence = 0.92

Then the interface displays Next
And displays 92% confidence
```

This test remains valid for component design, but integration with real confidence data depends on a future contract change.

## Accessibility Requirements

Accessibility behavior should follow `docs/accessibility-personas.md` rather than defining a separate Sprint 2 persona set.

For the Session components, implementation should preserve at minimum:

- status information available as text, not color only
- controls reachable by keyboard
- clear accessible labels for pause/resume controls
- confidence information available in a non-visual form when confidence data becomes available
- error messages exposed clearly to assistive technology
- gesture feedback understandable without relying only on animation

Detailed persona requirements remain in `docs/accessibility-personas.md`.

## Sprint 2 Scope Boundary

The following are in scope for this Session requirements document:

- Session screen component structure
- camera/status presentation
- planned confidence presentation
- application-level recognition feedback using next, previous, and end
- pause/resume presentation behavior
- mapping existing application states into UI rendering
- mocked component-test targets

The following are not defined here:

- new global UI state names
- recognition/classification algorithms
- camera initialization implementation
- controller session-state implementation
- integration between the lower-level MediaPipe `swipe_left` / `swipe_right` schema and RecognitionEvent
- the final confidence-data contract
- calibration screen implementation
- gesture-profile screen implementation
- accessibility persona definitions

Calibration and profile interfaces can reuse these patterns in later work but are not part of the Sprint 2 Session implementation described here.
