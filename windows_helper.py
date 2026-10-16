"""Native Windows helper API for controlling presentations."""

from flask import Flask, Response, jsonify

from slidekick.presentation_adapter import KeyboardPresentationAdapter

app = Flask(__name__)
adapter = KeyboardPresentationAdapter()


def _build_response(command: str) -> tuple[Response, int]:
    """Execute a command and format the Flask JSON response."""
    result = adapter.execute_command(command)
    status_code = 200 if result.get("status") == "success" else 500
    return jsonify(result), status_code


@app.route("/next", methods=["GET", "POST"])
def trigger_next() -> tuple[Response, int]:
    """Trigger the next slide command."""
    return _build_response("next")


@app.route("/previous", methods=["GET", "POST"])
def trigger_previous() -> tuple[Response, int]:
    """Trigger the previous slide command."""
    return _build_response("previous")


@app.route("/pause", methods=["GET", "POST"])
def trigger_pause() -> tuple[Response, int]:
    """Trigger the pause presentation command."""
    return _build_response("pause")


@app.route("/resume", methods=["GET", "POST"])
def trigger_resume() -> tuple[Response, int]:
    """Trigger the resume presentation command."""
    return _build_response("resume")


if __name__ == "__main__":
    print("Starting native Windows presentation helper on port 8000...")
    app.run(host="0.0.0.0", port=8000)
