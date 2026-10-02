from collections import deque
from dataclasses import dataclass

import pytest

from slidekick.recognition.swipe_recognizer import (
    CONFIDENCE_THRESHOLD,
    IDEAL_DISPLACEMENT,
    IDEAL_MAX_DURATION,
    IDEAL_MIN_DURATION,
    MAX_SWIPE_DURATION,
    MIN_DISPLACEMENT,
    MIN_SWIPE_DURATION,
    SWIPE_COOLDOWN,
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
    x_positions, y_positions=None, start_time=100.0, time_step=0.10, last_swipe_time=0.0
):
    if y_positions is None:
        y_positions = [0.50] * len(x_positions)

    position_history = deque(maxlen=45)

    detected_event = None
    updated_last_swipe_time = last_swipe_time

    for index, (x, y) in enumerate(zip(x_positions, y_positions, strict=True)):
        current_time = start_time + (index * time_step)

        hand_landmarks = create_fake_hand(x, y)

        gesture_event, updated_last_swipe_time = detect_swipe(
            hand_landmarks, position_history, updated_last_swipe_time, current_time
        )

        if gesture_event is not None:
            detected_event = gesture_event
            break

    return detected_event, updated_last_swipe_time


def test_detect_swipe_recognizes_right_swipe():
    gesture_event, _ = run_movement([0.30, 0.35, 0.40, 0.45, 0.50])

    assert gesture_event is not None
    assert gesture_event["event_type"] == "gesture"
    assert gesture_event["gesture"] == "swipe_right"
    assert gesture_event["confidence"] >= CONFIDENCE_THRESHOLD


def test_detect_swipe_recognizes_left_swipe():
    gesture_event, _ = run_movement([0.70, 0.65, 0.60, 0.55, 0.50])

    assert gesture_event is not None
    assert gesture_event["event_type"] == "gesture"
    assert gesture_event["gesture"] == "swipe_left"
    assert gesture_event["confidence"] >= CONFIDENCE_THRESHOLD


def test_detect_swipe_rejects_small_movement():
    gesture_event, _ = run_movement([0.30, 0.31, 0.32, 0.33, 0.34])

    assert gesture_event is None


def test_detect_swipe_rejects_mostly_vertical_movement():
    gesture_event, _ = run_movement(
        x_positions=[0.30, 0.33, 0.36, 0.39, 0.42],
        y_positions=[0.20, 0.28, 0.36, 0.44, 0.52],
    )

    assert gesture_event is None


def test_detect_swipe_blocks_second_swipe_during_cooldown():
    first_event, last_swipe_time = run_movement(
        [0.30, 0.35, 0.40, 0.45, 0.50],
        start_time=100.0,
    )

    assert first_event is not None

    second_event, _ = run_movement(
        [0.30, 0.35, 0.40, 0.45, 0.50],
        start_time=last_swipe_time + 0.20,
        last_swipe_time=last_swipe_time,
    )

    assert second_event is None


def test_detect_swipe_allows_new_swipe_after_cooldown():
    first_event, last_swipe_time = run_movement(
        [0.30, 0.35, 0.40, 0.45, 0.50],
        start_time=100.0,
    )

    assert first_event is not None

    second_event, _ = run_movement(
        [0.30, 0.35, 0.40, 0.45, 0.50],
        start_time=last_swipe_time + SWIPE_COOLDOWN + 0.10,
        last_swipe_time=last_swipe_time,
    )

    assert second_event is not None
    assert second_event["gesture"] == "swipe_right"


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
