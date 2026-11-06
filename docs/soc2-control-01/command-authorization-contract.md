# Command Authorization Contract

**Control:** SOC 2 Control 01, Keyboard Command Authorization, aligned to CC6.1
**Owner:** Joon Rho, R01
**Supports:** AC-01 and gap G3
**Code:** `src/slidekick/command_policy.py`, `src/slidekick/gesture_command_controller.py`

This is a project control interpretation of CC6.1. It is not an official AICPA control title and it is not a claim of SOC 2 certification.

## The rule

Only a documented presentation command, requested through a validated gesture mapping, while the session is RUNNING, may reach the presentation adapter. Anything else is refused and no key is pressed.

## Approved commands

| Command | Key pressed by the adapter | Who may trigger it |
|---|---|---|
| `next` | right | gesture profile, helper endpoint `/next` |
| `previous` | left | gesture profile, helper endpoint `/previous` |
| `pause` | b | gesture profile, helper endpoint `/pause` |
| `resume` | b | gesture profile, helper endpoint `/resume` |
| `end` | esc | lifecycle or manual control only, never a gesture profile |

The profile bindable set is `next`, `previous`, `pause` and `resume`. The approved set adds `end`. Both sets live in `command_policy.py` and nowhere else.

## Decision on end

`end` is not bindable by a gesture profile. A wrong mapping should not be able to close the slideshow in front of an audience. The adapter keeps `end_presentation` for lifecycle and manual use, and `execute_command` still refuses the string `end`. To change this decision, move `end` into `PROFILE_BINDABLE_COMMANDS` and update the tests that name it. Nothing else needs to move.

## Pause and resume are two different things

The session pause stops SlideKick from acting on gestures. It presses no key. The slideshow pause and resume commands press `b` and blank the screen. The two never trigger each other. Because both slideshow commands press the same key, the adapter has no memory of whether the screen is currently blank.

## Gesture to command mapping

A mapping is a dictionary from gesture id to command name. It is accepted only if every entry passes both checks.

| Part | Rule |
|---|---|
| Gesture id | A string of lowercase letters, digits and underscores, starting with a letter, at most 64 characters |
| Command | A string that is exactly one of the bindable commands, in lowercase, with no spaces |
| Whole mapping | Must be a mapping. An empty one is valid and binds nothing |

One bad entry rejects the whole mapping. The previous mapping stays active. All problems are reported in a single error so a profile can be fixed in one pass.

The gesture id check covers shape only. Which ids the recognizer really emits belongs to the recognition owner. If a registry of known gestures is added later, it should plug in beside the shape check.

## Where the rule is enforced

| Layer | Check | Owner |
|---|---|---|
| Mapping load or update | `validate_gesture_bindings` refuses anything outside the table above | Joon |
| Session | Only RUNNING sessions pass gesture events on | Joon |
| Controller dispatch | Re-checks the command against the bindable set and fails closed | Joon |
| Adapter `execute_command` | Four command string allowlist, everything else returns Invalid Command | Eric |
| Native helper | Fixed POST routes, loopback only | Eric |

The adapter and helper rows are defense in depth. Control 01 relies on them but does not own them.

## For anyone adding profile loading

Call `validate_gesture_bindings`, or hand the mapping to `GestureCommandController.set_gesture_bindings`, before a profile becomes active. Do not store profile data in the controller any other way. The `gesture_bindings` property is a read-only view on purpose.
