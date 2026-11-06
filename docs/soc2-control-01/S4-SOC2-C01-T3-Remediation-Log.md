# S4-SOC2-C01-T3 Remediation Log: Controller and Gesture Mapping

**Jira:** SCRUM-172
**Owner:** Joon Rho, R01
**Date:** November 4, 2026

Findings F1 to F3 from the assessment were confirmed against the original code, so remediation was required. F4 to F7 need no code change from this control. They are recorded as residual risk or handed off.

## Changes

| Finding | Change | Files |
|---|---|---|
| F1 | `end` is no longer bindable. Only `next`, `previous`, `pause` and `resume` are | `src/slidekick/command_policy.py` |
| F2 | Mappings are validated when loaded. A bad id, a bad command, or a non mapping is refused with one error listing every problem | `src/slidekick/command_policy.py`, `src/slidekick/gesture_command_controller.py` |
| F2 | The controller dispatch checks the command again and returns False for anything not bindable, including unhashable values that used to raise | `src/slidekick/gesture_command_controller.py` |
| F3 | `gesture_bindings` is a read only view. Replacing bindings goes through `set_gesture_bindings`, which validates first and swaps all at once. The default bindings are read only | `src/slidekick/gesture_command_controller.py` |
| F5 | New tests assert zero calls on the keyboard library for every refused input | `tests/unit/test_control01_keyboard_command_authorization.py` |

The unified diff is in `control01.patch`.

## Behavior change to know about

One Sprint 3 test described the old behavior on purpose. `test_custom_mapping_routes_through_coordinator_and_rejects_unknown_command` loaded a mapping containing `arbitrary_hotkey` and expected a failure at dispatch. That mapping is now refused when it is loaded, which is exactly what AC-05 asks for. The test was split in two:

- `test_custom_mapping_routes_through_coordinator` keeps the valid half
- `test_custom_mapping_with_unknown_command_is_rejected_before_use` covers the refusal

No other existing test changed. The original file is kept in `evidence/` for comparison.

## Decision for the team

Keeping `end` out of gesture profiles is a policy choice and not a bug fix. It is the safer default and it matches the lifecycle design. If the team wants a gesture to end a presentation, the change is one line in `PROFILE_BINDABLE_COMMANDS` plus two tests. Please confirm with Eric and Diego before the profile feature lands.

## Not changed on purpose

| Item | Reason |
|---|---|
| F4, controller has no session gate | The coordinator stays the one enforcement point, as the Sprint 4 draft decided. Adding a gate to the controller changes the coordinator contract. Worth a follow up if more callers appear |
| F6, adapter error echo | Adapter is Eric's. Handed off |
| F7, window focus | Eric's hardening task. Stays listed as residual risk |
| Adapter, helper, CI workflow | Not Joon's files |

## Retest

All new tests and every existing test pass after the change. Details and numbers are in the evidence report.
