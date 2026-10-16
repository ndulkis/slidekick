"""Sprint 3 integration coverage without a camera or native key presses."""

import pytest

from slidekick.contracts import SessionState
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.session_controller import InvalidTransitionError
from slidekick.session_coordinator import PresentationCommandError, SessionCoordinator


class RecordingAdapter:
    def __init__(self):
        self.calls = []
        self.fail = False
        self.reject = False

    def pause_presentation(self):
        return True

    def resume_presentation(self):
        return True

    def end_presentation(self):
        return True

    def next_slide(self):
        if self.fail:
            raise OSError("keyboard unavailable")
        if self.reject:
            return False
        self.calls.append("next")
        return True

    def previous_slide(self):
        self.calls.append("previous")
        return True


def create_coordinator():
    adapter = RecordingAdapter()
    return SessionCoordinator(
        gestures=GestureCommandController(adapter=adapter)
    ), adapter


def swipe(name="swipe_right"):
    return {"event_type": "gesture", "gesture": name, "confidence": 0.9}


def test_lifecycle_gates_both_gesture_directions():
    coordinator, adapter = create_coordinator()
    assert coordinator.state is SessionState.IDLE
    assert not coordinator.handle_event(swipe())
    coordinator.start()
    assert coordinator.handle_event(swipe())
    assert coordinator.handle_event(swipe("swipe_left"))
    coordinator.pause()
    assert not coordinator.handle_event(swipe())
    assert adapter.calls == ["next", "previous"]
    coordinator.resume()
    assert coordinator.handle_event(swipe())
    coordinator.end()
    assert not coordinator.handle_event(swipe())
    assert adapter.calls == ["next", "previous", "next"]
    coordinator.start()  # documented restart transition
    assert coordinator.handle_event(swipe())


def test_non_gestures_and_unbound_events_are_ignored():
    coordinator, adapter = create_coordinator()
    coordinator.start()
    for event in ({"event_type": "landmarks"}, swipe("unknown"), {}, None, "bad"):
        assert not coordinator.handle_event(event)
    assert adapter.calls == []


def test_invalid_transition_keeps_state_and_does_not_send_blank_key():
    coordinator, adapter = create_coordinator()
    with pytest.raises(InvalidTransitionError):
        coordinator.pause()
    coordinator.start()
    coordinator.pause()
    with pytest.raises(InvalidTransitionError):
        coordinator.end()  # paused -> ended is intentionally unsupported
    assert coordinator.state is SessionState.PAUSED
    assert adapter.calls == []


def test_adapter_error_is_surfaceable_and_recovers():
    coordinator, adapter = create_coordinator()
    coordinator.start()
    adapter.fail = True
    with pytest.raises(PresentationCommandError, match="keyboard unavailable"):
        coordinator.handle_event(swipe())
    assert coordinator.last_error
    adapter.fail = False
    assert coordinator.handle_event(swipe())
    assert coordinator.last_error is None


def test_adapter_false_result_surfaces_failure():
    coordinator, adapter = create_coordinator()
    coordinator.start()
    adapter.reject = True
    with pytest.raises(PresentationCommandError, match="not executed"):
        coordinator.handle_event(swipe())
