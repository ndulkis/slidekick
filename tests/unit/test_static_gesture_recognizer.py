"""Unit tests for custom static gesture classification."""

from types import SimpleNamespace

from slidekick.recognition.static_gesture_recognizer import (
    get_static_gesture_candidate,
)


def make_result(label="pinch", confidence=0.90, has_hand=True):
    """Create a simple MediaPipe-like recognition result."""
    return SimpleNamespace(
        hand_landmarks=[[object()]] if has_hand else [],
        gestures=[
            [
                SimpleNamespace(
                    category_name=label,
                    score=confidence,
                )
            ]
        ],
    )


def test_recognizes_custom_gesture():
    result = make_result("pinch", 0.90)

    candidate = get_static_gesture_candidate(result)

    assert candidate == {
        "gesture": "pinch",
        "confidence": 0.90,
    }


def test_rejects_none_gesture():
    result = make_result("none", 0.95)

    assert get_static_gesture_candidate(result) is None


def test_rejects_low_confidence():
    result = make_result("pinch", 0.40)

    assert get_static_gesture_candidate(result) is None


def test_rejects_missing_hand():
    result = make_result(has_hand=False)

    assert get_static_gesture_candidate(result) is None


def test_rejects_empty_predictions():
    result = SimpleNamespace(
        hand_landmarks=[[object()]],
        gestures=[],
    )

    assert get_static_gesture_candidate(result) is None


def test_accepts_confidence_at_threshold():
    result = make_result("pinch", 0.60)

    assert get_static_gesture_candidate(result) is not None


def test_rejects_invalid_confidence():
    result = make_result("pinch", float("nan"))

    assert get_static_gesture_candidate(result) is None
