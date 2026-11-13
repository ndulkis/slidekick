# S4-R01-T1 Interface Contracts and Ownership Boundaries

**Jira:** SCRUM-167
**Owner:** Joon Rho, R01
**Status:** Draft. Contract A and D describe code that already exists. Contract B and C describe code added in SCRUM-168. Teammate sign-off is pending, see the last section.

## How the layers fit

```text
Profile file or profile UI
  -> load_profile or profile_from_mapping       gesture_profile.py            Joon
     -> GestureProfile, read only
        -> SessionCoordinator.apply_profile     session_coordinator.py        Joon
           -> GestureCommandController          gesture_command_controller.py Joon

Recognition event
  -> SessionCoordinator.handle_event            session gate, RUNNING only    Joon
     -> GestureCommandController.handle_event   gesture to command mapping    Joon
        -> PresentationAdapter methods          presentation_adapter.py       Eric
           -> keyboard
```

Every arrow is a point where bad input is refused. Nothing below a refusal runs.

## Contract A: recognition event, owned by Diego

The recognizer emits plain dictionaries. The full shapes are in `docs/observer-event-contract.md`. The controller reads two fields only.

| Field | Rule |
|---|---|
| `event_type` | The string `gesture` for a gesture event. Landmark events use another value and never trigger a command |
| `gesture` | A string gesture id. Anything else is ignored |

A gesture id is lowercase letters, digits and underscores, starts with a letter, and is at most 64 characters. Today the recognizer emits `swipe_right` and `swipe_left`. New ids from custom or static gestures must follow the same rule so a profile can name them.

Diego decides which ids exist. R01 decides how a profile binds them.

## Contract B: profile file, written by the UI or enrollment, read by R01

A profile is a JSON object with exactly three fields.

| Field | Rule |
|---|---|
| `version` | The number 1. Any other value, including the text "1", is refused |
| `name` | Letters, digits, spaces, underscores, dots and hyphens. Starts with a letter or digit. At most 64 characters |
| `bindings` | An object from gesture id to command name. Every command must be `next`, `previous`, `pause` or `resume`. An empty object is valid and binds nothing |

```json
{
  "version": 1,
  "name": "presenter",
  "bindings": {
    "swipe_right": "next",
    "swipe_left": "previous",
    "palm_open": "pause",
    "fist": "resume"
  }
}
```

Loading rules:

- Unknown fields are refused.
- A key repeated anywhere in the file is refused, so a binding cannot hide behind a later copy.
- Files over 64 KB, files that are not UTF-8 and files that are not JSON are refused.
- One bad entry rejects the whole profile. Nothing is partly loaded.
- All problems are reported together in one `InvalidProfileError`. A message quotes at most 40 characters of a rejected value.
- Loading never presses a key and never touches a session.

An optional `known_gestures` set can be passed to the loader. When it is given, a profile that binds an id outside the set is refused. Diego supplies that set.

The built in default is `profiles/default.json`. A test keeps it equal to the controller's default bindings.

## Contract C: controller and session, owned by Joon

| Call | Behavior |
|---|---|
| `GestureCommandController` created with bindings | Validates them first. Raises `InvalidGestureBindingError` on any problem |
| `controller.gesture_bindings` | A read only view. It cannot be edited or replaced from outside |
| `controller.set_gesture_bindings` | Validates, then swaps all bindings at once. On failure the previous bindings stay |
| `controller.handle_event` | Returns True only when a bound gesture reached the adapter and the adapter returned True. Unbound, malformed and non gesture events return False. A command outside the bindable set returns False even if bindings were corrupted |
| `coordinator.apply_profile` | Needs a `GestureProfile`. Refused with `ProfileChangeError` while RUNNING. Allowed in IDLE, PAUSED and ENDED. On any failure the previous bindings and `profile_name` stay |
| `coordinator.handle_event` | Unchanged. Only RUNNING sessions pass gesture events on |

Applying a profile never calls the adapter, and a profile change does not change the session state.

## Contract D: presentation adapter, owned by Eric

The controller needs these methods and nothing else.

| Method | Key | Returns |
|---|---|---|
| `next_slide` | right | True when the key was attempted |
| `previous_slide` | left | True when the key was attempted |
| `pause_presentation` | b | True when the key was attempted |
| `resume_presentation` | b | True when the key was attempted |
| `end_presentation` | esc | True when the key was attempted. Never reachable from a gesture profile |

The adapter also offers `execute_command` for the Windows helper. It accepts only the four commands above as strings. A false result or an exception becomes a `PresentationCommandError` in the coordinator.

This task asks the adapter for no change. One open request: the controller sees only true or false and cannot tell why a key failed. Status exposure belongs to SCRUM-57.

## Approved presentation actions

| Command | Bindable by a profile | Notes |
|---|---|---|
| `next` | Yes | |
| `previous` | Yes | |
| `pause` | Yes | Slideshow black screen. Not the same as the session pause |
| `resume` | Yes | Same key as pause, so the adapter does not know the screen state |
| `end` | No | Lifecycle or manual use only |

The full rule is in `docs/soc2-control-01/command-authorization-contract.md`.

## Ownership boundaries

| Area | Owner | May change alone | Needs sign-off |
|---|---|---|---|
| `command_policy.py`, `gesture_profile.py`, controller, coordinator, `profiles/` | Joon | Internals that keep the contracts above | A contract change, from Diego, Andres and Eric |
| Recognition package and gesture ids | Diego | Algorithms, classifiers, new ids that follow Contract A | A new id format, from Joon |
| Frontend and profile UI | Andres | Layout and flow | A different profile shape, from Joon |
| `presentation_adapter.py`, `windows_helper.py`, enrollment backend | Eric | Key handling, focus handling, platform fallbacks | A new command or a changed return value, from Joon |
| CI workflow and shared tooling | Nathan | Pipeline steps | Nothing from R01 |

Adding a command takes four steps in this order: add it to `command_policy.py`, add it to the adapter, add tests in both places, then get sign-off from Joon and Eric.

## Review sign-off

Nothing here is approved yet. Each row stays Pending until the person answers in writing.

| Person | Confirms | Status | Date and note |
|---|---|---|---|
| Diego | Gesture id rule in Contract A, and who passes the known gestures to the loader | Pending | |
| Andres | The profile schema in Contract B fits the profile UI | Pending | |
| Eric | Contract D, and where enrollment output goes | Pending | |
