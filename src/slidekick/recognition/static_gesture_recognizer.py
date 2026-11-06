"""Extract custom static gesture candidates from MediaPipe results."""

import math
from dataclasses import dataclass

# Initial experimental threshold; tune during evaluation.
STATIC_CONFIDENCE_THRESHOLD = 0.60

# These categories must not activate custom commands.
IGNORED_GESTURES = {"none", "unknown"}

STATIC_HOLD_DURATION = 0.40
STATIC_RELEASE_DURATION = 0.25


@dataclass
class StaticGestureState:
    """Track static gesture hold and re-arming state."""

    candidate_name: str | None = None
    candidate_start_time: float | None = None

    # True after activation, until a deliberate release occurs.
    activated: bool = False

    # When the gesture first disappeared.
    release_start_time: float | None = None


def get_static_gesture_candidate(
    result,
    min_confidence=STATIC_CONFIDENCE_THRESHOLD,
):
    """Return a static gesture candidate or None.

    This function only interprets classifier output.
    It does not emit events or execute presentation commands.
    """

    # No predictions or no detected hand.
    if not result.hand_landmarks or not result.gestures:
        return None

    # MediaPipe returns gesture classifications grouped by hand.
    first_hand_predictions = result.gestures[0]

    if not first_hand_predictions:
        return None

    # Choose the highest-scoring classification.
    prediction = max(
        first_hand_predictions,
        key=lambda category: category.score,
    )

    gesture_name = prediction.category_name
    confidence = float(prediction.score)

    # Reject missing labels and invalid confidence values.
    if not gesture_name or not math.isfinite(confidence):
        return None

    # "none" indicates that no custom gesture was recognized.
    if gesture_name.lower() in IGNORED_GESTURES:
        return None

    # Reject low-confidence predictions.
    if confidence < min_confidence:
        return None

    return {
        "gesture": gesture_name,
        "confidence": confidence,
    }


def update_static_gesture(
    candidate,
    state: StaticGestureState,
    current_time: float,
    motion_suppressed: bool = False,
):
    """Return an accepted static gesture once per deliberate hold.

    candidate:
        Dictionary from get_static_gesture_candidate(), or None.

    motion_suppressed:
        True when the arbitration system detects meaningful motion.

    This function does not execute commands or emit events.
    """

    # Meaningful motion cancels any pending static hold.
    if motion_suppressed:
        if not state.activated:
            state.candidate_name = None
            state.candidate_start_time = None

        state.release_start_time = None
        return None

    # No valid gesture candidate.
    if candidate is None:
        if state.release_start_time is None:
            state.release_start_time = current_time

        # A brief tracking loss should not immediately re-arm.
        if current_time - state.release_start_time >= STATIC_RELEASE_DURATION:
            state.candidate_name = None
            state.candidate_start_time = None
            state.activated = False

        return None

    # A valid candidate has appeared.
    state.release_start_time = None

    # Already activated: do not trigger again until released.
    if state.activated:
        return None

    gesture_name = candidate["gesture"]

    # A new gesture starts a fresh hold period.
    if gesture_name != state.candidate_name:
        state.candidate_name = gesture_name
        state.candidate_start_time = current_time
        return None

    # The same candidate must remain stable long enough.
    if state.candidate_start_time is None:
        state.candidate_start_time = current_time
        return None

    held_duration = current_time - state.candidate_start_time

    if held_duration < STATIC_HOLD_DURATION and not math.isclose(
        held_duration,
        STATIC_HOLD_DURATION,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        return None

    # Accept the gesture once.
    state.activated = True

    return candidate
