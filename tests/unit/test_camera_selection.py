"""Camera listing, selection by unique ID, and switching mid-session."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from slidekick import api_server
from slidekick.api_server import Backend, create_app
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.recognition import camera as camera_module
from slidekick.recognition.camera import (
    list_cameras,
    open_with_frame,
    resolve_camera,
)
from slidekick.session_coordinator import SessionCoordinator

BUILTIN = {"id": "6C70", "name": "MacBook Pro Camera", "index": 1, "phone": False}
PHONE = {"id": "3BA9", "name": "iPhone Camera", "index": 0, "phone": True}

PROFILER = {
    "SPCameraDataType": [
        {
            "_name": "MacBook Pro Camera",
            "spcamera_model-id": "MacBook Pro Camera",
            "spcamera_unique-id": "6C707041-05AC",
        },
        {
            "_name": "iPhone Camera",
            "spcamera_model-id": "iPhone16,2",
            "spcamera_unique-id": "3BA945EE-C94B",
        },
    ]
}


def test_list_cameras_numbers_by_unique_id_like_opencv(monkeypatch):
    monkeypatch.setattr(camera_module.sys, "platform", "darwin")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout=json.dumps(PROFILER)),
    )
    assert list_cameras() == [
        {"id": "3BA945EE-C94B", "name": "iPhone Camera", "index": 0, "phone": True},
        {
            "id": "6C707041-05AC",
            "name": "MacBook Pro Camera",
            "index": 1,
            "phone": False,
        },
    ]


def test_list_cameras_falls_back_to_one_default(monkeypatch):
    monkeypatch.setattr(camera_module.sys, "platform", "darwin")

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "system_profiler")

    monkeypatch.setattr(subprocess, "run", fail)
    assert [c["id"] for c in list_cameras()] == ["default"]


def test_resolve_camera():
    cameras = [PHONE, BUILTIN]
    assert resolve_camera(cameras, PHONE["id"]) is PHONE
    # Nothing selected, or the selected camera is gone: prefer the built-in.
    assert resolve_camera(cameras, None) is BUILTIN
    assert resolve_camera(cameras, "gone") is BUILTIN
    assert resolve_camera([PHONE], "gone") is PHONE
    assert resolve_camera([], "gone") is None


class FakeCapture:
    def __init__(self, opened=True, frames=True):
        self.opened = opened
        self.frames = frames
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        return self.frames, None

    def release(self):
        self.released = True


@pytest.mark.parametrize(
    ("opens", "frames", "works"),
    [(True, True, True), (False, False, False), (True, False, False)],
)
def test_open_with_frame_needs_a_frame(opens, frames, works):
    # (True, False): opens but never sends a frame, like a sleeping iPhone.
    new = FakeCapture(opened=opens, frames=frames)
    camera = open_with_frame(3, open_camera=lambda index: new, timeout=0.1)
    assert camera is (new if works else None)
    assert new.released is not works


@pytest.fixture
def cameras():
    """The connected cameras. Tests disconnect the phone by removing it."""
    return [PHONE, BUILTIN]


@pytest.fixture
def backend(tmp_path, monkeypatch, cameras):
    monkeypatch.setattr(api_server, "list_cameras", lambda: cameras)
    coordinator = SessionCoordinator(gestures=GestureCommandController())
    backend = Backend(coordinator, camera_path=tmp_path / "camera.json")
    return backend


def test_selection_is_saved_by_id_and_defaults_to_builtin(backend, tmp_path):
    client = create_app(backend).test_client()
    assert client.get("/api/cameras").json == {
        "cameras": [
            {"id": "3BA9", "name": "iPhone Camera"},
            {"id": "6C70", "name": "MacBook Pro Camera"},
        ],
        "selected": "6C70",
    }
    assert client.put("/api/cameras", json={"id": "nope"}).status_code == 400

    assert client.put("/api/cameras", json={"id": "3BA9"}).json["selected"] == "3BA9"
    assert json.loads((tmp_path / "camera.json").read_text()) == {"id": "3BA9"}
    assert api_server.load_camera_id(tmp_path / "camera.json") == "3BA9"


def test_missing_phone_at_start_falls_back_to_builtin(backend, cameras):
    backend.camera_id = "3BA9"
    cameras.remove(PHONE)
    backend.start()
    assert backend.get_camera() is BUILTIN


def test_switch_mid_session_and_revert_on_failure(backend):
    backend.start()
    backend.camera_ready()
    assert backend.get_camera() is BUILTIN

    backend.set_camera({"id": "3BA9"})
    # The old camera keeps streaming while the phone opens.
    assert backend.camera == "ready"
    assert backend.status()["camera_id"] == "3BA9"
    assert backend.get_camera() is PHONE

    backend.camera_switch_failed()
    status = backend.status()
    assert status["camera"] == "ready"
    assert status["camera_message"] == (
        "Couldn't switch to iPhone Camera, still using MacBook Pro Camera."
    )
    assert backend.get_camera() is BUILTIN
    assert backend.camera_id == "6C70"


def test_second_choice_during_a_switch_keeps_the_open_camera(backend, cameras):
    usb = {"id": "AAAA", "name": "USB Camera", "index": 2, "phone": False}
    cameras.append(usb)
    backend.start()
    backend.camera_ready()

    backend.set_camera({"id": "3BA9"})  # still opening when...
    backend.set_camera({"id": "AAAA"})  # ...the user picks again
    backend.camera_switch_failed()

    assert backend.status()["camera_message"] == (
        "Couldn't switch to USB Camera, still using MacBook Pro Camera."
    )
    assert backend.get_camera() is BUILTIN


def test_camera_id_is_only_reported_during_a_session(backend):
    backend.set_camera({"id": "3BA9"})
    assert backend.status()["camera_id"] is None
    backend.start()
    assert backend.status()["camera_id"] == "3BA9"


def test_lost_camera_falls_back_to_another(backend, cameras):
    backend.camera_id = "3BA9"
    backend.start()
    backend.camera_ready()
    assert backend.camera_lost()
    assert backend.get_camera() is BUILTIN
    # The choice is kept for the next session, when the phone may be back.
    assert backend.camera_id == "3BA9"

    cameras.remove(PHONE)
    backend.camera_ready()
    assert not backend.camera_lost()
