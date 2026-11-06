# S4-SOC2-C01-T1 Risk Assessment: Keyboard Command Authorization

**Jira:** SCRUM-170
**Control owner:** Joon Rho, R01
**Criterion:** CC6.1, logical access security, applied at the application action boundary
**Date:** November 4, 2026
**Method:** Source review of the repository snapshot, plus a probe of the original controller with a fake keyboard library. No real key was pressed at any point.

This assessment is a project control interpretation of CC6.1. It is not a claim of SOC 2 certification.

## 1. What is being protected

A simulated keystroke lands in whatever window has focus. A wrong command can skip slides, blank the screen or end a presentation in front of an audience, so every route to the keyboard needs a gate. The control separates two jobs:

- **Controller authorization** decides whether a command is allowed to be requested at all. This is Joon's layer: bindings, session gate and controller dispatch.
- **Native adapter enforcement** decides whether a requested command may become a keystroke. This is Eric's layer: the adapter, the Windows helper and window focus.

## 2. Command entry paths

| Path | How a command gets in | Gates before the keyboard | Gap found |
|---|---|---|---|
| P1 | Recognition event into `SessionCoordinator.handle_event`, then the controller, then an adapter method | RUNNING state, event shape check, bound gesture, command policy | None on this path after remediation |
| P2 | `GestureCommandController.handle_event` called directly | Bound gesture and command policy only. The controller does not know the session state | F4, residual by design |
| P3 | Windows helper POST to `/next`, `/previous`, `/pause`, `/resume` | Fixed routes, POST only, loopback bind, four command allowlist | No caller authentication, owned by Eric |
| P4 | Direct calls to adapter methods such as `end_presentation` | None. This is the lowest layer by design | Expected, covered by code review |
| P5 | `execute_command` with a string | Four command allowlist, case and space normalization, error result otherwise | F5 and F6 |
| P6 | Loading a gesture profile or config | Did not exist. The constructor accepted any mapping unchecked | F1, F2, F3 |
| P7 | Frontend | The React app makes no network calls today, so it has no route to the keyboard yet | Revisit when transport is added |

P6 matters most for the future. There is no profile loading code yet. The only mapping sources today are the defaults and the constructor argument, so the controller is where the contract has to live.

## 3. Risk matrix

Likelihood and impact are rated on a three level scale. Status is the state after the Sprint 4 work.

| ID | Risk | Likelihood | Impact | Existing protection | Finding | Status |
|---|---|---|---|---|---|---|
| R1 | Unsupported or malformed command reaches the keyboard | Low | Medium | Adapter allowlist and Invalid Command result | F5, tests did not prove zero key presses | Closed by new tests |
| R2 | A profile maps a gesture to an unexpected action | Medium | High | Unknown command strings failed at dispatch only | F1, F2, F3 | Closed by remediation |
| R3 | Command runs outside a RUNNING session | Low | Medium | Coordinator gates on RUNNING | F4, the controller can be called without the gate | Residual, documented |
| R4 | Approved shortcut reaches the wrong window | Medium | Medium | None in code | Focus is not checked | Open, owned by Eric |
| R5 | Helper accepts requests from any local process | Medium | Medium | Loopback bind, POST only | No authentication | Open, owned by Eric, see his CC6.6 assessment |

## 4. Findings

Every finding marked confirmed was reproduced by running the original code. The output is in `evidence/baseline_probe_output.txt`.

**F1. End was bindable from a profile. Confirmed.**
Binding a gesture to `end` and sending it during a RUNNING session pressed escape. The draft listed this as G3. Nothing in the code said whether it was allowed.

**F2. Malformed mappings were accepted at load. Confirmed.**
A mapping to `ctrl+w`, to a list, or with a number as the gesture id loaded without complaint. Strings failed quietly at dispatch, so no key was pressed. A list as the command raised a `TypeError` from the controller instead of failing closed. The criterion AC-05 asks for rejection before use, so this fails it.

**F3. Bindings could be changed after construction. Confirmed.**
`gesture_bindings` was a plain public dictionary. Writing `end` into it after validation, or into the shared default dictionary, bypassed any check a loader might add. The shared default also leaked between controllers.

**F4. The controller has no session awareness. Confirmed.**
Calling `handle_event` on the controller during an IDLE session pressed right arrow. The coordinator is the real gate and the live script uses it, but the performance test pipeline calls the controller directly. This is acceptable only while the coordinator stays the one supported entry point.

**F5. Existing invalid command tests did not prove zero key presses.**
The adapter tests assert the error result but never assert that the keyboard library was untouched. The adapter code is correct today. The proof was missing.

**F6. The adapter echoes the raw command and the exception message in its error result.**
Low risk, because the helper only passes fixed strings. Worth tidying when Eric next touches the adapter. No change made.

**F7. Window focus is not validated. Not tested here.**
This is G5 from the draft. Command allowlisting does not solve it and this report does not claim it does.

## 5. State names

The draft refers to a READY state. The code and the session state model call it `IDLE`. This assessment and the tests use `IDLE`. The matrix tested is IDLE, RUNNING, PAUSED and ENDED.

## 6. Hand offs

| To | Item |
|---|---|
| Eric | F6 error echo, R4 window focus, R5 helper authentication, and whether the adapter should expose the command set so tests can read it instead of probing |
| Diego | Whether a registry of known gesture ids should sit beside the shape check |
| Nathan | Nothing required. The new tests already run under the existing unit test CI step |

## 7. Ownership check

No file owned by Eric, Diego, Andres or Nathan was changed. The adapter, the helper and the CI workflow are untouched. Their current behavior was only read and probed.
