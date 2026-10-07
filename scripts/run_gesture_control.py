from slidekick.gesture_command_controller import GestureCommandController
from slidekick.presentation_adapter import KeyboardPresentationAdapter
from slidekick.recognition.camera import run_camera


def main():
    adapter = KeyboardPresentationAdapter()
    controller = GestureCommandController(adapter=adapter)

    run_camera(controller.handle_event)


if __name__ == "__main__":
    main()
