"""Runner keyboard controls and failure behavior without real camera imports."""

import importlib.util
from pathlib import Path

from slidekick.contracts import SessionState
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.session_coordinator import SessionCoordinator

spec = importlib.util.spec_from_file_location(
    "gesture_demo_runner", Path(__file__).resolve().parents[2] / "scripts/run_gesture_control.py"
)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class Adapter:
    def __init__(self):
        self.calls = []

    def next_slide(self):
        self.calls.append("next")
        return True

    def previous_slide(self):
        self.calls.append("previous")
        return True

    def pause_presentation(self):
        raise AssertionError("presentation must not be blanked")

    def resume_presentation(self):
        raise AssertionError("presentation must not be unblanked")

    def end_presentation(self):
        raise AssertionError("must not send ESC")


def test_camera_key_controls_lifecycle_not_slideshow():
    adapter = Adapter()
    session = SessionCoordinator(gestures=GestureCommandController(adapter))
    control = runner.make_key_handler(session)
    session.start()
    control(ord("p"))
    assert session.state is SessionState.PAUSED
    assert session.handle_event({"event_type": "gesture", "gesture": "swipe_right"}) is False
    control(ord("e"))  # paused -> ended is not allowed yet
    assert session.state is SessionState.PAUSED
    control(ord("r"))
    assert session.handle_event({"event_type": "gesture", "gesture": "swipe_right"})
    control(ord("e"))
    assert session.state is SessionState.ENDED
    assert not session.handle_event({"event_type": "gesture", "gesture": "swipe_right"})
    control(ord("s"))
    assert session.state is SessionState.RUNNING
    assert adapter.calls == ["next"]
