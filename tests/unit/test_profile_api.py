"""Integration of validated gesture profiles with the dashboard API."""
from slidekick.api_server import Backend, create_app
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.session_coordinator import SessionCoordinator

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
        self.calls.append("pause")
        return True

    def resume_presentation(self):
        self.calls.append("resume")
        return True

def test_switch_paused_and_reject_running(tmp_path):
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "a.json").write_text('{"version":1,"name":"a","bindings":{"swipe_right":"next"}}')
    (profiles / "b.json").write_text('{"version":1,"name":"b","bindings":{"swipe_right":"previous"}}')
    adapter = Adapter()
    backend = Backend(SessionCoordinator(gestures=GestureCommandController(adapter)), profile_dir=profiles)
    client = create_app(backend).test_client()
    assert [p["name"] for p in client.get("/api/profiles").json["profiles"]] == ["a", "b"]
    assert client.put("/api/profiles/active", json={"name":"a"}).status_code == 200
    client.post("/api/session/start", json={})
    event = {"event_type":"gesture", "gesture":"swipe_right"}
    assert backend.handle_event(event)
    assert adapter.calls == ["next"]
    assert client.put("/api/profiles/active", json={"name":"b"}).status_code == 409
    assert backend.coordinator.profile_name == "a"
    client.post("/api/session/pause", json={})
    assert client.put("/api/profiles/active", json={"name":"b"}).status_code == 200
    assert not backend.handle_event(event)
    client.post("/api/session/resume", json={})
    assert backend.handle_event(event)
    assert adapter.calls == ["next", "previous"]
    assert client.put("/api/profiles/active", json={"name":"nonexistent"}).status_code == 400
    assert backend.coordinator.profile_name == "b"
