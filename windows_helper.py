"""Native Windows helper API for controlling presentations and browsers."""

from flask import Flask, Response, jsonify
import pyautogui

from slidekick.presentation_adapter import KeyboardPresentationAdapter

app = Flask(__name__)
adapter = KeyboardPresentationAdapter()


def _build_response(command: str) -> tuple[Response, int]:
    """Execute a command and format the Flask JSON response."""
    result = adapter.execute_command(command)
    status_code = 200 if result.get("status") == "success" else 500
    return jsonify(result), status_code


# --- EXISTING PRESENTATION ROUTES ---

@app.route("/health", methods=["GET"])
def health_check() -> tuple[Response, int]:
    """Verify the helper is running and accepting requests."""
    return jsonify({"status": "ok", "service": "slidekick-native-helper"}), 200

@app.route("/next", methods=["POST"])
def trigger_next() -> tuple[Response, int]:
    return _build_response("next")

@app.route("/previous", methods=["POST"])
def trigger_previous() -> tuple[Response, int]:
    return _build_response("previous")

@app.route("/pause", methods=["POST"])
def trigger_pause() -> tuple[Response, int]:
    return _build_response("pause")

@app.route("/resume", methods=["POST"])
def trigger_resume() -> tuple[Response, int]:
    return _build_response("resume")


# --- NEW BROWSER CONTROL ROUTES ---

@app.route("/tab-right", methods=["POST"])
def tab_right() -> tuple[Response, int]:
    """Switch to the next browser tab (Ctrl + Tab)."""
    print("Simulating: Ctrl + Tab (Next Browser Tab)")
    pyautogui.hotkey('ctrl', 'tab')
    return jsonify({"status": "success", "command": "tab-right"}), 200

@app.route("/tab-left", methods=["POST"])
def tab_left() -> tuple[Response, int]:
    """Switch to the previous browser tab (Ctrl + Shift + Tab)."""
    print("Simulating: Ctrl + Shift + Tab (Previous Browser Tab)")
    pyautogui.hotkey('ctrl', 'shift', 'tab')
    return jsonify({"status": "success", "command": "tab-left"}), 200

@app.route("/scroll-down", methods=["POST"])
def scroll_down() -> tuple[Response, int]:
    """Scroll down the active window."""
    print("Simulating: Scroll Down")
    pyautogui.scroll(-500)  # Negative integer scrolls down on Windows
    return jsonify({"status": "success", "command": "scroll-down"}), 200

@app.route("/scroll-up", methods=["POST"])
def scroll_up() -> tuple[Response, int]:
    """Scroll up the active window."""
    print("Simulating: Scroll Up")
    pyautogui.scroll(500)
    return jsonify({"status": "success", "command": "scroll-up"}), 200


if __name__ == "__main__":
    print("Starting native Windows presentation helper on port 8000...")
    app.run(host="127.0.0.1", port=8000)