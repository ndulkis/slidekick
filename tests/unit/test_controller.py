from slidekick.controller import GestureType, PresentationController, RecognitionEvent


class FakeAdapter:
    def __init__(self):
        self.calls = []

    def next_slide(self):
        self.calls.append("next")
        return True

    def previous_slide(self):
        self.calls.append("previous")
        return True

    def end_presentation(self):
        self.calls.append("end")
        return True


def test_controller_routes_next_gesture():
    adapter = FakeAdapter()
    controller = PresentationController(adapter=adapter)
    result = controller.handle_event(RecognitionEvent(GestureType.NEXT))
    assert result is True
    assert adapter.calls == ["next"]


def test_controller_routes_previous_gesture():
    adapter = FakeAdapter()
    controller = PresentationController(adapter=adapter)
    result = controller.handle_event(RecognitionEvent(GestureType.PREVIOUS))
    assert result is True
    assert adapter.calls == ["previous"]


def test_controller_routes_end_gesture():
    adapter = FakeAdapter()
    controller = PresentationController(adapter=adapter)
    result = controller.handle_event(RecognitionEvent(GestureType.END))
    assert result is True
    assert adapter.calls == ["end"]
