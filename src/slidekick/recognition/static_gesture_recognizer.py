"""Extract custom static gesture candidates from MediaPipe results."""

import math

# Initial experimental threshold; tune during evaluation.
STATIC_CONFIDENCE_THRESHOLD = 0.60

# These categories must not activate custom commands.
IGNORED_GESTURES = {"none", "unknown"}


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
