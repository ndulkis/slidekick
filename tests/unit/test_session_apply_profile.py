"""S4-R01-T2: applying a gesture profile through the session coordinator."""

import pytest

from slidekick.command_policy import InvalidGestureBindingError
from slidekick.contracts import SessionState
from slidekick.gesture_command_controller import (
    DEFAULT_GESTURE_BINDINGS,
    GestureCommandController,
)
from slidekick.gesture_profile import GestureProfile, default_profile
from slidekick.recognition.events import create_gesture_event
from slidekick.session_coordinator import ProfileChangeError, SessionCoordinator


class FakeAdapter:
    def __init__(self):
        self.calls = []

    def _record(self, name):
        self.calls.append(name)
        return True

    def next_slide(self):
        return self._record("next")

    def previous_slide(self):
        return self._record("previous")

    def pause_presentation(self):
        return self._record("pause")

    def resume_presentation(self):
        return self._record("resume")

    def end_presentation(self):
        return self._record("end")


PRESENTER = GestureProfile(
    name="presenter",
    bindings={"fist": "pause", "palm_open": "resume", "swipe_left": "next"},
)


def build():
    adapter = FakeAdapter()
    coordinator = SessionCoordinator(gestures=GestureCommandController(adapter=adapter))
    return coordinator, adapter


def gesture(name):
    return create_gesture_event(name, 0.9, 1.0)


def in_state(state):
    coordinator, adapter = build()
    if state in (SessionState.RUNNING, SessionState.PAUSED, SessionState.ENDED):
        coordinator.start()
    if state is SessionState.PAUSED:
        coordinator.pause()
    if state is SessionState.ENDED:
        coordinator.end()
    assert coordinator.state is state
    return coordinator, adapter


@pytest.mark.parametrize(
    "state", [SessionState.IDLE, SessionState.PAUSED, SessionState.ENDED]
)
def test_profile_can_be_applied_when_the_session_is_not_running(state):
    coordinator, _ = in_state(state)

    coordinator.apply_profile(PRESENTER)

    assert dict(coordinator.gestures.gesture_bindings) == dict(PRESENTER.bindings)
    assert coordinator.profile_name == "presenter"
    assert coordinator.state is state


def test_profile_is_refused_while_running_and_nothing_changes():
    coordinator, adapter = in_state(SessionState.RUNNING)

    with pytest.raises(ProfileChangeError, match="Pause the session"):
        coordinator.apply_profile(PRESENTER)

    assert dict(coordinator.gestures.gesture_bindings) == dict(DEFAULT_GESTURE_BINDINGS)
    assert coordinator.profile_name is None
    assert coordinator.state is SessionState.RUNNING
    assert adapter.calls == []


@pytest.mark.parametrize(
    "not_a_profile",
    [
        None,
        {},
        {"swipe_right": "next"},
        "presenter",
        5,
        [PRESENTER],
        PRESENTER.bindings,
    ],
    ids=repr,
)
def test_only_a_gesture_profile_is_accepted(not_a_profile):
    coordinator, _ = build()

    with pytest.raises(ProfileChangeError, match="needs a GestureProfile"):
        coordinator.apply_profile(not_a_profile)

    assert dict(coordinator.gestures.gesture_bindings) == dict(DEFAULT_GESTURE_BINDINGS)


def test_a_rejected_change_keeps_the_previous_profile_name_and_bindings():
    coordinator, _ = build()
    coordinator.apply_profile(PRESENTER)

    class Rejecting(GestureCommandController):
        def set_gesture_bindings(self, gesture_bindings):
            raise InvalidGestureBindingError("controller said no")

    coordinator.gestures.set_gesture_bindings = Rejecting().set_gesture_bindings

    with pytest.raises(InvalidGestureBindingError, match="controller said no"):
        coordinator.apply_profile(default_profile())

    assert coordinator.profile_name == "presenter"


def test_new_bindings_drive_commands_after_resume_and_old_ones_stop():
    coordinator, adapter = build()
    coordinator.start()
    assert coordinator.handle_event(gesture("swipe_right")) is True

    coordinator.pause()
    coordinator.apply_profile(PRESENTER)
    coordinator.resume()

    assert coordinator.handle_event(gesture("swipe_right")) is False
    assert coordinator.handle_event(gesture("swipe_left")) is True
    assert coordinator.handle_event(gesture("fist")) is True
    assert coordinator.handle_event(gesture("palm_open")) is True
    assert adapter.calls == ["next", "next", "pause", "resume"]


@pytest.mark.parametrize(
    "state", [SessionState.IDLE, SessionState.PAUSED, SessionState.ENDED]
)
def test_session_restrictions_still_hold_after_a_profile_is_applied(state):
    coordinator, adapter = in_state(state)
    coordinator.apply_profile(PRESENTER)

    for name in ("fist", "palm_open", "swipe_left", "swipe_right"):
        assert coordinator.handle_event(gesture(name)) is False

    assert adapter.calls == []


def test_applying_the_default_profile_restores_the_default_bindings():
    coordinator, adapter = build()
    coordinator.apply_profile(PRESENTER)
    coordinator.apply_profile(default_profile())
    coordinator.start()

    assert coordinator.profile_name == "default"
    assert coordinator.handle_event(gesture("swipe_right")) is True
    assert coordinator.handle_event(gesture("fist")) is False
    assert adapter.calls == ["next"]


def test_applying_a_profile_never_calls_the_adapter():
    coordinator, adapter = in_state(SessionState.PAUSED)

    coordinator.apply_profile(PRESENTER)

    assert adapter.calls == []
