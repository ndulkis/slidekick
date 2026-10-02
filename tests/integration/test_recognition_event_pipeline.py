from slidekick.recognition.camera import emit_event
from slidekick.recognition.events import create_gesture_event


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
