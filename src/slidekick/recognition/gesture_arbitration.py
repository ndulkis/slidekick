"""Detect hand movement that should suppress static gestures."""

import math
from collections import deque
from dataclasses import dataclass, field

from .static_gesture_recognizer import (
    STATIC_RELEASE_DURATION,
    StaticGestureState,
    update_static_gesture,
)

# Initial experimental values (normalized hand coordinates).
MOTION_WINDOW_SECONDS = 0.20
MOTION_DISPLACEMENT_THRESHOLD = 0.04

# Use multiple palm landmarks to reduce single-point jitter.
PALM_LANDMARK_IDS = (0, 5, 9, 13, 17)


# Initial post-swipe suppression period in seconds.
POST_SWIPE_SUPPRESSION = 0.60


@dataclass
class SwipeStaticArbitrationState:
    """Track suppression following accepted swipe gestures."""

    blocked_until: float = 0.0
    requires_release: bool = False
    release_start_time: float | None = None


@dataclass
class GestureArbitrationState:
    """Store recent hand positions independently from swipe history."""

    position_history: deque = field(default_factory=deque)


def get_palm_center(hand_landmarks):
    """Return the normalized center of the palm."""
    if len(hand_landmarks) < 21:
        return None

    points = [hand_landmarks[i] for i in PALM_LANDMARK_IDS]

    x = sum(point.x for point in points) / len(points)
    y = sum(point.y for point in points) / len(points)

    if not math.isfinite(x) or not math.isfinite(y):
        return None

    return x, y


def detect_meaningful_motion(
    hand_landmarks,
    state: GestureArbitrationState,
    current_time: float,
):
    """Return True when the hand has moved significantly.

    This detects motion for static gesture suppression.
    It does NOT recognize swipes or generate events.
    """

    palm_center = get_palm_center(hand_landmarks)

    if palm_center is None:
        state.position_history.clear()
        return True  # No reliable stationary-hand evidence.

    history = state.position_history

    history.append((current_time, *palm_center))

    # Retain only recent positions.
    while history and current_time - history[0][0] > MOTION_WINDOW_SECONDS:
        history.popleft()

    # Not enough observations to estimate movement.
    if len(history) < 2:
        return False

    # Compare current position against recent positions.
    current_x, current_y = palm_center

    for _, previous_x, previous_y in history:
        displacement = math.hypot(
            current_x - previous_x,
            current_y - previous_y,
        )

        if displacement >= MOTION_DISPLACEMENT_THRESHOLD:
            return True

    return False


def arbitrate_static_gesture(
    candidate,
    hand_landmarks,
    current_time: float,
    motion_state: GestureArbitrationState,
    static_state: StaticGestureState,
    arbitration_state: SwipeStaticArbitrationState,
    swipe_event=None,
):
    """Accept a static gesture only when it does not conflict with a swipe.

    swipe_event is an already accepted event from the swipe recognizer.
    This function does not emit or execute presentation commands.
    """

    # A completed swipe takes priority over static recognition.
    if swipe_event is not None:
        arbitration_state.blocked_until = current_time + POST_SWIPE_SUPPRESSION
        arbitration_state.requires_release = True
        arbitration_state.release_start_time = None

    # Detect movement independently from swipe classification.
    is_moving = detect_meaningful_motion(
        hand_landmarks,
        motion_state,
        current_time,
    )

    # Track deliberate release following a swipe.
    if arbitration_state.requires_release:
        if candidate is None:
            if arbitration_state.release_start_time is None:
                arbitration_state.release_start_time = current_time

            release_duration = current_time - arbitration_state.release_start_time

            if release_duration >= STATIC_RELEASE_DURATION:
                arbitration_state.requires_release = False
                arbitration_state.release_start_time = None
        else:
            arbitration_state.release_start_time = None

    # A missing candidate must still reach the hold detector so
    # its existing release/re-arming logic can run.
    if candidate is None:
        return update_static_gesture(
            None,
            static_state,
            current_time,
        )

    # Suppress while moving, during the post-swipe window,
    # or until the gesture has been deliberately released.
    suppressed = (
        is_moving
        or current_time < arbitration_state.blocked_until
        or arbitration_state.requires_release
    )

    return update_static_gesture(
        candidate,
        static_state,
        current_time,
        motion_suppressed=suppressed,
    )
