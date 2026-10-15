# Observer Event Contract Draft

**Status:** Sprint 2 draft
**Owner:** Project team

## Purpose

Define the stable messages exchanged between recognition, the controller, and the presentation command adapter. The UI should not depend on implementation details of camera capture, ML inference, or keyboard control.

## Recognition events

Recognition emits plain dictionaries, built by the helpers in `src/slidekick/recognition/events.py`. Every event has an `event_type`.

Gesture event:

| Field | Type | Required | Contract |
|---|---|---:|---|
| `event_type` | `string` | Yes | Always `"gesture"` |
| `gesture` | `string` | Yes | Recognized gesture name, currently `swipe_right` or `swipe_left` |
| `confidence` | `float` | Yes | Score from `0.0` to `1.0`, which the swipe recognizer clamps to that range |
| `timestamp` | `float` | Yes | Time the event was created |

Landmark event:

| Field | Type | Required | Contract |
|---|---|---:|---|
| `event_type` | `string` | Yes | Always `"landmarks"` |
| `timestamp` | `float` | Yes | Time the event was created |
| `landmarks` | `list` | Yes | One entry per detected hand landmark, each with `id`, `x`, `y` and `z` |

Rules:

1. Only gesture events can trigger a presentation command. Landmark events are for display and diagnostics, and the command controller ignores them.
2. Recognition decides which gesture happened. It does not decide what the gesture does.
3. Recognition providers must emit the same event shape whether the source is the camera pipeline or something else.

## Gesture to command mapping

`GestureCommandController.handle_event` in `src/slidekick/gesture_command_controller.py` consumes recognition events and returns the adapter's result, or `False` when nothing ran.

- Events whose `event_type` is not `"gesture"` are ignored.
- A gesture is looked up in the controller's bindings. The defaults are `swipe_right` to `next` and `swipe_left` to `previous`.
- A gesture with no binding does nothing.
- A bound command calls the matching method on the presentation adapter. The supported commands are `next`, `previous`, `pause`, `resume` and `end`.

There is no separate command event. The result of the mapping is the adapter call and the boolean it returns.

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
3. Subscribers read this event to react to session state without needing to know how the controller decided to change it.

## Observer boundary

### Recognition → Gesture command controller

Recognition emits events through a handler passed to `run_camera`. `scripts/run_gesture_control.py` passes `GestureCommandController.handle_event`, so each event goes straight to the controller.

### Session controller → Subscribers

The session controller publishes `SessionEvent` values after successful state transitions.

Nothing subscribes to it yet. It is not connected to the gesture command controller or to the UI. Intended subscribers include the React UI and recognition or session coordination, for example ignoring gestures while a session is paused. The browser cannot subscribe to the Python controller until a browser to Python transport exists.

Subscribers must not directly mutate session state through the event.
Session state changes must go through the session controller.

## Current flow

```text
camera
  -> swipe recognizer
  -> gesture event (dict)
  -> GestureCommandController.handle_event
  -> presentation adapter
```

The Session page in the React UI does not use this path. It keeps its own local status state, driven by demo controls.

## Compatibility and change policy

- Additive fields require a documented default or migration plan.
- Renaming an existing field requires updating Python contracts, frontend types, tests, and documentation in the same pull request.
- New gestures must be added to the recognizer, the controller bindings, the UI affordances, and tests together.
- Adapter-specific behavior belongs behind `PresentationAdapter` and must not leak into recognition events.

## Known gaps

- The frontend session types still use the earlier gesture names `next`, `previous`, `end` and `none`, which are not aligned with the recognition names `swipe_left` and `swipe_right`.
- No browser to Python transport exists yet.
- Session events have no subscribers yet.
