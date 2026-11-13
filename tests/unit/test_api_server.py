"""Dashboard HTTP API over a real SessionCoordinator with a fake adapter."""

import json
import time

from slidekick.api_server import Backend, create_app
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.session_coordinator import SessionCoordinator

CALIBRATION = {
    "min_displacement": 0.12,
    "max_swipe_duration": 2.0,
    "confidence_threshold": 0.6,
    "swipe_cooldown": 1.0,
}


class Adapter:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def next_slide(self):
        self.calls.append("next")
        return self.ok

    def previous_slide(self):
        self.calls.append("previous")
        return self.ok

    pause_presentation = resume_presentation = previous_slide


def make_client(tmp_path, adapter=None):
    adapter = adapter or Adapter()
    coordinator = SessionCoordinator(gestures=GestureCommandController(adapter))
    backend = Backend(coordinator, calibration_path=tmp_path / "calibration.json")
    return create_app(backend).test_client(), backend, adapter


def post(client, path, body=None, **kwargs):
    return client.post(path, json=body or {}, **kwargs)


def swipe(backend, confidence=0.9):
    return backend.handle_event(
        {"event_type": "gesture", "gesture": "swipe_right", "confidence": confidence}
    )


def test_session_lifecycle_and_gestures(tmp_path):
    client, backend, adapter = make_client(tmp_path)
    assert client.get("/api/session").json == {
        "state": "idle",
        "camera": "off",
        "last_gesture": None,
        "presentation_error": None,
    }

    res = post(client, "/api/session/start")
    assert res.status_code == 200
    assert res.json["event"] == {
        "type": "session_started",
        "previous_state": "idle",
        "new_state": "running",
        "use_case": "UC10",
    }

    assert swipe(backend)
    assert client.get("/api/session").json["last_gesture"] == {
        "id": 1,
        "gesture": "next",
        "confidence": 0.9,
    }

    # Pausing clears the gesture and stops commands.
    post(client, "/api/session/pause")
    assert client.get("/api/session").json["last_gesture"] is None
    assert not swipe(backend)

    # Paused -> ended is not allowed.
    res = post(client, "/api/session/end")
    assert res.status_code == 409
    assert res.json["state"] == "paused"

    assert post(client, "/api/session/bogus").status_code == 404
    assert adapter.calls == ["next"]


def test_failed_keystroke_is_reported_not_raised(tmp_path):
    client, backend, _ = make_client(tmp_path, Adapter(ok=False))
    post(client, "/api/session/start")
    assert swipe(backend) is False
    assert client.get("/api/session").json["presentation_error"]


def test_rejects_cross_site_and_foreign_host_requests(tmp_path):
    client, backend, _ = make_client(tmp_path)
    # A plain form/text POST (no CORS preflight) must not change state.
    res = client.post("/api/session/start", data="x", content_type="text/plain")
    assert res.status_code == 415
    res = post(client, "/api/session/start", headers={"Host": "evil.example:5001"})
    assert res.status_code == 403
    assert backend.state.value == "idle"


def test_calibration_round_trip_and_persistence(tmp_path):
    client, backend, _ = make_client(tmp_path)
    assert client.put("/api/calibration", json=CALIBRATION).json == CALIBRATION
    assert backend.calibration.min_displacement == 0.12
    assert json.loads((tmp_path / "calibration.json").read_text()) == CALIBRATION

    # A restarted backend loads the saved file.
    _, restarted, _ = make_client(tmp_path)
    assert restarted.calibration.swipe_cooldown == 1.0


def test_calibration_validation(tmp_path):
    client, backend, _ = make_client(tmp_path)
    bad = [
        {**CALIBRATION, "swipe_cooldown": -1},
        {**CALIBRATION, "swipe_cooldown": True},
        {**CALIBRATION, "stationary_threshold": 0.1},
        {"min_displacement": 0.1},
        # Must stay below ideal_displacement (0.20).
        {**CALIBRATION, "min_displacement": 0.2},
    ]
    for body in bad:
        assert client.put("/api/calibration", json=body).status_code == 400, body
    assert backend.calibration.min_displacement == 0.10
    assert not (tmp_path / "calibration.json").exists()


def test_camera_follows_the_session(tmp_path):
    client, backend, _ = make_client(tmp_path)
    assert not backend._started.is_set()

    # Starting a session asks for the camera.
    post(client, "/api/session/start")
    assert backend._started.is_set()
    assert backend.camera == "starting"
    assert not backend.should_stop_camera()
    backend.camera_ready()

    # Ending it stops the camera loop, which reports back.
    post(client, "/api/session/end")
    assert backend.should_stop_camera()
    backend.camera_stopped()
    assert backend.camera == "off"
    assert not backend._started.is_set()


def test_camera_failure_or_closed_window_ends_the_session(tmp_path):
    client, backend, _ = make_client(tmp_path)

    # Camera never became ready.
    post(client, "/api/session/start")
    backend.camera_stopped()
    assert client.get("/api/session").json["camera"] == "error"
    assert backend.state.value == "ended"

    # Camera window closed while paused. A new start clears the old error.
    post(client, "/api/session/start")
    assert backend.camera == "starting"
    backend.camera_ready()
    post(client, "/api/session/pause")
    backend.camera_stopped()
    assert backend.camera == "off"
    assert backend.state.value == "ended"


def test_camera_stream_serves_frames_and_ends_when_the_camera_stops(tmp_path):
    client, backend, _ = make_client(tmp_path)
    backend.set_frame(b"JPEG1")

    res = client.get("/api/camera")
    assert res.mimetype == "multipart/x-mixed-replace"
    assert res.headers["Cross-Origin-Resource-Policy"] == "same-origin"

    frames = backend.frames(timeout=0.05)
    assert next(frames) == b"JPEG1"
    backend.set_frame(b"JPEG2")
    assert next(frames) == b"JPEG2"
    # No new frame: the stream ends instead of repeating the old one.
    assert list(frames) == []

    # A stopped camera leaves no stale frame for the next session's stream.
    backend.camera_stopped()
    assert list(backend.frames(timeout=0.05)) == []


def test_quit_stops_the_camera_and_wakes_an_idle_app(tmp_path):
    client, backend, _ = make_client(tmp_path)

    # Cross-site requests cannot quit the app.
    res = client.post("/api/quit", data="x", content_type="text/plain")
    assert res.status_code == 415
    assert not backend.quitting

    post(client, "/api/session/start")
    backend.camera_ready()
    backend._started.clear()  # as if the app loop were idle
    assert post(client, "/api/quit").json == {"quitting": True}
    assert backend.should_stop_camera()
    assert backend._started.is_set()

    # The camera loop exits and ends the live session on the way out.
    backend.camera_stopped()
    assert backend.state.value == "ended"


def test_closing_the_dashboard_window_quits_but_a_reload_does_not(tmp_path):
    _, backend, _ = make_client(tmp_path)
    backend.quit_when_dashboard_closes = True

    # Reload: the old page goes, a new one connects within the grace period.
    backend.dashboard_connected()
    backend.dashboard_disconnected(grace=0.05)
    backend.dashboard_connected()
    time.sleep(0.15)
    assert not backend.quitting

    # Closed: nothing reconnects.
    backend.dashboard_disconnected(grace=0.05)
    time.sleep(0.15)
    assert backend.quitting


def test_a_browser_tab_closing_never_quits(tmp_path):
    _, backend, _ = make_client(tmp_path)  # quit_when_dashboard_closes off
    backend.dashboard_connected()
    backend.dashboard_disconnected(grace=0.01)
    time.sleep(0.1)
    assert not backend.quitting


def test_alive_stream_counts_the_dashboard_while_connected(tmp_path):
    client, backend, _ = make_client(tmp_path)
    res = client.get("/api/alive", buffered=False)
    assert res.mimetype == "text/event-stream"
    chunks = iter(res.response)
    assert next(chunks) == b"retry: 1000\n\n"
    assert backend._dashboards == 1
    res.close()  # the browser went away
    assert backend._dashboards == 0
