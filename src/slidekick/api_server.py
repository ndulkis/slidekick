"""Local HTTP API so the React dashboard can drive SlideKick.

The dashboard controls everything: starting a session turns the camera on and
ending it turns the camera off. The server runs in a background thread, because
OpenCV needs the main thread on macOS. It binds to 127.0.0.1 only. The browser reaches
it through the Vite dev server's /api proxy (frontend/vite.config.ts).
"""

import dataclasses
import json
import logging
import threading
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

from .contracts import SessionState
from .recognition.swipe_recognizer import GestureCalibration
from .session_controller import InvalidTransitionError
from .session_coordinator import PresentationCommandError, SessionCoordinator

logger = logging.getLogger(__name__)

API_HOST = "127.0.0.1"
API_PORT = 5001

# The GestureCalibration fields the Settings page can change. Must match
# backendField in frontend/src/settings/calibrationSettings.ts.
CALIBRATION_FIELDS = (
    "min_displacement",
    "max_swipe_duration",
    "confidence_threshold",
    "swipe_cooldown",
)

SESSION_ACTIONS = ("start", "pause", "resume", "end")

# Requests from any other host are refused, so a web page cannot use DNS
# rebinding to reach this API.
ALLOWED_HOSTNAMES = {"127.0.0.1", "localhost"}


class CalibrationError(ValueError):
    """The submitted calibration is malformed or fails GestureCalibration checks."""


def parse_calibration(data: Any, base: GestureCalibration) -> GestureCalibration:
    """Apply the editable fields in data to base. Raises CalibrationError."""
    if not isinstance(data, dict) or set(data) != set(CALIBRATION_FIELDS):
        raise CalibrationError(f"Expected exactly these fields: {CALIBRATION_FIELDS}")
    for name, value in data.items():
        # bool is an int subclass, so reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise CalibrationError(f"{name} must be a number")
    try:
        return dataclasses.replace(base, **{k: float(v) for k, v in data.items()})
    except ValueError as exc:
        raise CalibrationError(str(exc)) from exc


def calibration_fields(calibration: GestureCalibration) -> dict[str, float]:
    return {name: getattr(calibration, name) for name in CALIBRATION_FIELDS}


def load_calibration(path: Path | None) -> GestureCalibration:
    """Read the saved calibration, falling back to defaults if missing or bad."""
    default = GestureCalibration()
    if path is None or not path.exists():
        return default
    try:
        return parse_calibration(json.loads(path.read_text()), default)
    except (OSError, json.JSONDecodeError, CalibrationError):
        logger.warning("Ignoring unreadable calibration file %s", path, exc_info=True)
        return default


class Backend:
    """Thread-safe facade over the session that the camera loop and the HTTP
    API share.
    """

    def __init__(
        self, coordinator: SessionCoordinator, calibration_path: Path | None = None
    ) -> None:
        self.coordinator = coordinator
        self.calibration_path = calibration_path
        self.calibration = load_calibration(calibration_path)
        # off -> starting (session started) -> ready -> off (session ended),
        # or starting -> error if the camera never opens.
        self.camera = "off"
        self._started = threading.Event()
        self.last_gesture: dict[str, Any] | None = None
        self._gesture_id = 0
        self._lock = threading.Lock()

    @property
    def state(self):
        return self.coordinator.state

    def start(self):
        def start():
            event = self.coordinator.start()
            if self.camera != "ready":
                self.camera = "starting"
            self._started.set()
            return event

        return self._act(start)

    def pause(self):
        return self._act(self.coordinator.pause)

    def resume(self):
        return self._act(self.coordinator.resume)

    def end(self):
        return self._act(self.coordinator.end)

    def _act(self, action):
        with self._lock:
            event = action()
            # A gesture from before a session change must not reappear as new.
            self.last_gesture = None
            return event

    def handle_event(self, event: Any) -> bool:
        """Recognition callback. Never raises, so a failed keystroke does not
        stop the camera loop; the failure is reported via presentation_error.
        """
        with self._lock:
            try:
                handled = self.coordinator.handle_event(event)
            except PresentationCommandError:
                return False
            if handled:
                self._gesture_id += 1
                self.last_gesture = {
                    "id": self._gesture_id,
                    "gesture": self.coordinator.gestures.gesture_bindings[
                        event["gesture"]
                    ],
                    "confidence": event.get("confidence"),
                }
            return handled

    def wait_for_start(self) -> None:
        """Block until a session is started. The camera loop waits here."""
        self._started.wait()

    def should_stop_camera(self) -> bool:
        return self.state is SessionState.ENDED

    def camera_ready(self) -> None:
        self.camera = "ready"

    def camera_stopped(self) -> None:
        """The camera loop exited: the session ended, the camera window was
        closed, or the camera never opened.
        """
        with self._lock:
            self._started.clear()
            self.camera = "off" if self.camera == "ready" else "error"
            # Without a camera there is no session. Paused cannot end directly
            # (docs/session-state-model.md), so resume first.
            if self.state is SessionState.PAUSED:
                self.coordinator.resume()
            if self.state is SessionState.RUNNING:
                self.coordinator.end()
            self.last_gesture = None

    def set_calibration(self, data: Any) -> GestureCalibration:
        calibration = parse_calibration(data, self.calibration)
        if self.calibration_path is not None:
            self.calibration_path.parent.mkdir(parents=True, exist_ok=True)
            self.calibration_path.write_text(
                json.dumps(calibration_fields(calibration), indent=2)
            )
        self.calibration = calibration
        return calibration

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "state": self.coordinator.state.value,
                "camera": self.camera,
                "last_gesture": self.last_gesture,
                "presentation_error": self.coordinator.last_error,
            }


def create_app(backend: Backend) -> Flask:
    app = Flask(__name__)

    @app.before_request
    def check_request():
        if request.host.rsplit(":", 1)[0] not in ALLOWED_HOSTNAMES:
            return jsonify(error="Forbidden host"), 403
        # Requiring a JSON body makes cross-site requests need a CORS
        # preflight, which this server never approves.
        if request.method != "GET" and not request.is_json:
            return jsonify(error="Expected application/json"), 415
        return None

    @app.get("/api/session")
    def get_session():
        return jsonify(backend.status())

    @app.post("/api/session/<action>")
    def session_action(action: str):
        if action not in SESSION_ACTIONS:
            return jsonify(error=f"Unknown action {action}"), 404
        try:
            event = getattr(backend, action)()
        except InvalidTransitionError as exc:
            return jsonify(error=str(exc), **backend.status()), 409
        return jsonify(
            event={
                "type": event.type.value,
                "previous_state": event.previous_state.value,
                "new_state": event.new_state.value,
                "use_case": event.use_case,
            },
            **backend.status(),
        )

    @app.get("/api/calibration")
    def get_calibration():
        return jsonify(calibration_fields(backend.calibration))

    @app.put("/api/calibration")
    def put_calibration():
        try:
            calibration = backend.set_calibration(request.get_json())
        except CalibrationError as exc:
            return jsonify(error=str(exc)), 400
        return jsonify(calibration_fields(calibration))

    return app


def serve_in_background(backend: Backend, port: int = API_PORT) -> threading.Thread:
    app = create_app(backend)
    thread = threading.Thread(
        target=app.run,
        kwargs={"host": API_HOST, "port": port, "use_reloader": False},
        daemon=True,
    )
    thread.start()
    return thread
