# Observer Event Contract Draft

**Status:** Sprint 2 draft
**Owner:** Project team

## Purpose

Define the stable messages exchanged between recognition, the controller, and the presentation command adapter. The UI should not depend on implementation details of camera capture, ML inference, or keyboard control.

## RecognitionEvent

| Field | Type | Required | Contract |
|---|---|---:|---|
| `gesture` | `Gesture` | Yes | `next`, `previous`, `end`, or `none` |
| `confidence` | `float` | Yes | Inclusive range `0.0` to `1.0` |
| `source` | `string` | Yes | Provider identifier, such as `placeholder` or a future model name |

Rules:

1. `confidence` outside `[0, 1]` is invalid.
2. `Gesture.NONE` is an intentional no-op and must not create a presentation command.
3. Recognition providers must emit the same contract regardless of whether the source is placeholder logic, a camera pipeline, or an ML model.

## CommandEvent

| Field | Type | Required | Contract |
|---|---|---:|---|
| `command` | `string` | Yes | Normalized command such as `next_slide`, `previous_slide`, or `end_presentation` |
| `source_gesture` | `Gesture` | Yes | Gesture that caused the command |
| `metadata` | `object \| null` | No | Diagnostic information, including confidence and source |

## SessionEvent

Published by the session controller when a session transitions between states. See [Session State Model](session-state-model.md) for the full state machine, valid and invalid transitions, and the UC10/UC6/UC7/UC8 mapping this is built from.

| Field | Type | Required | Contract |
|---|---|---:|---|
| `type` | `SessionEventType` | Yes | `session_started`, `session_paused`, `session_resumed`, or `session_ended` |
| `previous_state` | `SessionState` | Yes | The state the session was in before this transition |
| `new_state` | `SessionState` | Yes | The state the session is in after this transition |
| `use_case` | `string` | Yes | The UC ID that triggered the transition, e.g. `"UC10"` |

Rules:

1. Only published after a transition has been validated and applied; an invalid transition attempt does not publish an event.
2. `previous_state` and `new_state` must always differ; an event describes a change, not a no-op.
3. Subscribers (UI, recognition, presentation adapter) read this event to react to session state without needing to know how the controller decided to change it.

## Observer boundary

### Recognition → Controller

The recognition provider publishes or returns `RecognitionEvent` values.
The controller consumes these events and maps supported gestures to
normalized presentation commands.

### Session Controller → Subscribers

The session controller publishes `SessionEvent` values after successful
state transitions.

Subscribers may include:
- React UI
- recognition/session coordination
- other components that need session-state updates

Subscribers must not directly mutate session state through the event.
Session state changes must go through the session controller.

## Current Sprint 1 flow

```text
React Session UI
  -> local placeholder recognition
  -> controller contract
  -> normalized command event
  -> presentation adapter boundary
```

The browser-to-Python transport and live camera/model observer are intentionally deferred beyond Sprint 1.

## Compatibility and change policy

- Additive fields require a documented default or migration plan.
- Renaming an existing field requires updating Python contracts, frontend types, tests, and documentation in the same pull request.
- New gestures must be added to the enum, controller mapping, UI affordances, and tests together.
- Adapter-specific behavior belongs behind `PresentationAdapter` and must not leak into recognition events.
