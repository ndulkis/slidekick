from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

from .events import create_gesture_event


# This class handles states GESTURE_READY and GESTURE_ONGOING as a way to avoid duplicate gestures from triggering at the same time
class GestureState(Enum):
    GESTURE_READY = auto()
    GESTURE_ONGOING = auto()


@dataclass
class GestureRecognitionState:
    state: GestureState = GestureState.GESTURE_READY
    last_gesture_time: float = 0.0
    stationary_start_time: float | None = None


MIN_DISPLACEMENT = 0.10
IDEAL_DISPLACEMENT = 0.20

MIN_DIRECTION_CONSISTENCY = 0.60

MIN_AXIS_PURITY = 0.45

MIN_SWIPE_DURATION = 0.10
IDEAL_MIN_DURATION = 0.20
IDEAL_MAX_DURATION = 1.00
MAX_SWIPE_DURATION = 1.75

SWIPE_COOLDOWN = 1.5

# Minimum time the hand must remain settled before recognizing another gesture
GESTURE_STATIONARY_DURATION = 0.30

# Maximum normalized hand movement allowed while considering the hand stationary
GESTURE_STATIONARY_THRESHOLD = 0.015

CONFIDENCE_THRESHOLD = 0.55

# Weights utilized for confidence score
DISPLACEMENT_WEIGHT = 0.40
DIRECTION_WEIGHT = 0.35
AXIS_PURITY_WEIGHT = 0.10
DURATION_WEIGHT = 0.15

# Sanity Check for changing weights so they are no longer than 1.0
TOTAL_CONFIDENCE_WEIGHT = (
    DISPLACEMENT_WEIGHT + DIRECTION_WEIGHT + AXIS_PURITY_WEIGHT + DURATION_WEIGHT
)

if abs(TOTAL_CONFIDENCE_WEIGHT - 1.0) >= 1e-9:
    raise ValueError("Confidence weights must sum to 1.0")


def clamp(value):
    # Keeps a score between 0.0 and 1.0
    return max(0.0, min(value, 1.0))


def calculate_displacement_score(displacement):
    # Scores how strongly the swipe exceeds the minimum required displacement
    score = (displacement - MIN_DISPLACEMENT) / (IDEAL_DISPLACEMENT - MIN_DISPLACEMENT)

    return clamp(score)


def calculate_axis_purity(primary_displacement, off_axis_displacement):
    # Measures how much of the total movement occurred on the intended axis
    total_displacement = primary_displacement + off_axis_displacement

    if total_displacement == 0:
        return 0.0

    return primary_displacement / total_displacement


def calculate_duration_score(duration):
    # Gestures outside the allowed duration range receive no duration confidence
    if duration < MIN_SWIPE_DURATION or duration > MAX_SWIPE_DURATION:
        return 0.0

    # Gestures inside the ideal duration window receive full duration confidence
    if IDEAL_MIN_DURATION <= duration <= IDEAL_MAX_DURATION:
        return 1.0

    # Short but still valid gestures gradually increase toward the ideal range
    if duration < IDEAL_MIN_DURATION:
        score = (duration - MIN_SWIPE_DURATION) / (
            IDEAL_MIN_DURATION - MIN_SWIPE_DURATION
        )

        return clamp(score)

    # Long but still valid gestures gradually decrease after the ideal range
    score = (MAX_SWIPE_DURATION - duration) / (MAX_SWIPE_DURATION - IDEAL_MAX_DURATION)

    return clamp(score)


def calculate_swipe_confidence(
    displacement,
    direction_consistency,
    axis_purity,
    duration,
):
    displacement_score = calculate_displacement_score(displacement)
    duration_score = calculate_duration_score(duration)

    confidence = (
        DISPLACEMENT_WEIGHT * displacement_score
        + DIRECTION_WEIGHT * direction_consistency
        + AXIS_PURITY_WEIGHT * axis_purity
        + DURATION_WEIGHT * duration_score
    )

    return clamp(confidence)


# Checks whether the hand moved less than our experimental threshold between consecutive frames
def is_hand_stationary(
    position_history: deque[tuple[float, float, float]],
) -> bool:
    if len(position_history) < 2:
        return False

    # Compare the hand's current position to its previous position
    previous_x = position_history[-2][1]
    previous_y = position_history[-2][2]

    current_x = position_history[-1][1]
    current_y = position_history[-1][2]

    movement_x = abs(current_x - previous_x)
    movement_y = abs(current_y - previous_y)

    return (
        movement_x <= GESTURE_STATIONARY_THRESHOLD
        and movement_y <= GESTURE_STATIONARY_THRESHOLD
    )


def detect_swipe(
    hand_landmarks,
    position_history: deque[tuple[float, float, float]],
    gesture_state: GestureRecognitionState,
    current_time: float,
):
    # Uses landmark 9 near the center of the hand to track movement
    tracked_landmark = hand_landmarks[9]

    # Stores timestamp, horizontal position, and vertical position
    position_history.append(
        (
            current_time,
            tracked_landmark.x,
            tracked_landmark.y,
        )
    )

    # While a gesture is ongoing, the function won't evaluate another swipe.
    # It will wait for the hand to settle and for the cooldown to finish
    if gesture_state.state == GestureState.GESTURE_ONGOING:
        if is_hand_stationary(position_history):
            if gesture_state.stationary_start_time is None:
                gesture_state.stationary_start_time = current_time
        else:
            gesture_state.stationary_start_time = None

        cooldown_complete = (
            current_time - gesture_state.last_gesture_time >= SWIPE_COOLDOWN
        )

        stationary_complete = (
            gesture_state.stationary_start_time is not None
            and current_time - gesture_state.stationary_start_time
            >= GESTURE_STATIONARY_DURATION
        )

        if cooldown_complete and stationary_complete:
            gesture_state.state = GestureState.GESTURE_READY
            gesture_state.stationary_start_time = None
            position_history.clear()

        return None

    if len(position_history) <= 1:
        return None

    # Gets the oldest and newest recorded hand positions
    starting_time, starting_x, starting_y = position_history[0]
    ending_time, ending_x, ending_y = position_history[-1]

    # Horizontal movement is the primary axis for left/right swipes
    x_displacement = ending_x - starting_x

    # Vertical movement is the off-axis movement for horizontal swipes
    y_displacement = ending_y - starting_y

    primary_displacement = abs(x_displacement)
    off_axis_displacement = abs(y_displacement)

    axis_purity = calculate_axis_purity(
        primary_displacement,
        off_axis_displacement,
    )

    movement_duration = ending_time - starting_time

    # Stores horizontal movement between each pair of frames
    frame_movements = []

    for index in range(1, len(position_history)):
        previous_x = position_history[index - 1][1]
        current_x = position_history[index][1]

        frame_movements.append(current_x - previous_x)

    if not frame_movements:
        return None

    right_movements = sum(movement > 0 for movement in frame_movements)
    left_movements = sum(movement < 0 for movement in frame_movements)

    right_consistency = right_movements / len(frame_movements)
    left_consistency = left_movements / len(frame_movements)

    gesture_name = ""
    direction_consistency = 0.0

    # Uses the consistency associated with the overall direction of movement
    if x_displacement > 0:
        gesture_name = "swipe_right"
        direction_consistency = right_consistency

    elif x_displacement < 0:
        gesture_name = "swipe_left"
        direction_consistency = left_consistency

    else:
        return None

    valid_duration = MIN_SWIPE_DURATION <= movement_duration <= MAX_SWIPE_DURATION

    cooldown_complete = ending_time - gesture_state.last_gesture_time >= SWIPE_COOLDOWN

    # Movement must be primarily horizontal, but diagonal movement is allowed
    valid_candidate = (
        primary_displacement >= MIN_DISPLACEMENT
        and direction_consistency >= MIN_DIRECTION_CONSISTENCY
        and axis_purity >= MIN_AXIS_PURITY
        and valid_duration
        and cooldown_complete
    )

    if not valid_candidate:
        return None

    confidence = calculate_swipe_confidence(
        primary_displacement,
        direction_consistency,
        axis_purity,
        movement_duration,
    )

    # Candidate must also meet the final confidence threshold
    if confidence < CONFIDENCE_THRESHOLD:
        return None

    gesture_event = create_gesture_event(
        gesture_name,
        confidence,
        ending_time,
    )

    gesture_state.state = GestureState.GESTURE_ONGOING
    gesture_state.last_gesture_time = ending_time
    gesture_state.stationary_start_time = None

    position_history.clear()

    return gesture_event
