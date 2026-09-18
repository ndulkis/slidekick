import pyautogui
from flask import Flask

app = Flask(__name__)


class KeyboardPresentationAdapter:
    """MVP Adapter that uses universal keystrokes to control slides."""

    def next_slide(self) -> bool:
        print("Simulating: RIGHT arrow (Next Slide)")
        pyautogui.press("right")
        return True


adapter = KeyboardPresentationAdapter()


@app.route("/next", methods=["GET"])
def trigger_next():
    print("Command received from Docker container!")
    adapter.next_slide()
    return "Success", 200


if __name__ == "__main__":
    print("Starting native Windows presentation helper on port 8000...")
    app.run(host="0.0.0.0", port=8000)
