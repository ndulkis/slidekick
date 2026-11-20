"""The `slidekick` command: camera recognition, the dashboard API, and the
dashboard itself, started together.
"""

import importlib.util
import os
import plistlib
import shutil
import socket
import subprocess  # nosec B404
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path

from .api_server import API_PORT, Backend, serve_in_background
from .gesture_command_controller import GestureCommandController
from .recognition.camera import run_camera
from .session_coordinator import SessionCoordinator

# ponytail: assumes an editable install from a checkout (`pip install -e .`);
# the models, data/ and frontend/ live in the repo, not in the package.
REPO_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_PORT = 5173
APP_ICON = REPO_ROOT / "assets/app-icon/SlideKick.icns"


def find_app_browser() -> str | None:
    """Path to Chrome or Edge, which can show a page in its own app window."""
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for root in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(root)
        if base:
            candidates += [
                rf"{base}\Google\Chrome\Application\chrome.exe",
                rf"{base}\Microsoft\Edge\Application\msedge.exe",
            ]
    for path in candidates:
        if Path(path).exists():
            return path
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        if found := shutil.which(name):
            return found
    return None


def native_window_command(url: str, work_dir: str) -> list[str] | None:
    """macOS: the command that shows url in SlideKick's own native window
    (dashboard_window.py), so the Dock shows SlideKick's icon, not Chrome's.
    None on other systems, or when pywebview is not installed.
    """
    if sys.platform != "darwin" or importlib.util.find_spec("webview") is None:
        return None
    return [window_python(work_dir), "-m", "slidekick.dashboard_window", url]


def window_python(work_dir: str) -> str:
    """Python as the executable of a throwaway SlideKick.app in work_dir. The
    Dock takes an app's name and icon from the bundle its executable is in,
    so without this the window is labelled "Python".
    """
    # Only framework builds (python.org, Homebrew) have the GUI-capable
    # Python.app; others keep the "Python" label.
    python_app = Path(sys.base_prefix) / "Resources/Python.app/Contents/MacOS/Python"
    if not python_app.exists():
        return sys.executable
    contents = Path(work_dir) / "SlideKick.app/Contents"
    (contents / "MacOS").mkdir(parents=True)
    (contents / "Resources").mkdir()
    (contents / "MacOS/SlideKick").symlink_to(python_app)
    (contents / "Resources/SlideKick.icns").symlink_to(APP_ICON)
    (contents / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleName": "SlideKick",
                "CFBundleDisplayName": "SlideKick",
                "CFBundleIdentifier": "dev.slidekick.dashboard",
                "CFBundleExecutable": "SlideKick",
                "CFBundleIconFile": "SlideKick.icns",
                "CFBundlePackageType": "APPL",
            }
        )
    )
    return str(contents / "MacOS/SlideKick")


def wait_for_port(port: int, timeout: float = 15.0) -> bool:
    """True once something accepts connections on localhost:port."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            socket.create_connection(("localhost", port), timeout=0.5).close()
            return True
        except OSError:
            time.sleep(0.1)
    return False


def start_dashboard(
    profile_dir: str, on_window_closed: Callable[[], None] | None = None
) -> list[subprocess.Popen]:
    """Start the Vite dashboard dev server and open the dashboard.

    The dashboard opens in a window that this process owns, so quitting
    SlideKick can close it, and closing it quits SlideKick: a native window on
    macOS, otherwise a Chrome/Edge app window. Without either it opens as a
    tab in the default browser, which SlideKick cannot close.

    on_window_closed runs as soon as the native window's process ends. (A
    Chrome/Edge app window's process outlives its window on macOS, so that
    one is noticed through /api/alive instead.)

    Returns the processes to terminate on exit.
    """
    frontend = REPO_ROOT / "frontend"
    vite = frontend / "node_modules/vite/bin/vite.js"
    node = shutil.which("node")
    if node is None or not vite.exists():
        print("Dashboard not started: run `npm --prefix frontend ci` first.")
        return []
    url = f"http://localhost:{DASHBOARD_PORT}/session"
    print(f"Dashboard: {url}")
    native = native_window_command(url, profile_dir)
    browser = None if native else find_app_browser()

    # Vite runs with node directly instead of through npm, so terminating it
    # also stops the server on Windows (npm.cmd would leave node running).
    command = [node, str(vite), "--port", str(DASHBOARD_PORT), "--strictPort"]
    if native is None and browser is None:
        command += ["--open", "/session"]
    # Bandit is silenced on the import and on both Popen calls: fixed
    # argument lists, no shell, no user input.
    processes = [subprocess.Popen(command, cwd=frontend)]  # nosec B603

    if (native or browser) and wait_for_port(DASHBOARD_PORT):
        window = subprocess.Popen(  # nosec B603
            native
            or [
                browser,
                f"--app={url}",
                # Its own profile keeps this a separate browser process.
                # With the user's profile, an already-running Chrome
                # would take the window over and it could not be closed.
                f"--user-data-dir={profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=1100,850",
                # Keep the dashboard fully alive while it is hidden behind
                # the slideshow.
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            # The app bundle's Python is not the virtualenv's, so hand it
            # this process's import path.
            env={**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, sys.path))}
            if native
            else None,
        )
        processes.append(window)
        if native and on_window_closed is not None:
            threading.Thread(
                target=lambda: (window.wait(), on_window_closed()), daemon=True
            ).start()
    return processes


def main():
    # The camera loop opens models/ and data/ by relative path, so run from the
    # repo root wherever `slidekick` was typed.
    os.chdir(REPO_ROOT)
    # Default bindings: swipes only. "end" is not bindable by policy
    # (command_policy.py), so no gesture can close the slideshow.
    session = SessionCoordinator(gestures=GestureCommandController())
    backend = Backend(
        session,
        calibration_path=REPO_ROOT / "data/calibration.json",
        camera_path=REPO_ROOT / "data/camera.json",
        bindings_path=REPO_ROOT / "data/gesture_bindings.json",
    )
    serve_in_background(backend)
    print(f"Dashboard API: http://127.0.0.1:{API_PORT}/api/session")

    # The browser profile (or macOS app bundle) is throwaway: the dashboard
    # keeps nothing in it.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile_dir:
        # Closing the native window quits at once, even with other dashboard
        # pages (a browser tab) still open.
        processes = start_dashboard(profile_dir, on_window_closed=backend.quit)
        # Only with the app window (vite + window). A normal browser tab may
        # be suspended by the browser, which must not quit a presentation.
        backend.quit_when_dashboard_closes = len(processes) == 2
        print("Start a session from the dashboard. Quit there, or with Ctrl+C.")
        try:
            while not backend.quitting:
                run_one_session(backend)
        except KeyboardInterrupt:
            pass
        finally:
            # Closes the dashboard window and stops the dev server. Waiting
            # lets the browser let go of its profile before it is deleted.
            for process in processes:
                process.terminate()
            for process in processes:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


def run_one_session(backend: Backend) -> None:
    """Wait for the dashboard to start a session, then run the camera until
    the session ends. Must run on the main thread (OpenCV on macOS).
    """
    backend.wait_for_start()
    if backend.quitting:
        return
    try:
        run_camera(
            backend.handle_event,
            enable_static_events=True,
            get_calibration=lambda: backend.calibration,
            on_ready=backend.camera_ready,
            should_stop=backend.should_stop_camera,
            on_frame=backend.set_frame,
            get_camera=backend.get_camera,
            on_camera_failed=backend.camera_switch_failed,
            on_camera_lost=backend.camera_lost,
        )
    finally:
        backend.camera_stopped()
