"""TEST-2: session / recognition event / command integration without hardware."""

import pytest

from slidekick.contracts import SessionState
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.session_controller import InvalidTransitionError
from slidekick.session_coordinator import PresentationCommandError, SessionCoordinator


class FakeAdapter:
    def __init__(self):
        self.calls = []
        self.should_fail = False

    def _record(self, command):
        if self.should_fail:
            raise OSError("simulated keyboard failure")
        self.calls.append(command)
        return True

    def next_slide(self):
        return self._record("next")

    def previous_slide(self):
        return self._record("previous")

    def pause_presentation(self):
        return self._record("blank")

    def resume_presentation(self):
        return self._record("unblank")

    def end_presentation(self):
        return self._record("escape")


def make_system(bindings=None):
    adapter = FakeAdapter()
    gesture_controller = GestureCommandController(
        adapter=adapter, gesture_bindings=bindings
    )
    return SessionCoordinator(gestures=gesture_controller), adapter


def gesture(name):
    return {"event_type": "gesture", "gesture": name, "confidence": 0.96}


def test_recognition_events_reach_adapter_only_while_running():
    session, adapter = make_system()
    assert session.handle_event(gesture("swipe_right")) is False
    session.start()
    assert session.handle_event(gesture("swipe_right")) is True
    assert session.handle_event(gesture("swipe_left")) is True
    session.pause()
    assert session.handle_event(gesture("swipe_right")) is False
    assert adapter.calls == ["next", "previous"]
    session.resume()
    assert session.handle_event(gesture("swipe_right")) is True
    session.end()
    assert session.handle_event(gesture("swipe_left")) is False
    session.start()
    assert session.handle_event(gesture("swipe_left")) is True
    assert adapter.calls == ["next", "previous", "next", "previous"]


@pytest.mark.parametrize("event", [
    None, {}, "swipe_right", {"event_type": "landmarks"},
    {"event_type": "gesture", "gesture": None},
    {"event_type": "gesture", "gesture": "unknown"},
])
def test_unrecognized_or_malformed_camera_events_cannot_send_keys(event):
    session, adapter = make_system()
    session.start()
    assert session.handle_event(event) is False
    assert adapter.calls == []


def test_session_pause_resume_and_end_never_invoke_slideshow_shortcuts():
    session, adapter = make_system()
    session.start()
    session.pause()
    with pytest.raises(InvalidTransitionError):
        session.end()  # documented paused -> ended restriction
    assert session.state is SessionState.PAUSED
    session.resume()
    session.end()
    assert adapter.calls == []  # no B or ESC injected by lifecycle controls


def test_custom_mapping_routes_through_coordinator_and_rejects_unknown_command():
    session, adapter = make_system({
        "swipe_right": "previous", "swipe_left": "arbitrary_hotkey"
    })
    session.start()
    assert session.handle_event(gesture("swipe_right")) is True
    with pytest.raises(PresentationCommandError, match="not executed"):
        session.handle_event(gesture("swipe_left"))
    assert adapter.calls == ["previous"]


def test_adapter_failure_surfaces_and_next_gesture_recovers():
    session, adapter = make_system()
    session.start()
    adapter.should_fail = True
    with pytest.raises(PresentationCommandError, match="simulated keyboard failure"):
        session.handle_event(gesture("swipe_right"))
    assert session.last_error
    assert adapter.calls == []
    adapter.should_fail = False
    assert session.handle_event(gesture("swipe_right")) is True
    assert session.last_error is None
    assert adapter.calls == ["next"]
