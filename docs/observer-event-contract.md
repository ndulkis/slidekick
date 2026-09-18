# Observer Event Contract Draft

**Status:** Sprint 1 draft
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

## Observer boundary

The recognition provider publishes or returns `RecognitionEvent` values. The controller is the observer/consumer of those values. The controller is responsible for:

- validating or relying on the typed event contract;
- mapping supported gestures to normalized commands;
- ignoring `none` events;
- invoking the configured `PresentationAdapter`;
- returning a `CommandEvent` for successful command mapping.

The recognition provider must not import or call a presentation adapter. The UI must not call `pyautogui` or any presentation adapter directly.

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
