from collections import deque
from dataclasses import dataclass

import pytest

from slidekick.recognition.camera import HAND_LOSS_GRACE_FRAMES, process_hand_detection
from slidekick.recognition.swipe_recognizer import (
    CONFIDENCE_THRESHOLD,
    GESTURE_STATIONARY_DURATION,
    IDEAL_DISPLACEMENT,
    IDEAL_MAX_DURATION,
    IDEAL_MIN_DURATION,
    MAX_SWIPE_DURATION,
    MIN_DISPLACEMENT,
    MIN_SWIPE_DURATION,
    SWIPE_COOLDOWN,
    GestureCalibration,
    GestureRecognitionState,
    GestureState,
    calculate_axis_purity,
    calculate_displacement_score,
    calculate_duration_score,
    clamp,
    detect_swipe,
)


@dataclass
class FakeLandmark:
    x: float
    y: float
    z: float = 0.0


def create_fake_hand(x, y):
    landmarks = [FakeLandmark(0.0, 0.0) for _ in range(21)]

    # Swipe recognizer currently tracks landmark 9.
    landmarks[9] = FakeLandmark(x, y)

    return landmarks


def run_movement(
    x_positions,
    y_positions=None,
    start_time=100.0,
    time_step=0.10,
    gesture_state=None,
    position_history=None,
):
    if y_positions is None:
        y_positions = [0.50] * len(x_positions)

    if gesture_state is None:
        gesture_state = GestureRecognitionState()

    if position_history is None:
        position_history = deque(maxlen=45)

    detected_events = []

    for index, (x, y) in enumerate(zip(x_positions, y_positions, strict=True)):
        current_time = start_time + (index * time_step)

        hand_landmarks = create_fake_hand(x, y)

        gesture_event = detect_swipe(
            hand_landmarks, position_history, gesture_state, current_time
        )

        if gesture_event is not None:
            detected_events.append(gesture_event)

    return detected_events, gesture_state


def test_calibration_resets_to_defaults():
    # Create a customized configuration.
    calibration = GestureCalibration(
        min_displacement=0.30,
        ideal_displacement=0.40,
        confidence_threshold=0.80,
    )

    # Confirm the custom settings were applied.
    assert calibration.min_displacement == 0.30
    assert calibration.ideal_displacement == 0.40
    assert calibration.confidence_threshold == 0.80

    # Simulate the user selecting "Reset to Defaults".
    calibration = GestureCalibration()

    # Verify that all settings match the default configuration.
    assert calibration == GestureCalibration()
    assert calibration.min_displacement == 0.10
    assert calibration.ideal_displacement == 0.20
    assert calibration.confidence_threshold == 0.55


def test_calibration_rejects_invalid_displacement():
    # Minimum displacement cannot exceed ideal displacement.
    with pytest.raises(ValueError):
        GestureCalibration(
            min_displacement=0.40,
            ideal_displacement=0.20,
        )

    # Equal values would cause division by zero.
    with pytest.raises(ValueError):
        GestureCalibration(
            min_displacement=0.20,
            ideal_displacement=0.20,
        )

    # Negative displacement values are invalid.
    with pytest.raises(ValueError):
        GestureCalibration(
            min_displacement=-0.10,
        )


def test_custom_calibration_rearms_with_shorter_cooldown():
    # Configure a shorter cooldown and stationary period.
    calibration = GestureCalibration(
        swipe_cooldown=0.50,
        stationary_duration=0.20,
    )

    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    # First, perform a valid swipe.
    x_positions = [0.30, 0.35, 0.40, 0.45, 0.50]

    detected_events = []

    for index, x in enumerate(x_positions):
        event = detect_swipe(
            hand_landmarks=create_fake_hand(x, 0.50),
            position_history=position_history,
            gesture_state=gesture_state,
            current_time=100.0 + index * 0.10,
            calibration=calibration,
        )

        if event is not None:
            detected_events.append(event)

    # The recognizer should now block additional gestures.
    assert len(detected_events) == 1
    assert gesture_state.state == GestureState.GESTURE_ONGOING

    # Hold the hand stationary after the swipe.
    for current_time in [100.50, 100.60, 100.70]:
        detect_swipe(
            hand_landmarks=create_fake_hand(0.50, 0.50),
            position_history=position_history,
            gesture_state=gesture_state,
            current_time=current_time,
            calibration=calibration,
        )

        if current_time < 100.70:
            # Both re-arming requirements are not yet satisfied.
            assert gesture_state.state == GestureState.GESTURE_ONGOING

    # Both custom requirements are satisfied at 100.70.
    assert gesture_state.state == GestureState.GESTURE_READY


def test_default_calibration_accepts_moderate_confidence_swipe():
    # Use the default recognition thresholds.
    calibration = GestureCalibration()

    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    detected_events = []

    # Total displacement is 0.15, producing a confidence
    # score of approximately 0.80.
    x_positions = [0.30, 0.34, 0.38, 0.42, 0.45]

    for index, x in enumerate(x_positions):
        event = detect_swipe(
            hand_landmarks=create_fake_hand(x, 0.50),
            position_history=position_history,
            gesture_state=gesture_state,
            current_time=100.0 + index * 0.10,
            calibration=calibration,
        )

        if event is not None:
            detected_events.append(event)

    # Default threshold is 0.55, so this swipe is accepted.
    assert len(detected_events) == 1
    assert detected_events[0]["gesture"] == "swipe_right"
    assert gesture_state.state == GestureState.GESTURE_ONGOING


def test_custom_calibration_rejects_low_confidence_swipe():
    # Set the confidence requirement higher than the default.
    calibration = GestureCalibration(
        confidence_threshold=1.0,
    )

    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    detected_events = []

    # Total displacement is 0.15, below the ideal of 0.20.
    # The movement still exceeds the default minimum of 0.10.
    x_positions = [0.30, 0.34, 0.38, 0.42, 0.45]

    for index, x in enumerate(x_positions):
        event = detect_swipe(
            hand_landmarks=create_fake_hand(x, 0.50),
            position_history=position_history,
            gesture_state=gesture_state,
            current_time=100.0 + index * 0.10,
            calibration=calibration,
        )

        if event is not None:
            detected_events.append(event)

    # The custom confidence threshold should reject the swipe.
    assert detected_events == []
    assert gesture_state.state == GestureState.GESTURE_READY


def test_custom_calibration_accepts_long_swipe():
    # Require a longer swipe than the default configuration.
    calibration = GestureCalibration(
        min_displacement=0.30,
        ideal_displacement=0.40,
    )

    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    detected_events = []

    # Total horizontal displacement is 0.40.
    x_positions = [0.20, 0.30, 0.40, 0.50, 0.60]

    for index, x in enumerate(x_positions):
        event = detect_swipe(
            hand_landmarks=create_fake_hand(x, 0.50),
            position_history=position_history,
            gesture_state=gesture_state,
            current_time=100.0 + index * 0.10,
            calibration=calibration,
        )

        if event is not None:
            detected_events.append(event)

    # The movement satisfies the customized swipe requirements.
    assert len(detected_events) == 1
    assert detected_events[0]["gesture"] == "swipe_right"
    assert gesture_state.state == GestureState.GESTURE_ONGOING


def test_custom_calibration_rejects_short_swipe():
    # Custom settings require a longer swipe than the default.
    calibration = GestureCalibration(
        min_displacement=0.30,
        ideal_displacement=0.40,
    )

    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    detected_events = []

    # Total horizontal displacement is 0.20.
    x_positions = [0.30, 0.35, 0.40, 0.45, 0.50]

    for index, x in enumerate(x_positions):
        event = detect_swipe(
            hand_landmarks=create_fake_hand(x, 0.50),
            position_history=position_history,
            gesture_state=gesture_state,
            current_time=100.0 + index * 0.10,
            calibration=calibration,
        )

        if event is not None:
            detected_events.append(event)

    # This movement does not meet the custom minimum distance.
    assert detected_events == []
    assert gesture_state.state == GestureState.GESTURE_READY


def test_detect_swipe_recognizes_right_swipe():
    events, gesture_state = run_movement([0.30, 0.35, 0.40, 0.45, 0.50])

    assert len(events) == 1
    assert events[0]["event_type"] == "gesture"
    assert events[0]["gesture"] == "swipe_right"
    assert events[0]["confidence"] >= CONFIDENCE_THRESHOLD
    assert gesture_state.state == GestureState.GESTURE_ONGOING


def test_detect_swipe_recognizes_left_swipe():
    events, gesture_state = run_movement([0.70, 0.65, 0.60, 0.55, 0.50])

    assert len(events) == 1
    assert events[0]["event_type"] == "gesture"
    assert events[0]["gesture"] == "swipe_left"
    assert events[0]["confidence"] >= CONFIDENCE_THRESHOLD
    assert gesture_state.state == GestureState.GESTURE_ONGOING


def test_detect_swipe_rejects_small_movement():
    events, gesture_state = run_movement([0.30, 0.31, 0.32, 0.33, 0.34])

    assert events == []
    assert gesture_state.state == GestureState.GESTURE_READY


def test_detect_swipe_rejects_mostly_vertical_movement():
    events, gesture_state = run_movement(
        x_positions=[0.30, 0.33, 0.36, 0.39, 0.42],
        y_positions=[0.20, 0.28, 0.36, 0.44, 0.52],
    )

    assert events == []
    assert gesture_state.state == GestureState.GESTURE_READY


def test_detect_swipe_blocks_duplicates_during_continuous_movement():
    positions = [0.10 + (index * 0.02) for index in range(100)]

    events, gesture_state = run_movement(
        positions,
        time_step=0.05,
    )

    assert len(events) == 1
    assert gesture_state.state == GestureState.GESTURE_ONGOING


def test_detect_swipe_remains_ongoing_without_stationary_period():
    events, gesture_state = run_movement(
        [0.30, 0.35, 0.40, 0.45, 0.50],
        start_time=100.0,
    )

    assert len(events) == 1

    more_events, gesture_state = run_movement(
        [0.55, 0.60, 0.65, 0.70, 0.75],
        start_time=100.0 + SWIPE_COOLDOWN + 1.0,
        gesture_state=gesture_state,
    )

    assert more_events == []
    assert gesture_state.state == GestureState.GESTURE_ONGOING


def test_detect_swipe_rearms_after_stationary_period_and_cooldown():
    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    # Perform the first intentional swipe.
    first_events, gesture_state = run_movement(
        [0.30, 0.35, 0.40, 0.45, 0.50],
        gesture_state=gesture_state,
        position_history=position_history,
    )

    assert len(first_events) == 1
    assert first_events[0]["gesture"] == "swipe_right"
    assert gesture_state.state == GestureState.GESTURE_ONGOING

    # Hold the hand stationary long enough to satisfy both
    # the cooldown and stationary duration requirements.
    stationary_frames = int(
        (SWIPE_COOLDOWN + GESTURE_STATIONARY_DURATION + 0.30) / 0.10
    )

    stationary_events, gesture_state = run_movement(
        [0.50] * stationary_frames,
        start_time=100.5,
        gesture_state=gesture_state,
        position_history=position_history,
    )

    assert stationary_events == []
    assert gesture_state.state == GestureState.GESTURE_READY

    # Perform another intentional swipe from the hand's current position.
    # Starting at 0.50 avoids an artificial jump back to 0.30.
    second_events, gesture_state = run_movement(
        [0.50, 0.55, 0.60, 0.65, 0.70],
        start_time=103.0,
        gesture_state=gesture_state,
        position_history=position_history,
    )

    print("Second swipe events:", second_events)
    print("Gesture state:", gesture_state.state)
    print("History length:", len(position_history))
    print("Position history:", list(position_history))
    assert len(second_events) == 1
    assert second_events[0]["gesture"] == "swipe_right"
    assert gesture_state.state == GestureState.GESTURE_ONGOING


def test_detect_swipe_does_not_rearm_during_slow_continuous_movement():
    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    # First, perform a valid swipe.
    first_events, gesture_state = run_movement(
        [0.30, 0.35, 0.40, 0.45, 0.50],
        gesture_state=gesture_state,
        position_history=position_history,
    )

    assert len(first_events) == 1
    assert gesture_state.state == GestureState.GESTURE_ONGOING

    # Continue moving slowly without stopping.
    # Each frame moves less than the stationary threshold.
    slow_positions = [0.50 + (index * 0.005) for index in range(50)]

    additional_events, gesture_state = run_movement(
        slow_positions,
        start_time=100.5,
        time_step=0.05,
        gesture_state=gesture_state,
        position_history=position_history,
    )

    assert additional_events == []
    assert gesture_state.state == GestureState.GESTURE_ONGOING


def test_clamp_keeps_value_inside_range():
    assert clamp(0.50) == 0.50


def test_clamp_limits_value_below_zero():
    assert clamp(-0.50) == 0.0


def test_clamp_limits_value_above_one():
    assert clamp(1.50) == 1.0


def test_displacement_score_is_zero_at_minimum():
    assert calculate_displacement_score(MIN_DISPLACEMENT) == 0.0


def test_displacement_score_is_one_at_ideal():
    assert calculate_displacement_score(IDEAL_DISPLACEMENT) == 1.0


def test_displacement_score_is_clamped_above_ideal():
    assert calculate_displacement_score(IDEAL_DISPLACEMENT + 0.20) == 1.0


def test_axis_purity_is_one_for_horizontal_movement():
    assert calculate_axis_purity(0.20, 0.0) == 1.0


def test_axis_purity_is_half_for_equal_horizontal_and_vertical_movement():
    assert calculate_axis_purity(0.20, 0.20) == pytest.approx(0.50)


def test_axis_purity_is_zero_when_there_is_no_movement():
    assert calculate_axis_purity(0.0, 0.0) == 0.0


def test_duration_score_is_zero_below_minimum():
    assert calculate_duration_score(MIN_SWIPE_DURATION - 0.01) == 0.0


def test_duration_score_is_one_inside_ideal_range():
    duration = (IDEAL_MIN_DURATION + IDEAL_MAX_DURATION) / 2

    assert calculate_duration_score(duration) == 1.0


def test_duration_score_is_zero_above_maximum():
    assert calculate_duration_score(MAX_SWIPE_DURATION + 0.01) == 0.0


def test_hand_tracking_loss_does_not_rearm_gesture():
    position_history = deque(maxlen=45)
    gesture_state = GestureRecognitionState()

    # Perform one valid swipe.
    events, gesture_state = run_movement(
        [0.30, 0.35, 0.40, 0.45, 0.50],
        gesture_state=gesture_state,
        position_history=position_history,
    )

    assert len(events) == 1
    assert gesture_state.state == GestureState.GESTURE_ONGOING

    # Simulate MediaPipe losing the hand.
    class FakeResult:
        def __init__(self):
            self.hand_landmarks = []

    missed_hand_frames = 0

    for _ in range(HAND_LOSS_GRACE_FRAMES):
        gesture_event, landmark_event, missed_hand_frames = process_hand_detection(
            FakeResult(),
            None,
            position_history,
            gesture_state,
            missed_hand_frames,
        )

        assert gesture_event is None
        assert landmark_event is None
        assert gesture_state.state == GestureState.GESTURE_ONGOING

    # After the grace period, position history should be cleared,
    # but the gesture lifecycle must remain ongoing.
    assert missed_hand_frames == HAND_LOSS_GRACE_FRAMES
    assert len(position_history) == 0

    # Tracking resumes with continued movement.
    # This should NOT generate a duplicate swipe.
    more_events, gesture_state = run_movement(
        [0.55, 0.60, 0.65, 0.70, 0.75],
        start_time=100.5,
        gesture_state=gesture_state,
        position_history=position_history,
    )

    assert more_events == []
    assert gesture_state.state == GestureState.GESTURE_ONGOING
