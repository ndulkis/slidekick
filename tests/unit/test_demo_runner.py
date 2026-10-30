"""Runner keyboard controls and failure behavior without real camera imports."""

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock

from slidekick.contracts import SessionState
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.session_coordinator import SessionCoordinator

spec = importlib.util.spec_from_file_location(
    "gesture_demo_runner",
    Path(__file__).resolve().parents[2] / "scripts/run_gesture_control.py",
)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
# The runner only needs run_camera as an imported name; keep hardware libraries
# (MediaPipe/OpenCV) out of collection so this test also works on CI runners.
original_camera = sys.modules.get("slidekick.recognition.camera")
fake_camera = types.ModuleType("slidekick.recognition.camera")
fake_camera.run_camera = Mock()
try:
    sys.modules["slidekick.recognition.camera"] = fake_camera
    spec.loader.exec_module(runner)
finally:
    if original_camera is None:
        sys.modules.pop("slidekick.recognition.camera", None)
    else:
        sys.modules["slidekick.recognition.camera"] = original_camera


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
    assert (
        session.handle_event({"event_type": "gesture", "gesture": "swipe_right"})
        is False
    )
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
