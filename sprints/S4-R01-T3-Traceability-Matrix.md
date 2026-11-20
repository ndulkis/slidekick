# S4-R01-T3 Requirements to Test Traceability Matrix

**Jira:** SCRUM-169, covering the changes made in SCRUM-168
**Owner:** Joon Rho, R01
**Scope:** gesture profiles, the session layer that applies them, and the Control 01 checks they rely on

Results below are from local runs. CI results are not attached yet. See `S4-R01-T3-Peer-Review-and-Regression.md`.

## Test files

| Short name | File |
|---|---|
| Profile tests | `tests/unit/test_gesture_profile.py` |
| Session tests | `tests/unit/test_session_apply_profile.py` |
| Pipeline tests | `tests/integration/test_gesture_profile_pipeline.py` |
| Control 01 tests | `tests/unit/test_control01_keyboard_command_authorization.py` |
| Existing tests | `tests/unit/test_gesture_command_controller.py`, `tests/unit/test_session_coordinator.py`, `tests/integration/test_s3_test2_session_pipeline.py` |

## Summary

| ID | Requirement | Source | Code | Result |
|---|---|---|---|---|
| REQ-GP-01 | A profile binds gestures only to approved, bindable commands | UC9 as cited in `session-state-model.md`, SCRUM-168, Control 01 AC-01 | `command_policy.py`, `gesture_profile.py` | Verified locally |
| REQ-GP-02 | Invalid profiles and mappings are rejected before dispatch | SCRUM-168, Control 01 AC-05 | `gesture_profile.py`, `command_policy.py`, controller | Verified locally |
| REQ-GP-03 | Profile files are read safely | Design requirement from CC6.1 input handling | `load_profile` | Verified locally |
| REQ-GP-04 | A profile is applied through the session layer and never while RUNNING | SCRUM-168, session restrictions | `SessionCoordinator.apply_profile` | Verified locally |
| REQ-GP-05 | Gesture events reach the adapter only while RUNNING, whichever profile is active | UC10, UC6, UC7, UC8, Control 01 AC-04 | `SessionCoordinator.handle_event` | Verified locally |
| REQ-GP-06 | Swipe navigation keeps working with the default profile | UC1 and UC2 in the Sprint 3 gap analysis | controller, default profile | Verified locally |
| REQ-GP-07 | A profile can be limited to gestures the recognizer emits | Dependency on Diego, see the T1 plan | `known_gestures` in the loaders | Partly verified. Nothing passes the set in yet |
| REQ-GP-08 | No profile can trigger `end` or a key outside the documented set | Control 01 AC-03 and gap G3 | `command_policy.py`, controller | Verified locally |
| REQ-GP-09 | The rest of the project does not regress | SCRUM-169 | whole repository | Passing locally. CI pending |

## Tests by requirement

### REQ-GP-01 Approved commands only

- Profile tests: `test_valid_mapping_builds_a_profile`, `test_default_file_matches_built_in_defaults`, `test_valid_profile_names`, `test_empty_bindings_are_valid_and_bind_nothing`
- Pipeline tests: `test_profile_file_drives_the_keyboard_through_every_layer`
- Control 01 tests: `test_ac01_policy_sets_are_consistent`, `test_ac01_default_bindings_only_use_bindable_commands`, `test_ac05_approved_custom_profile_works_across_the_stack`
- Existing tests: `test_custom_mapping_routes_through_coordinator`

### REQ-GP-02 Rejected before dispatch

- Profile tests: `test_bad_bindings_are_rejected_before_use`, `test_bindings_must_be_a_mapping`, `test_non_mapping_profile_is_rejected`, `test_missing_field_is_rejected`, `test_wrong_version_is_rejected`, `test_unknown_fields_are_rejected`, `test_bad_profile_name_is_rejected`, `test_directly_built_profile_is_validated_too`, `test_one_bad_entry_rejects_the_whole_profile_and_every_problem_is_reported`, `test_file_with_a_dangerous_binding_is_rejected`
- Pipeline tests: `test_bad_profile_file_is_rejected_at_load_and_the_old_profile_keeps_working`, `test_controller_still_refuses_unvalidated_bindings_handed_to_it_directly`
- Control 01 tests: `test_ac05_bad_command_target_is_rejected_at_load`, `test_ac05_bad_gesture_id_is_rejected_at_load`, `test_ac05_non_mapping_profile_is_rejected`, `test_ac05_one_bad_entry_rejects_the_whole_profile_and_reports_all_problems`
- Existing tests: `test_custom_mapping_with_unknown_command_is_rejected_before_use`, which replaces a Sprint 3 test whose expected behavior changed on purpose

### REQ-GP-03 Safe file reading

- Profile tests: `test_file_over_the_size_limit_is_rejected`, `test_file_at_the_size_limit_is_read`, `test_invalid_json_is_rejected`, `test_valid_json_that_is_not_an_object_is_rejected`, `test_non_utf8_file_is_rejected`, `test_repeated_key_is_rejected_so_a_binding_cannot_hide`, `test_repeated_top_level_key_is_rejected`, `test_deeply_nested_file_is_rejected_without_crashing`, `test_missing_file_is_rejected`, `test_directory_is_rejected`, `test_path_with_a_null_byte_is_rejected`, `test_error_text_stays_short_for_huge_values`, `test_error_text_quotes_only_a_short_piece_of_a_rejected_value`, `test_load_valid_file_from_a_path_or_a_string`

### REQ-GP-04 Applied through the session, never while RUNNING

- Session tests: `test_profile_can_be_applied_when_the_session_is_not_running`, `test_profile_is_refused_while_running_and_nothing_changes`, `test_only_a_gesture_profile_is_accepted`, `test_a_rejected_change_keeps_the_previous_profile_name_and_bindings`, `test_applying_a_profile_never_calls_the_adapter`
- Pipeline tests: `test_changing_profile_mid_session_needs_a_pause`
- Control 01 tests: `test_ac05_failed_update_keeps_previous_bindings_active`, `test_ac05_valid_update_replaces_bindings_atomically`

### REQ-GP-05 RUNNING only

- Session tests: `test_session_restrictions_still_hold_after_a_profile_is_applied`, `test_new_bindings_drive_commands_after_resume_and_old_ones_stop`
- Pipeline tests: `test_nothing_reaches_the_keyboard_until_the_session_is_running`
- Control 01 tests: `test_ac04_inactive_session_blocks_every_gesture`, `test_ac04_running_session_dispatches_exactly_once`, `test_ac04_restart_after_end_routes_again`, `test_ac04_lifecycle_changes_press_no_keys`, `test_ac04_malformed_events_while_running_press_nothing`
- Existing tests: `test_lifecycle_gates_both_gesture_directions`, `test_recognition_events_reach_adapter_only_while_running`, `test_session_pause_resume_and_end_never_invoke_slideshow_shortcuts`, `test_invalid_transition_keeps_state_and_does_not_send_blank_key`

### REQ-GP-06 Default navigation

- Session tests: `test_applying_the_default_profile_restores_the_default_bindings`
- Control 01 tests: `test_ac03_gesture_to_key_end_to_end`
- Existing tests: `test_swipe_right_routes_to_next_slide`, `test_swipe_left_routes_to_previous_slide`, `test_camera_key_controls_lifecycle_not_slideshow`

### REQ-GP-07 Recognizer set

- Profile tests: `test_known_gestures_accepts_a_profile_inside_the_set`, `test_known_gestures_rejects_a_gesture_the_recognizer_does_not_emit`, `test_known_gestures_accepts_any_collection_type`, `test_known_gestures_given_as_a_string_is_a_programming_error`, `test_empty_known_gestures_rejects_every_binding`, `test_load_passes_known_gestures_through`
- Pipeline tests: `test_profile_binding_a_gesture_the_recognizer_never_emits_is_rejected`

### REQ-GP-08 No end, no stray keys

- Profile tests: `test_profile_bindings_are_read_only`, `test_profile_does_not_follow_later_edits_to_its_source`
- Control 01 tests: `test_ac03_end_is_the_only_esc_and_is_not_reachable_from_a_gesture`, `test_ac03_every_valid_binding_resolves_to_an_allowed_key`, `test_ac05_dispatch_fails_closed_if_bindings_are_corrupted`, `test_ac05_bindings_cannot_be_edited_or_replaced_from_outside`, `test_ac02_adapter_rejects_bad_commands_with_zero_keyboard_calls`

### REQ-GP-09 No regression

Not a single test. The evidence is the full Python suite, `ruff`, `bandit`, and the frontend lint, typecheck, test and build commands. Numbers are in `S4-R01-T3-Peer-Review-and-Regression.md` and the raw output is in `docs/sprint4/evidence/`.

## Not covered

| Item | Why |
|---|---|
| Live camera, real slideshow and real key presses | All tests use a fake keyboard library. Live behavior was not run |
| The profile UI and enrollment backend | Owned by Andres and Eric. No code from either was in the snapshot used here |
| The recognizer's real gesture set | Not passed to the loader yet, so REQ-GP-07 is only partly verified |
| Applying a profile from another thread | The coordinator is not designed for concurrent use and this was not examined |
| Python 3.11 and Node 20 as pinned for CI | The local runs used Python 3.12 and Node 22 |
