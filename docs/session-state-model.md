# Session State Model

**Status:** Sprint 2 draft
**Owner:** R01
**Scope:** S2-R01-T1, states and transitions for UC10, UC6, UC7, UC8

## Source

This model is a direct translation of the State Diagram in the requirements doc (Requirements Modeling section) into a state machine the session controller can implement. It covers only the states reachable through UC10, UC6, UC7, and UC8. The diagram also includes Customizing Gestures and Error/Recovery Needed, driven by UC9 and by camera/platform errors, those are out of scope for this model and should be picked up when that part of the controller is built.

## States

```python
class SessionState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"
```

| SessionState | Diagram state | Meaning |
|---|---|---|
| `IDLE` | Idle | App is open, no presentation session has been started |
| `RUNNING` | Presentation Mode Active | Presentation Mode is active, gesture recognition is on |
| `PAUSED` | Gesture Recognition Paused | Presentation Mode is active, gesture recognition is paused, camera feed stays on |
| `ENDED` | Presentation Finalized | Session has been finalized, gesture recognition and camera are off |

## Events

```python
class SessionEventType(StrEnum):
    STARTED = "session_started"
    PAUSED = "session_paused"
    RESUMED = "session_resumed"
    ENDED = "session_ended"
```

```python
@dataclass(frozen=True)
class SessionEvent:
    type: SessionEventType
    previous_state: SessionState
    new_state: SessionState
    use_case: str  # "UC10", "UC6", "UC7", or "UC8"
```

The controller's public operations are named after the triggering action (`start()`, `pause()`, `resume()`, `end()`), matching the plan's `START_SESSION` / `PAUSE_SESSION` / `RESUME_SESSION` / `END_SESSION` vocabulary. Each operation, once it validates the current state and changes it, publishes the `SessionEvent` above describing what just happened. This follows the same shape as `RecognitionEvent` and `CommandEvent` in the [Observer Event Contract](observer-event-contract.md), where that contract now also lives.

## Valid transitions

| From | Event | To | Use case |
|---|---|---|---|
| `IDLE` | `START_SESSION` | `RUNNING` | UC10: Start Presentation Mode |
| `RUNNING` | `PAUSE_SESSION` | `PAUSED` | UC6: Pause Gesture Recognition |
| `PAUSED` | `RESUME_SESSION` | `RUNNING` | UC7: Resume Gesture Recognition |
| `RUNNING` | `END_SESSION` | `ENDED` | UC8: Finalize Presentation |
| `ENDED` | `START_SESSION` | `RUNNING` | UC10: Start Presentation Mode (restart) |

The `ENDED -> RUNNING` restart path is drawn directly in the diagram as a UC10 edge from Presentation Finalized back to Presentation Mode Active. It's a separate decision from the initial `IDLE -> RUNNING` start, both are triggered by `START_SESSION`, but from different states, so the controller needs to branch on current state rather than assume `START_SESSION` only ever fires from `IDLE`.

## Invalid transitions

| From | Event | Why it's invalid |
|---|---|---|
| `IDLE` | `PAUSE_SESSION` | Nothing is running to pause |
| `IDLE` | `RESUME_SESSION` | Nothing is paused to resume |
| `IDLE` | `END_SESSION` | No active session to finalize |
| `RUNNING` | `START_SESSION` | Already running; not shown as a transition in the diagram |
| `PAUSED` | `START_SESSION` | A session is already in progress, just paused |
| `PAUSED` | `PAUSE_SESSION` | Already paused |
| `ENDED` | `PAUSE_SESSION` | Nothing is running to pause |
| `ENDED` | `RESUME_SESSION` | Nothing is paused to resume |
| `ENDED` | `END_SESSION` | Already ended |

## Open question for the team

The diagram has no edge from Gesture Recognition Paused directly to Presentation Finalized. That leaves `PAUSED -> END_SESSION` undefined rather than explicitly valid or invalid. Two reasonable options:

1. Treat it as invalid, require `RESUME_SESSION` before `END_SESSION`, matching what's actually drawn.
2. Treat it as valid, a user should be able to end a presentation while paused without being forced to resume first.

This needs a team decision before T2 implements `end()`, since the controller's validation logic depends on which way this goes. Until decided, this model treats `PAUSED -> END_SESSION` as invalid, the conservative reading of what's actually drawn.

## Acceptance checklist

- [x] All four states documented
- [x] Valid transitions defined
- [x] Invalid transitions defined
- [x] UC10/UC6/UC7/UC8 mapped
- [x] Event names and payload defined
- [ ] Team reviews and agrees on the contract, including the open question above
