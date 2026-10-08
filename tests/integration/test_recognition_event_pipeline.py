from slidekick.gesture_command_controller import GestureCommandController
from slidekick.presentation_adapter import PresentationAdapter
from slidekick.recognition.camera import emit_event
from slidekick.recognition.events import create_gesture_event


class FakeAdapter(PresentationAdapter):
    def __init__(self):
        self.calls = []

    def next_slide(self) -> bool:
        self.calls.append("next")
        return True

    def previous_slide(self) -> bool:
        self.calls.append("previous")
        return True

    def pause_presentation(self) -> bool:
        self.calls.append("pause")
        return True

    def resume_presentation(self) -> bool:
        self.calls.append("resume")
        return True

    def end_presentation(self) -> bool:
        self.calls.append("end")
        return True


def test_gesture_event_reaches_controller_and_adapter():
    adapter = FakeAdapter()
    controller = GestureCommandController(adapter=adapter)

    gesture_event = create_gesture_event(
        "swipe_right",
        0.85,
        100.0,
    )

    emit_event(gesture_event, controller.handle_event)

    assert adapter.calls == ["next"]


def test_gesture_event_reaches_event_handler():
    received_events = []

    gesture_event = create_gesture_event("swipe_right", 0.85, 100.0)

    emit_event(gesture_event, received_events.append)

    assert len(received_events) == 1
    assert received_events[0] == gesture_event
    assert received_events[0]["gesture"] == "swipe_right"
    assert received_events[0]["confidence"] == 0.85


def test_none_event_is_not_sent_to_handler():
    received_events = []

    emit_event(None, received_events.append)

    assert received_events == []


def test_event_is_safe_when_no_handler_is_provided():
    gesture_event = create_gesture_event(
        "swipe_left",
        0.80,
        100.0,
    )

    emit_event(gesture_event, None)
