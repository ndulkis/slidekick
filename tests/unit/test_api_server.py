"""Dashboard HTTP API over a real SessionCoordinator with a fake adapter."""

import json

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
        "camera": "starting",
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
