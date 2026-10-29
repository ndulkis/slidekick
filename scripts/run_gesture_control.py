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


def main():
    adapter = KeyboardPresentationAdapter()
    controller = GestureCommandController(adapter=adapter)
    session = SessionCoordinator(gestures=controller)

    session.start()
    print(f"Session: {session.state.value}")

    run_camera(
        session.handle_event,
        key_handler=make_key_handler(session),
    )


if __name__ == "__main__":
    main()
