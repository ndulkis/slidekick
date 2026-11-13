"""The `slidekick` command: camera recognition, the dashboard API, and the
dashboard itself, started together.
"""

import os
import shutil
import subprocess
from pathlib import Path

from .api_server import API_PORT, Backend, serve_in_background
from .gesture_command_controller import GestureCommandController
from .recognition.camera import run_camera
from .session_coordinator import SessionCoordinator

# ponytail: assumes an editable install from a checkout (`pip install -e .`);
# the models, data/ and frontend/ live in the repo, not in the package.
REPO_ROOT = Path(__file__).resolve().parents[2]
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
    # The camera loop opens models/ and data/ by relative path, so run from the
    # repo root wherever `slidekick` was typed.
    os.chdir(REPO_ROOT)
    # Default bindings: swipes only. "end" is not bindable by policy
    # (command_policy.py), so no gesture can close the slideshow.
    session = SessionCoordinator(gestures=GestureCommandController())
    backend = Backend(session, calibration_path=REPO_ROOT / "data/calibration.json")
    serve_in_background(backend)
    print(f"Dashboard API: http://127.0.0.1:{API_PORT}/api/session")

    dashboard = start_dashboard()
    print("Start a session from the dashboard. Ctrl+C to quit.")
    try:
        while True:
            run_one_session(backend)
    except KeyboardInterrupt:
        pass
    finally:
        if dashboard is not None:
            dashboard.terminate()


def run_one_session(backend: Backend) -> None:
    """Wait for the dashboard to start a session, then run the camera until
    the session ends. Must run on the main thread (OpenCV on macOS).
    """
    backend.wait_for_start()
    try:
        run_camera(
            backend.handle_event,
            enable_static_events=True,
            get_calibration=lambda: backend.calibration,
            on_ready=backend.camera_ready,
            should_stop=backend.should_stop_camera,
            on_frame=backend.set_frame,
        )
    finally:
        backend.camera_stopped()
