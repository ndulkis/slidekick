"""The `slidekick` runner starts the camera per session, without real camera imports."""

import importlib
import sys
import types
from unittest.mock import Mock

from slidekick.api_server import Backend
from slidekick.contracts import SessionState
from slidekick.session_coordinator import SessionCoordinator

# The runner only needs run_camera as an imported name; keep hardware libraries
# (MediaPipe/OpenCV) out of collection so this test also works on CI runners.
original_camera = sys.modules.get("slidekick.recognition.camera")
fake_camera = types.ModuleType("slidekick.recognition.camera")
fake_camera.run_camera = Mock()
try:
    sys.modules["slidekick.recognition.camera"] = fake_camera
    runner = importlib.import_module("slidekick.app")
finally:
    if original_camera is None:
        sys.modules.pop("slidekick.recognition.camera", None)
    else:
        sys.modules["slidekick.recognition.camera"] = original_camera


def test_camera_runs_only_while_a_session_is_live():
    backend = Backend(SessionCoordinator())
    seen = {}

    def camera(handler, on_ready, should_stop, **kwargs):
        on_ready()
        seen["camera"] = backend.camera
        seen["stop_while_running"] = should_stop()
        backend.end()  # the dashboard's End button
        seen["stop_after_end"] = should_stop()

    runner.run_camera = camera
    backend.start()  # the dashboard's Start button
    runner.run_one_session(backend)

    assert seen == {
        "camera": "ready",
        "stop_while_running": False,
        "stop_after_end": True,
    }
    assert backend.camera == "off"
    assert backend.state is SessionState.ENDED
