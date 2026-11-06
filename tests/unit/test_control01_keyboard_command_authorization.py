"""SOC 2 Control 01, Keyboard Command Authorization (CC6.1).

Tests for S4-SOC2-C01-T2. Each test names the acceptance criterion it supports, AC-01
to AC-06, so results map straight into the evidence report.

Where it matters these tests run the real KeyboardPresentationAdapter against the fake
pyautogui from conftest, so "zero keyboard calls" means zero calls on the keyboard
library itself and not just zero calls on a test double.
"""

from unittest import mock

import pytest

from slidekick.command_policy import (
    APPROVED_COMMANDS,
    GESTURE_ID_PATTERN,
    PROFILE_BINDABLE_COMMANDS,
    InvalidGestureBindingError,
    validate_gesture_bindings,
)
from slidekick.contracts import SessionState
from slidekick.gesture_command_controller import (
    DEFAULT_GESTURE_BINDINGS,
    GestureCommandController,
)
from slidekick.recognition.events import create_gesture_event
from slidekick.session_coordinator import SessionCoordinator

# The documented key for each command. This is the contract the adapter must meet.
DOCUMENTED_KEYS = {
    "next": "right",
    "previous": "left",
    "pause": "b",
    "resume": "b",
}
ALLOWED_KEYS = set(DOCUMENTED_KEYS.values())


def build(adapters, bindings=None):
    """Real session, real controller, real keyboard adapter, fake pyautogui."""
    adapter = adapters.KeyboardPresentationAdapter()
    controller = GestureCommandController(adapter=adapter, gesture_bindings=bindings)
    return SessionCoordinator(gestures=controller), controller


def gesture(name):
    return create_gesture_event(name, 0.95, 100.0)


def assert_no_keyboard_activity(fake_pyautogui):
    """Nothing at all touched pyautogui: no press, hotkey, write or keyDown."""
    assert fake_pyautogui.mock_calls == []


# ---------------------------------------------------------------------------
# AC-01  Allowlist and gesture-to-action contract
# ---------------------------------------------------------------------------


def test_ac01_policy_sets_are_consistent():
    assert PROFILE_BINDABLE_COMMANDS <= APPROVED_COMMANDS
    assert APPROVED_COMMANDS - PROFILE_BINDABLE_COMMANDS == {"end"}
    assert isinstance(APPROVED_COMMANDS, frozenset)
    assert isinstance(PROFILE_BINDABLE_COMMANDS, frozenset)


def test_ac01_default_bindings_only_use_bindable_commands():
    assert set(DEFAULT_GESTURE_BINDINGS.values()) <= PROFILE_BINDABLE_COMMANDS
    assert validate_gesture_bindings(DEFAULT_GESTURE_BINDINGS) == dict(
        DEFAULT_GESTURE_BINDINGS
    )


def test_ac01_default_bindings_cannot_be_edited_in_place():
    with pytest.raises(TypeError):
        DEFAULT_GESTURE_BINDINGS["swipe_right"] = "end"
    assert DEFAULT_GESTURE_BINDINGS["swipe_right"] == "next"


@pytest.mark.parametrize("command", sorted(APPROVED_COMMANDS))
def test_ac01_adapter_command_set_matches_policy(adapters, fake_pyautogui, command):
    """Drift check: the adapter accepts exactly the bindable commands, and refuses end."""
    adapter = adapters.KeyboardPresentationAdapter()
    result = adapter.execute_command(command)

    if command in PROFILE_BINDABLE_COMMANDS:
        assert result["status"] == "success"
        fake_pyautogui.press.assert_called_once_with(DOCUMENTED_KEYS[command])
    else:
        assert result["status"] == "error"
        assert_no_keyboard_activity(fake_pyautogui)


# ---------------------------------------------------------------------------
# AC-02  Unsupported commands produce zero keyboard calls
# ---------------------------------------------------------------------------

BAD_COMMANDS = [
    "jump",
    "",
    "   ",
    "\t\n",
    None,
    0,
    123,
    1.5,
    True,
    b"next",
    ["next"],
    ("next",),
    {"command": "next"},
    object(),
    "end",
    "esc",
    "escape",
    "b",
    "right",
    "left",
    "ctrl+alt+delete",
    "alt+f4",
    "win+d",
    "next;previous",
    "next previous",
    "next\nprevious",
    "next\x00",
    "next'; DROP TABLE slides;--",
    "$(next)",
    "../next",
    "nxt",
    "nextt",
    "\u202enext",
    "\uff4e\uff45\uff58\uff54",
]


@pytest.mark.parametrize("bad", BAD_COMMANDS, ids=lambda value: repr(value)[:30])
def test_ac02_adapter_rejects_bad_commands_with_zero_keyboard_calls(
    adapters, fake_pyautogui, bad
):
    adapter = adapters.KeyboardPresentationAdapter()
    result = adapter.execute_command(bad)

    assert result["status"] == "error"
    assert result["error"] == "Invalid Command"
    assert_no_keyboard_activity(fake_pyautogui)


# ---------------------------------------------------------------------------
# AC-03  Approved actions press only their documented key
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("command", "key"), sorted(DOCUMENTED_KEYS.items()))
def test_ac03_adapter_presses_only_the_documented_key(
    adapters, fake_pyautogui, command, key
):
    adapter = adapters.KeyboardPresentationAdapter()

    assert adapter.execute_command(command) == {"status": "success", "command": command}
    assert fake_pyautogui.mock_calls == [mock.call.press(key)]


def test_ac03_adapter_normalizes_case_and_spaces_without_extra_keys(
    adapters, fake_pyautogui
):
    adapter = adapters.KeyboardPresentationAdapter()

    assert adapter.execute_command("  NeXt ")["status"] == "success"
    assert fake_pyautogui.mock_calls == [mock.call.press("right")]


@pytest.mark.parametrize(
    ("gesture_name", "key"),
    [("swipe_right", "right"), ("swipe_left", "left")],
)
def test_ac03_gesture_to_key_end_to_end(adapters, fake_pyautogui, gesture_name, key):
    """G4: recognition event, session gate, controller mapping, adapter, keyboard."""
    session, _ = build(adapters)
    session.start()

    assert session.handle_event(gesture(gesture_name)) is True
    assert fake_pyautogui.mock_calls == [mock.call.press(key)]


def test_ac03_end_is_the_only_esc_and_is_not_reachable_from_a_gesture(
    adapters, fake_pyautogui
):
    """End to esc is evaluated on its own entry path, the adapter method."""
    adapter = adapters.KeyboardPresentationAdapter()
    assert adapter.end_presentation() is True
    assert fake_pyautogui.mock_calls == [mock.call.press("esc")]

    fake_pyautogui.reset_mock()
    with pytest.raises(InvalidGestureBindingError):
        build(adapters, {"swipe_right": "end"})
    assert_no_keyboard_activity(fake_pyautogui)


def test_ac03_every_valid_binding_resolves_to_an_allowed_key(adapters, fake_pyautogui):
    bindings = {f"gesture_{command}": command for command in PROFILE_BINDABLE_COMMANDS}
    session, _ = build(adapters, bindings)
    session.start()

    for name in bindings:
        assert session.handle_event(gesture(name)) is True

    pressed = {call.args[0] for call in fake_pyautogui.press.call_args_list}
    assert pressed <= ALLOWED_KEYS
    assert len(fake_pyautogui.press.call_args_list) == len(bindings)
    assert [call[0] for call in fake_pyautogui.mock_calls] == ["press"] * len(bindings)


# ---------------------------------------------------------------------------
# AC-04  Session state gates every recognition event
# ---------------------------------------------------------------------------


def make_in_state(adapters, state):
    session, controller = build(adapters)
    if state is SessionState.RUNNING:
        session.start()
    elif state is SessionState.PAUSED:
        session.start()
        session.pause()
    elif state is SessionState.ENDED:
        session.start()
        session.end()
    assert session.state is state
    return session, controller


@pytest.mark.parametrize(
    "state", [SessionState.IDLE, SessionState.PAUSED, SessionState.ENDED]
)
@pytest.mark.parametrize("name", ["swipe_right", "swipe_left"])
def test_ac04_inactive_session_blocks_every_gesture(
    adapters, fake_pyautogui, state, name
):
    session, _ = make_in_state(adapters, state)
    fake_pyautogui.reset_mock()

    assert session.handle_event(gesture(name)) is False
    assert_no_keyboard_activity(fake_pyautogui)


@pytest.mark.parametrize(
    ("name", "key"), [("swipe_right", "right"), ("swipe_left", "left")]
)
def test_ac04_running_session_dispatches_exactly_once(
    adapters, fake_pyautogui, name, key
):
    session, _ = make_in_state(adapters, SessionState.RUNNING)

    assert session.handle_event(gesture(name)) is True
    assert fake_pyautogui.mock_calls == [mock.call.press(key)]


def test_ac04_restart_after_end_routes_again(adapters, fake_pyautogui):
    session, _ = make_in_state(adapters, SessionState.ENDED)
    assert session.handle_event(gesture("swipe_right")) is False
    session.start()

    assert session.handle_event(gesture("swipe_right")) is True
    assert fake_pyautogui.mock_calls == [mock.call.press("right")]


def test_ac04_lifecycle_changes_press_no_keys(adapters, fake_pyautogui):
    """G3: session pause and resume are not the slideshow black-screen key."""
    session, _ = build(adapters)

    session.start()
    session.pause()
    session.resume()
    session.end()

    assert_no_keyboard_activity(fake_pyautogui)


MALFORMED_EVENTS = [
    None,
    "swipe_right",
    42,
    [],
    {},
    {"event_type": "gesture"},
    {"event_type": "gesture", "gesture": None},
    {"event_type": "gesture", "gesture": 7},
    {"event_type": "gesture", "gesture": ["swipe_right"]},
    {"event_type": "gesture", "gesture": {"swipe_right": 1}},
    {"event_type": "gesture", "gesture": b"swipe_right"},
    {"event_type": "gesture", "gesture": "Swipe_Right"},
    {"event_type": "gesture", "gesture": " swipe_right"},
    {"event_type": "gesture", "gesture": "swipe_right\n"},
    {"event_type": "Gesture", "gesture": "swipe_right"},
    {"event_type": "landmarks", "gesture": "swipe_right"},
    {"event_type": None, "gesture": "swipe_right"},
]


@pytest.mark.parametrize("event", MALFORMED_EVENTS, ids=lambda value: repr(value)[:40])
def test_ac04_malformed_events_while_running_press_nothing(
    adapters, fake_pyautogui, event
):
    session, _ = make_in_state(adapters, SessionState.RUNNING)

    assert session.handle_event(event) is False
    assert_no_keyboard_activity(fake_pyautogui)


# ---------------------------------------------------------------------------
# AC-05  Invalid mappings are rejected before use
# ---------------------------------------------------------------------------

BAD_COMMAND_VALUES = [
    "end",
    "esc",
    "escape",
    "ctrl+w",
    "alt+f4",
    "arbitrary_hotkey",
    "Next",
    " next",
    "next ",
    "",
    None,
    123,
    ["next"],
    {"next": 1},
    b"next",
]

BAD_GESTURE_IDS = [
    "",
    "Swipe_Right",
    "swipe right",
    "swipe-right",
    "1swipe",
    "_swipe",
    "swipe_right\n",
    "swipe_right; end",
    "swipe\u202eright",
    "x" * 65,
    123,
    None,
    ("swipe_right",),
    b"swipe_right",
]


@pytest.mark.parametrize(
    "value", BAD_COMMAND_VALUES, ids=lambda value: repr(value)[:30]
)
def test_ac05_bad_command_target_is_rejected_at_load(adapters, fake_pyautogui, value):
    with pytest.raises(InvalidGestureBindingError):
        build(adapters, {"swipe_right": value})
    assert_no_keyboard_activity(fake_pyautogui)


@pytest.mark.parametrize(
    "gesture_id", BAD_GESTURE_IDS, ids=lambda value: repr(value)[:30]
)
def test_ac05_bad_gesture_id_is_rejected_at_load(adapters, fake_pyautogui, gesture_id):
    with pytest.raises(InvalidGestureBindingError):
        build(adapters, {gesture_id: "next"})
    assert_no_keyboard_activity(fake_pyautogui)


@pytest.mark.parametrize(
    "not_a_mapping", [["swipe_right", "next"], "swipe_right=next", 5, True]
)
def test_ac05_non_mapping_profile_is_rejected(adapters, not_a_mapping):
    with pytest.raises(InvalidGestureBindingError, match="must be a mapping"):
        build(adapters, not_a_mapping)


def test_ac05_one_bad_entry_rejects_the_whole_profile_and_reports_all_problems():
    with pytest.raises(InvalidGestureBindingError) as caught:
        validate_gesture_bindings(
            {"swipe_right": "next", "swipe_left": "ctrl+w", "Bad Id": "previous"}
        )

    message = str(caught.value)
    assert "swipe_left" in message
    assert "Bad Id" in message
    assert "swipe_right" not in message


def test_ac05_error_text_does_not_echo_huge_or_non_string_values():
    huge = "x" * 5000
    with pytest.raises(InvalidGestureBindingError) as caught:
        validate_gesture_bindings({"swipe_right": huge, "swipe_left": ["secret"]})

    message = str(caught.value)
    assert len(message) < 400
    assert "secret" not in message
    assert "a list" in message


def test_ac05_empty_profile_is_valid_and_binds_nothing(adapters, fake_pyautogui):
    session, _ = build(adapters, {})
    session.start()

    assert session.handle_event(gesture("swipe_right")) is False
    assert_no_keyboard_activity(fake_pyautogui)


def test_ac05_approved_custom_profile_works_across_the_stack(adapters, fake_pyautogui):
    profile = {
        "swipe_right": "next",
        "swipe_left": "previous",
        "palm_open": "pause",
        "fist": "resume",
    }
    session, _ = build(adapters, profile)
    session.start()

    for name, expected_key in [
        ("swipe_right", "right"),
        ("swipe_left", "left"),
        ("palm_open", "b"),
        ("fist", "b"),
    ]:
        fake_pyautogui.reset_mock()
        assert session.handle_event(gesture(name)) is True
        assert fake_pyautogui.mock_calls == [mock.call.press(expected_key)]


def test_ac05_valid_gesture_ids_match_the_documented_pattern():
    for good in ["swipe_right", "a", "palm_open_2", "x" * 64]:
        assert GESTURE_ID_PATTERN.fullmatch(good)


def test_ac05_failed_update_keeps_previous_bindings_active(adapters, fake_pyautogui):
    session, controller = build(adapters)
    session.start()

    with pytest.raises(InvalidGestureBindingError):
        controller.set_gesture_bindings({"swipe_right": "end"})

    assert dict(controller.gesture_bindings) == dict(DEFAULT_GESTURE_BINDINGS)
    assert session.handle_event(gesture("swipe_right")) is True
    assert fake_pyautogui.mock_calls == [mock.call.press("right")]


def test_ac05_valid_update_replaces_bindings_atomically(adapters, fake_pyautogui):
    session, controller = build(adapters)
    session.start()

    controller.set_gesture_bindings({"fist": "pause"})

    assert session.handle_event(gesture("swipe_right")) is False
    assert_no_keyboard_activity(fake_pyautogui)
    assert session.handle_event(gesture("fist")) is True
    assert fake_pyautogui.mock_calls == [mock.call.press("b")]


def test_ac05_bindings_cannot_be_edited_or_replaced_from_outside(
    adapters, fake_pyautogui
):
    session, controller = build(adapters)
    session.start()

    with pytest.raises(TypeError):
        controller.gesture_bindings["fist"] = "end"
    with pytest.raises(AttributeError):
        controller.gesture_bindings = {"fist": "end"}

    assert session.handle_event(gesture("fist")) is False
    assert_no_keyboard_activity(fake_pyautogui)


@pytest.mark.parametrize("sneaky", ["end", "ctrl+w", ["next"], None, 123])
def test_ac05_dispatch_fails_closed_if_bindings_are_corrupted(
    adapters, fake_pyautogui, sneaky
):
    """Defense in depth: the dispatch check holds even if validation was bypassed."""
    session, controller = build(adapters)
    session.start()
    controller._gesture_bindings["fist"] = sneaky

    assert controller.handle_event(gesture("fist")) is False
    assert_no_keyboard_activity(fake_pyautogui)


# ---------------------------------------------------------------------------
# AC-02 and AC-04 together: the controller on its own
# ---------------------------------------------------------------------------


def test_controller_ignores_unbound_and_non_gesture_events_with_zero_calls(
    adapters, fake_pyautogui
):
    _, controller = build(adapters)

    for event in [
        gesture("unknown_gesture"),
        {"event_type": "landmarks", "landmarks": []},
        {"event_type": "gesture", "gesture": None},
        {"event_type": "gesture", "gesture": ["swipe_right"]},
    ]:
        assert controller.handle_event(event) is False

    assert_no_keyboard_activity(fake_pyautogui)
