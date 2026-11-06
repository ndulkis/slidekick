"""Unit tests for custom static gesture classification."""

from types import SimpleNamespace

from slidekick.recognition.static_gesture_recognizer import (
    StaticGestureState,
    get_static_gesture_candidate,
    update_static_gesture,
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


def test_static_gesture_requires_hold():
    state = StaticGestureState()
    pinch = {"gesture": "pinch", "confidence": 0.90}

    assert update_static_gesture(pinch, state, 1.0) is None
    assert update_static_gesture(pinch, state, 1.2) is None

    result = update_static_gesture(pinch, state, 1.4)

    assert result == pinch
    assert state.activated is True


def test_static_gesture_triggers_only_once():
    state = StaticGestureState()
    pinch = {"gesture": "pinch", "confidence": 0.90}

    update_static_gesture(pinch, state, 1.0)
    assert update_static_gesture(pinch, state, 1.5) == pinch

    assert update_static_gesture(pinch, state, 2.0) is None
    assert update_static_gesture(pinch, state, 3.0) is None


def test_short_release_does_not_rearm():
    state = StaticGestureState()
    pinch = {"gesture": "pinch", "confidence": 0.90}

    update_static_gesture(pinch, state, 1.0)
    update_static_gesture(pinch, state, 1.5)

    update_static_gesture(None, state, 1.6)
    update_static_gesture(pinch, state, 1.7)

    assert state.activated is True
    assert update_static_gesture(pinch, state, 2.0) is None


def test_full_release_allows_new_activation():
    state = StaticGestureState()
    pinch = {"gesture": "pinch", "confidence": 0.90}

    update_static_gesture(pinch, state, 1.0)
    update_static_gesture(pinch, state, 1.5)

    update_static_gesture(None, state, 2.0)
    update_static_gesture(None, state, 2.3)

    assert state.activated is False

    update_static_gesture(pinch, state, 3.0)

    assert update_static_gesture(pinch, state, 3.5) == pinch


def test_motion_cancels_pending_hold():
    state = StaticGestureState()
    pinch = {"gesture": "pinch", "confidence": 0.90}

    update_static_gesture(pinch, state, 1.0)

    # The hand begins moving before the hold completes.
    assert (
        update_static_gesture(
            pinch,
            state,
            1.2,
            motion_suppressed=True,
        )
        is None
    )

    # Must start another full hold after movement stops.
    assert update_static_gesture(pinch, state, 1.3) is None
    assert update_static_gesture(pinch, state, 1.5) is None

    assert update_static_gesture(pinch, state, 1.8) == pinch


def test_switching_gestures_restarts_hold():
    state = StaticGestureState()

    pinch = {"gesture": "pinch", "confidence": 0.90}
    open_palm = {"gesture": "open_palm", "confidence": 0.90}

    update_static_gesture(pinch, state, 1.0)

    assert update_static_gesture(open_palm, state, 1.2) is None
    assert update_static_gesture(open_palm, state, 1.4) is None

    assert update_static_gesture(open_palm, state, 1.7) == open_palm
