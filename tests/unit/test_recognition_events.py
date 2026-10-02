from dataclasses import dataclass

from slidekick.recognition.events import (
    create_gesture_event,
    create_landmark_event,
)


@dataclass
class FakeLandmark:
    x: float
    y: float
    z: float


def test_create_gesture_event():
    event = create_gesture_event(
        "swipe_right",
        0.85,
        100.0,
    )

    assert event["event_type"] == "gesture"
    assert event["gesture"] == "swipe_right"
    assert event["confidence"] == 0.85
    assert event["timestamp"] == 100.0


def test_create_landmark_event():
    landmarks = [
        FakeLandmark(0.10, 0.20, 0.30),
        FakeLandmark(0.40, 0.50, 0.60),
    ]

    event = create_landmark_event(
        landmarks,
        100.0,
    )

    assert event["event_type"] == "landmarks"
    assert event["timestamp"] == 100.0
    assert len(event["landmarks"]) == 2

    assert event["landmarks"][0] == {
        "id": 0,
        "x": 0.10,
        "y": 0.20,
        "z": 0.30,
    }

    assert event["landmarks"][1] == {
        "id": 1,
        "x": 0.40,
        "y": 0.50,
        "z": 0.60,
    }
