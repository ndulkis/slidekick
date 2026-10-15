"""Recognize horizontal hand swipes and manage gesture re-arming.

The recognizer tracks MediaPipe hand landmarks, evaluates swipe
candidates, and prevents duplicate detections until the hand settles.
"""

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

from .events import create_gesture_event

# ============================================================
# 1. RECOGNITION CONFIGURATION
# ============================================================

# Minimum and ideal horizontal displacement (normalized coordinates).
MIN_DISPLACEMENT = 0.10
IDEAL_DISPLACEMENT = 0.20

# Minimum fraction of horizontal movements in the swipe direction.
MIN_DIRECTION_CONSISTENCY = 0.60

# Minimum proportion of movement along the intended axis.
MIN_AXIS_PURITY = 0.45

# Allowed and preferred swipe duration ranges (seconds).
MIN_SWIPE_DURATION = 0.10
IDEAL_MIN_DURATION = 0.20
IDEAL_MAX_DURATION = 1.00
MAX_SWIPE_DURATION = 1.75

# Time required between recognized gestures (seconds).
SWIPE_COOLDOWN = 1.5

# Stationary conditions required to re-arm gesture recognition.
GESTURE_STATIONARY_DURATION = 0.30
GESTURE_STATIONARY_THRESHOLD = 0.015

# Minimum confidence required to accept a swipe.
CONFIDENCE_THRESHOLD = 0.55

# Relative contribution of each metric to the confidence score.
DISPLACEMENT_WEIGHT = 0.40
DIRECTION_WEIGHT = 0.35
AXIS_PURITY_WEIGHT = 0.10
DURATION_WEIGHT = 0.15

TOTAL_CONFIDENCE_WEIGHT = (
    DISPLACEMENT_WEIGHT + DIRECTION_WEIGHT + AXIS_PURITY_WEIGHT + DURATION_WEIGHT
)

# Confidence weights must represent a complete weighted average.
if abs(TOTAL_CONFIDENCE_WEIGHT - 1.0) >= 1e-9:
    raise ValueError("Confidence weights must sum to 1.0")


# ============================================================
# 2. GESTURE STATES AND CALIBRATION
# ============================================================


class GestureState(Enum):
    """Control whether the recognizer can accept another gesture."""

    GESTURE_READY = auto()
    GESTURE_ONGOING = auto()


@dataclass
class GestureRecognitionState:
    """Store the runtime state used for gesture re-arming.

    The cooldown and stationary checks prevent one continuous hand
    movement from generating multiple gesture events.
    """

    state: GestureState = GestureState.GESTURE_READY
    last_gesture_time: float = 0.0

    # Time and position used to measure a stationary interval.
    stationary_start_time: float | None = None
    stationary_start_position: tuple[float, float] | None = None


@dataclass(frozen=True)
class GestureCalibration:
    """Hold recognition settings for future user customization.

    Defaults match the tested recognition configuration.
    The recognizer still uses module-level constants until the
    calibration object is integrated in a later step.
    """

    # Horizontal swipe requirements.
    min_displacement: float = MIN_DISPLACEMENT
    ideal_displacement: float = IDEAL_DISPLACEMENT
    min_direction_consistency: float = MIN_DIRECTION_CONSISTENCY
    min_axis_purity: float = MIN_AXIS_PURITY

    # Accepted and ideal movement durations.
    min_swipe_duration: float = MIN_SWIPE_DURATION
    ideal_min_duration: float = IDEAL_MIN_DURATION
    ideal_max_duration: float = IDEAL_MAX_DURATION
    max_swipe_duration: float = MAX_SWIPE_DURATION

    # Final recognition confidence threshold.
    confidence_threshold: float = CONFIDENCE_THRESHOLD

    # Cooldown and stationary requirements for re-arming.
    swipe_cooldown: float = SWIPE_COOLDOWN
    stationary_duration: float = GESTURE_STATIONARY_DURATION
    stationary_threshold: float = GESTURE_STATIONARY_THRESHOLD

    def __post_init__(self):
        """Validate calibration settings before they are used."""

        # Displacement thresholds must be ordered correctly.
        if not 0 <= self.min_displacement < self.ideal_displacement:
            raise ValueError(
                "Minimum displacement must be non-negative "
                "and less than ideal displacement."
            )

        # Direction consistency and axis purity are normalized scores.
        if not 0 <= self.min_direction_consistency <= 1:
            raise ValueError("Direction consistency must be between 0 and 1.")

        if not 0 <= self.min_axis_purity <= 1:
            raise ValueError("Axis purity must be between 0 and 1.")

        # Duration thresholds must progress from minimum to maximum.
        if not (
            0
            <= self.min_swipe_duration
            < self.ideal_min_duration
            <= self.ideal_max_duration
            < self.max_swipe_duration
        ):
            raise ValueError("Swipe duration thresholds must be ordered correctly.")

        # Confidence is a normalized score.
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1.")

        # Re-arming requirements cannot be negative.
        if self.swipe_cooldown < 0:
            raise ValueError("Swipe cooldown cannot be negative.")

        if self.stationary_duration < 0:
            raise ValueError("Stationary duration cannot be negative.")

        if not 0 <= self.stationary_threshold <= 1:
            raise ValueError("Stationary threshold must be between 0 and 1.")


# ============================================================
# 3. CONFIDENCE SCORING HELPERS
# ============================================================


def clamp(value):
    """Restrict a score to the range [0.0, 1.0]."""
    return max(0.0, min(value, 1.0))


def calculate_displacement_score(
    displacement,
    calibration: GestureCalibration | None = None,
):
    """Score swipe displacement using the configured thresholds."""
    if calibration is None:
        calibration = GestureCalibration()

    score = (displacement - calibration.min_displacement) / (
        calibration.ideal_displacement - calibration.min_displacement
    )

    return clamp(score)


def calculate_axis_purity(primary_displacement, off_axis_displacement):
    """Measure how much movement occurred along the intended axis.

    Horizontal swipes should have more horizontal than vertical
    displacement, although some diagonal movement is acceptable.
    """
    total_displacement = primary_displacement + off_axis_displacement

    if total_displacement == 0:
        return 0.0

    return primary_displacement / total_displacement


def calculate_duration_score(
    duration,
    calibration: GestureCalibration | None = None,
):
    """Score swipe duration against the configured time ranges."""
    if calibration is None:
        calibration = GestureCalibration()

    if (
        duration < calibration.min_swipe_duration
        or duration > calibration.max_swipe_duration
    ):
        return 0.0

    if calibration.ideal_min_duration <= duration <= calibration.ideal_max_duration:
        return 1.0

    if duration < calibration.ideal_min_duration:
        score = (duration - calibration.min_swipe_duration) / (
            calibration.ideal_min_duration - calibration.min_swipe_duration
        )
        return clamp(score)

    score = (calibration.max_swipe_duration - duration) / (
        calibration.max_swipe_duration - calibration.ideal_max_duration
    )

    return clamp(score)


def calculate_swipe_confidence(
    displacement,
    direction_consistency,
    axis_purity,
    duration,
    calibration: GestureCalibration | None = None,
):
    """Calculate gesture confidence using the provided calibration.

    A default calibration is used when no custom settings are provided.
    The confidence weights remain unchanged.
    """
    if calibration is None:
        calibration = GestureCalibration()

    displacement_score = calculate_displacement_score(
        displacement,
        calibration=calibration,
    )

    duration_score = calculate_duration_score(
        duration,
        calibration=calibration,
    )

    confidence = (
        DISPLACEMENT_WEIGHT * displacement_score
        + DIRECTION_WEIGHT * direction_consistency
        + AXIS_PURITY_WEIGHT * axis_purity
        + DURATION_WEIGHT * duration_score
    )

    return clamp(confidence)


# ============================================================
# 4. STATIONARY MOVEMENT DETECTION
# ============================================================


def is_hand_stationary(
    position_history: deque[tuple[float, float, float]],
    calibration: GestureCalibration | None = None,
) -> bool:
    """Check whether the latest two positions show minimal movement."""
    if calibration is None:
        calibration = GestureCalibration()
    """Check whether the latest two positions show minimal movement.

    This check is used while GESTURE_READY to prevent stationary
    samples from accumulating in the swipe history.

    Re-arming uses a separate position-anchor check so that slow,
    continuous movement cannot satisfy the stationary timer.
    """
    if len(position_history) < 2:
        return False

    # History samples contain (timestamp, x, y).
    previous_x = position_history[-2][1]
    previous_y = position_history[-2][2]

    current_x = position_history[-1][1]
    current_y = position_history[-1][2]

    movement_x = abs(current_x - previous_x)
    movement_y = abs(current_y - previous_y)

    return (
        movement_x <= calibration.stationary_threshold
        and movement_y <= calibration.stationary_threshold
    )


# ============================================================
# 5. MAIN SWIPE RECOGNITION
# ============================================================


def detect_swipe(
    hand_landmarks,
    position_history: deque[tuple[float, float, float]],
    gesture_state: GestureRecognitionState,
    current_time: float,
    calibration: GestureCalibration | None = None,
):
    """Detect a horizontal swipe and manage the gesture lifecycle.

    A gesture event is emitted only when displacement, direction,
    duration, cooldown, and confidence requirements are satisfied.

    After detection, the recognizer waits for both cooldown completion
    and a stationary interval before accepting another gesture.

    Uses default calibration settings unless custom settings are provided.
    """

    if calibration is None:
        calibration = GestureCalibration()

    # --------------------------------------------------------
    # A. Record the tracked hand position
    # --------------------------------------------------------

    # Landmark 9 is near the center of the hand.
    tracked_landmark = hand_landmarks[9]

    # Store timestamp and normalized horizontal/vertical positions.
    position_history.append(
        (
            current_time,
            tracked_landmark.x,
            tracked_landmark.y,
        )
    )

    # --------------------------------------------------------
    # B. Handle ongoing gestures and re-arming
    # --------------------------------------------------------

    if gesture_state.state == GestureState.GESTURE_ONGOING:
        current_x = tracked_landmark.x
        current_y = tracked_landmark.y

        # Establish an anchor when stationary tracking begins.
        if gesture_state.stationary_start_position is None:
            gesture_state.stationary_start_position = (current_x, current_y)
            gesture_state.stationary_start_time = current_time

        else:
            start_x, start_y = gesture_state.stationary_start_position

            movement_x = abs(current_x - start_x)
            movement_y = abs(current_y - start_y)

            # Reset the stationary interval when the hand moves
            # beyond the tolerance relative to the anchor.
            if (
                movement_x > calibration.stationary_threshold
                or movement_y > calibration.stationary_threshold
            ):
                gesture_state.stationary_start_position = (current_x, current_y)
                gesture_state.stationary_start_time = current_time

        # Both conditions are required before re-arming.
        cooldown_complete = (
            current_time - gesture_state.last_gesture_time >= calibration.swipe_cooldown
        )

        stationary_complete = (
            gesture_state.stationary_start_time is not None
            and current_time - gesture_state.stationary_start_time
            >= calibration.stationary_duration
        )

        if cooldown_complete and stationary_complete:
            gesture_state.state = GestureState.GESTURE_READY

            # Clear the stationary anchor and old movement samples.
            gesture_state.stationary_start_time = None
            gesture_state.stationary_start_position = None
            position_history.clear()

        # Never detect another swipe during this same call.
        return None

    # --------------------------------------------------------
    # C. Remove stationary history while ready
    # --------------------------------------------------------

    # Prevent nearly motionless samples from accumulating into
    # a misleading displacement or duration measurement.
    if is_hand_stationary(position_history, calibration=calibration):
        latest_position = position_history[-1]

        position_history.clear()
        position_history.append(latest_position)

    # At least two positions are required to measure movement.
    if len(position_history) <= 1:
        return None

    # --------------------------------------------------------
    # D. Calculate displacement and duration
    # --------------------------------------------------------

    starting_time, starting_x, starting_y = position_history[0]
    ending_time, ending_x, ending_y = position_history[-1]

    x_displacement = ending_x - starting_x
    y_displacement = ending_y - starting_y

    # Horizontal movement is the primary axis for a swipe.
    primary_displacement = abs(x_displacement)
    off_axis_displacement = abs(y_displacement)

    axis_purity = calculate_axis_purity(
        primary_displacement,
        off_axis_displacement,
    )

    movement_duration = ending_time - starting_time

    # --------------------------------------------------------
    # E. Calculate directional consistency
    # --------------------------------------------------------

    # Examine horizontal displacement between consecutive frames.
    frame_movements = []

    for index in range(1, len(position_history)):
        previous_x = position_history[index - 1][1]
        current_x = position_history[index][1]

        frame_movements.append(current_x - previous_x)

    if not frame_movements:
        return None

    # Count frames moving in each horizontal direction.
    right_movements = sum(movement > 0 for movement in frame_movements)
    left_movements = sum(movement < 0 for movement in frame_movements)

    right_consistency = right_movements / len(frame_movements)
    left_consistency = left_movements / len(frame_movements)

    gesture_name = ""
    direction_consistency = 0.0

    # Choose the gesture using the overall horizontal direction.
    if x_displacement > 0:
        gesture_name = "swipe_right"
        direction_consistency = right_consistency

    elif x_displacement < 0:
        gesture_name = "swipe_left"
        direction_consistency = left_consistency

    else:
        return None

    # --------------------------------------------------------
    # F. Validate the swipe candidate
    # --------------------------------------------------------

    valid_duration = (
        calibration.min_swipe_duration
        <= movement_duration
        <= calibration.max_swipe_duration
    )

    cooldown_complete = (
        ending_time - gesture_state.last_gesture_time >= calibration.swipe_cooldown
    )

    # Candidate must satisfy all minimum movement requirements.
    valid_candidate = (
        primary_displacement >= calibration.min_displacement
        and direction_consistency >= calibration.min_direction_consistency
        and axis_purity >= calibration.min_axis_purity
        and valid_duration
        and cooldown_complete
    )

    if not valid_candidate:
        return None

    # --------------------------------------------------------
    # G. Calculate and validate recognition confidence
    # --------------------------------------------------------

    confidence = calculate_swipe_confidence(
        primary_displacement,
        direction_consistency,
        axis_purity,
        movement_duration,
        calibration=calibration,
    )

    if confidence < calibration.confidence_threshold:
        return None

    # --------------------------------------------------------
    # H. Emit the gesture and enter the ongoing state
    # --------------------------------------------------------

    gesture_event = create_gesture_event(
        gesture_name,
        confidence,
        ending_time,
    )

    # Block further gestures until re-arming requirements are met.
    gesture_state.state = GestureState.GESTURE_ONGOING
    gesture_state.last_gesture_time = ending_time

    # Reset stationary tracking for the next re-arming cycle.
    gesture_state.stationary_start_time = None
    gesture_state.stationary_start_position = None

    # Start the next gesture with an empty movement history.
    position_history.clear()

    return gesture_event
