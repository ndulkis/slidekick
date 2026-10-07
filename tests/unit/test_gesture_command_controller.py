from slidekick.gesture_command_controller import GestureCommandController
from slidekick.presentation_adapter import PresentationAdapter


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


def test_swipe_right_routes_to_next_slide():
    adapter = FakeAdapter()
    controller = GestureCommandController(adapter=adapter)

    event = {
        "event_type": "gesture",
        "gesture": "swipe_right",
        "confidence": 0.85,
        "timestamp": 100.0,
    }

    result = controller.handle_event(event)

    assert result is True
    assert adapter.calls == ["next"]


def test_swipe_left_routes_to_previous_slide():
    adapter = FakeAdapter()
    controller = GestureCommandController(adapter=adapter)

    event = {
        "event_type": "gesture",
        "gesture": "swipe_left",
        "confidence": 0.85,
        "timestamp": 100.0,
    }

    result = controller.handle_event(event)

    assert result is True
    assert adapter.calls == ["previous"]


def test_landmark_event_does_not_trigger_command():
    adapter = FakeAdapter()
    controller = GestureCommandController(adapter=adapter)

    event = {
        "event_type": "landmarks",
        "timestamp": 100.0,
        "landmarks": [],
    }

    result = controller.handle_event(event)

    assert result is False
    assert adapter.calls == []


def test_unknown_gesture_does_not_trigger_command():
    adapter = FakeAdapter()
    controller = GestureCommandController(adapter=adapter)

    event = {
        "event_type": "gesture",
        "gesture": "unknown_gesture",
        "confidence": 0.90,
        "timestamp": 100.0,
    }

    result = controller.handle_event(event)

    assert result is False
    assert adapter.calls == []
