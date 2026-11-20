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


def test_quit_while_idle_exits_without_opening_the_camera():
    backend = Backend(SessionCoordinator())
    runner.run_camera = Mock(side_effect=AssertionError("camera must stay off"))

    backend.quit()
    runner.run_one_session(backend)  # returns instead of blocking

    assert backend.state is SessionState.IDLE
    assert backend.camera == "off"


def test_dashboard_opens_in_an_app_window_when_chrome_is_available(
    monkeypatch, tmp_path
):
    # A stand-in checkout with the frontend installed, so the test does not
    # depend on `npm ci` having run (the Python CI job never runs it).
    vite = tmp_path / "frontend/node_modules/vite/bin/vite.js"
    vite.parent.mkdir(parents=True)
    vite.touch()
    monkeypatch.setattr(runner, "REPO_ROOT", tmp_path)

    launched = []
    monkeypatch.setattr(
        runner.subprocess, "Popen", lambda cmd, **kw: launched.append(cmd)
    )
    monkeypatch.setattr(runner.shutil, "which", lambda name: "/usr/bin/node")
    monkeypatch.setattr(runner, "wait_for_port", lambda port: True)

    monkeypatch.setattr(runner, "find_app_browser", lambda: "/chrome")
    assert len(runner.start_dashboard("/tmp/profile")) == 2
    vite, browser = launched
    assert "--open" not in vite
    assert browser[:3] == [
        "/chrome",
        "--app=http://localhost:5173/session",
        "--user-data-dir=/tmp/profile",
    ]

    # No Chrome or Edge: fall back to a tab in the default browser.
    launched.clear()
    monkeypatch.setattr(runner, "find_app_browser", lambda: None)
    assert len(runner.start_dashboard("/tmp/profile")) == 1
    assert launched[0][-2:] == ["--open", "/session"]


def test_dashboard_is_skipped_when_the_frontend_is_not_installed(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(runner.subprocess, "Popen", Mock(side_effect=AssertionError))
    assert runner.start_dashboard("/tmp/profile") == []
