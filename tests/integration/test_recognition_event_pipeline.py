from collections import deque
from unittest.mock import MagicMock, patch

import numpy as np

from slidekick.gesture_command_controller import GestureCommandController
from slidekick.presentation_adapter import PresentationAdapter
from slidekick.recognition.camera import emit_event, process_hand_detection
from slidekick.recognition.events import create_gesture_event
from slidekick.recognition.swipe_recognizer import (
    GestureCalibration,
    GestureRecognitionState,
)


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


def test_camera_forwards_custom_calibration_to_recognizer():
    # Create custom calibration settings.
    calibration = GestureCalibration(
        min_displacement=0.30,
        ideal_displacement=0.40,
        confidence_threshold=0.80,
    )

    # Create mock MediaPipe hand detection results.
    hand_landmarks = [MagicMock(x=0.50, y=0.50, z=0.0) for _ in range(21)]

    result = MagicMock()
    result.hand_landmarks = [hand_landmarks]

    # Create a blank camera frame for landmark drawing.
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    # Mock swipe detection to inspect the calibration forwarded to it.
    with patch("slidekick.recognition.camera.detect_swipe") as mock_detect:
        mock_detect.return_value = None

        process_hand_detection(
            result=result,
            frame=frame,
            position_history=position_history,
            gesture_state=gesture_state,
            missed_hand_frames=0,
            calibration=calibration,
        )

        # Verify that the same custom calibration reaches detect_swipe.
        assert mock_detect.call_args.kwargs["calibration"] is calibration


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
