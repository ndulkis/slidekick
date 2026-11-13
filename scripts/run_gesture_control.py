import shutil
import subprocess
import threading
from pathlib import Path

from slidekick.api_server import API_PORT, Backend, serve_in_background
from slidekick.gesture_command_controller import GestureCommandController
from slidekick.presentation_adapter import KeyboardPresentationAdapter
from slidekick.recognition.camera import run_camera
from slidekick.session_controller import InvalidTransitionError
from slidekick.session_coordinator import SessionCoordinator


def make_key_handler(session: SessionCoordinator):
    actions = {
        ord("s"): session.start,
        ord("p"): session.pause,
        ord("r"): session.resume,
        ord("e"): session.end,
    }

    def handle_key(key: int) -> None:
        action = actions.get(key)

        if action is None:
            return

        try:
            action()
            print(f"Session: {session.state.value}")
        except InvalidTransitionError as exc:
            print(f"Invalid session action: {exc}")

    return handle_key


REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_PORT = 5173


def start_dashboard() -> subprocess.Popen | None:
    """Start the Vite dashboard dev server and open it in the browser.

    Runs vite with node directly instead of through npm, so terminating it
    also stops the server on Windows (npm.cmd would leave node running).
    """
    frontend = REPO_ROOT / "frontend"
    vite = frontend / "node_modules/vite/bin/vite.js"
    node = shutil.which("node")
    if node is None or not vite.exists():
        print("Dashboard not started: run `npm --prefix frontend ci` first.")
        return None
    print(f"Dashboard: http://localhost:{DASHBOARD_PORT}/session")
    return subprocess.Popen(
        [
            node,
            str(vite),
            "--port",
            str(DASHBOARD_PORT),
            "--strictPort",
            "--open",
            "/session",
        ],
        cwd=frontend,
    )


def main():
    adapter = KeyboardPresentationAdapter()
    controller = GestureCommandController(
        adapter=adapter,
        gesture_bindings={
            "swipe_right": "next",
            "swipe_left": "previous",
            "pinch": "end",
        },
    )
    session = SessionCoordinator(gestures=controller)
    backend = Backend(session, calibration_path=REPO_ROOT / "data/calibration.json")
    serve_in_background(backend)
    print(f"Dashboard API: http://127.0.0.1:{API_PORT}/api/session")

    dashboard = start_dashboard()
    try:
        run_session(backend)
    finally:
        if dashboard is not None:
            dashboard.terminate()


def run_session(backend: Backend) -> None:
    backend.start()
    print(f"Session: {backend.state.value}")

    run_camera(
        backend.handle_event,
        key_handler=make_key_handler(backend),
        enable_static_events=True,
        get_calibration=lambda: backend.calibration,
        on_ready=backend.camera_ready,
    )

    if backend.camera != "ready":
        # Keep the API up so the dashboard can show the camera error.
        backend.camera = "error"
        print("Camera did not start. The dashboard shows the error. Ctrl+C to quit.")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
