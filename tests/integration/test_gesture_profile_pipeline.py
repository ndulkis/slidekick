"""S4-R01-T2: profile file to keystroke, with the real adapter and a fake keyboard.

Profile file, loader, session coordinator, controller, keyboard adapter and the fake
pyautogui from conftest, in the order a real run would use them.
"""

import json
from unittest import mock

import pytest

from slidekick.command_policy import InvalidGestureBindingError
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.gesture_profile import InvalidProfileError, load_profile
from slidekick.recognition.events import create_gesture_event
from slidekick.session_coordinator import ProfileChangeError, SessionCoordinator

RECOGNIZED = {"swipe_right", "swipe_left", "palm_open", "fist"}

PRESENTER = {
    "version": 1,
    "name": "presenter",
    "bindings": {
        "swipe_right": "next",
        "swipe_left": "previous",
        "palm_open": "pause",
        "fist": "resume",
    },
}


def build(adapters):
    adapter = adapters.KeyboardPresentationAdapter()
    return SessionCoordinator(gestures=GestureCommandController(adapter=adapter))


def gesture(name):
    return create_gesture_event(name, 0.95, 100.0)


def profile_file(tmp_path, data):
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_profile_file_drives_the_keyboard_through_every_layer(
    adapters, fake_pyautogui, tmp_path
):
    session = build(adapters)
    profile = load_profile(profile_file(tmp_path, PRESENTER), known_gestures=RECOGNIZED)

    session.apply_profile(profile)
    session.start()

    for name, key in [
        ("swipe_right", "right"),
        ("swipe_left", "left"),
        ("palm_open", "b"),
        ("fist", "b"),
    ]:
        fake_pyautogui.reset_mock()
        assert session.handle_event(gesture(name)) is True
        assert fake_pyautogui.mock_calls == [mock.call.press(key)]


def test_nothing_reaches_the_keyboard_until_the_session_is_running(
    adapters, fake_pyautogui, tmp_path
):
    session = build(adapters)
    session.apply_profile(load_profile(profile_file(tmp_path, PRESENTER)))

    for name in PRESENTER["bindings"]:
        assert session.handle_event(gesture(name)) is False
    session.start()
    session.pause()
    for name in PRESENTER["bindings"]:
        assert session.handle_event(gesture(name)) is False

    assert fake_pyautogui.mock_calls == []


def test_changing_profile_mid_session_needs_a_pause(adapters, fake_pyautogui, tmp_path):
    session = build(adapters)
    session.start()
    profile = load_profile(profile_file(tmp_path, PRESENTER))

    with pytest.raises(ProfileChangeError):
        session.apply_profile(profile)
    assert session.handle_event(gesture("palm_open")) is False

    session.pause()
    session.apply_profile(profile)
    session.resume()

    assert session.handle_event(gesture("palm_open")) is True
    assert fake_pyautogui.mock_calls == [mock.call.press("b")]


@pytest.mark.parametrize(
    "bindings",
    [
        {"swipe_right": "end"},
        {"swipe_right": "ctrl+w"},
        {"swipe_right": "alt+f4"},
        {"Swipe Right": "next"},
        {"swipe_right": ["next"]},
    ],
    ids=repr,
)
def test_bad_profile_file_is_rejected_at_load_and_the_old_profile_keeps_working(
    adapters, fake_pyautogui, tmp_path, bindings
):
    session = build(adapters)
    session.start()
    bad = dict(PRESENTER, bindings=bindings)

    with pytest.raises(InvalidProfileError):
        load_profile(profile_file(tmp_path, bad))

    assert fake_pyautogui.mock_calls == []
    assert session.handle_event(gesture("swipe_right")) is True
    assert fake_pyautogui.mock_calls == [mock.call.press("right")]


def test_profile_binding_a_gesture_the_recognizer_never_emits_is_rejected(
    adapters, fake_pyautogui, tmp_path
):
    data = dict(PRESENTER, bindings={"wave": "next"})

    with pytest.raises(InvalidProfileError, match="does not emit"):
        load_profile(profile_file(tmp_path, data), known_gestures=RECOGNIZED)

    assert fake_pyautogui.mock_calls == []


def test_controller_still_refuses_unvalidated_bindings_handed_to_it_directly(
    adapters, fake_pyautogui
):
    session = build(adapters)

    with pytest.raises(InvalidGestureBindingError):
        session.gestures.set_gesture_bindings({"swipe_right": "end"})

    session.start()
    assert session.handle_event(gesture("swipe_right")) is True
    assert fake_pyautogui.mock_calls == [mock.call.press("right")]
