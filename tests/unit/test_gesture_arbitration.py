"""Unit tests for static gesture motion suppression."""

from types import SimpleNamespace

from slidekick.recognition.gesture_arbitration import (
    GestureArbitrationState,
    detect_meaningful_motion,
)


def make_hand(x=0.5, y=0.5):
    """Create a MediaPipe-like set of 21 hand landmarks."""
    return [SimpleNamespace(x=x, y=y, z=0.0) for _ in range(21)]


def test_stationary_hand_is_not_suppressed():
    state = GestureArbitrationState()

    assert not detect_meaningful_motion(make_hand(), state, 1.0)
    assert not detect_meaningful_motion(make_hand(), state, 1.1)
    assert not detect_meaningful_motion(make_hand(), state, 1.2)


def test_horizontal_motion_suppresses_static():
    state = GestureArbitrationState()

    detect_meaningful_motion(make_hand(0.40), state, 1.0)

    assert detect_meaningful_motion(make_hand(0.46), state, 1.1)


def test_vertical_motion_suppresses_static():
    state = GestureArbitrationState()

    detect_meaningful_motion(make_hand(y=0.40), state, 1.0)

    assert detect_meaningful_motion(make_hand(y=0.46), state, 1.1)


def test_small_jitter_does_not_suppress_static():
    state = GestureArbitrationState()

    detect_meaningful_motion(make_hand(0.500), state, 1.0)

    assert not detect_meaningful_motion(make_hand(0.505), state, 1.1)


def test_motion_history_expires():
    state = GestureArbitrationState()

    detect_meaningful_motion(make_hand(0.40), state, 1.0)
    detect_meaningful_motion(make_hand(0.50), state, 1.1)

    # Old movement should not suppress a later steady hand.
    assert not detect_meaningful_motion(make_hand(0.50), state, 1.5)


def test_invalid_landmarks_suppress_static():
    state = GestureArbitrationState()

    assert detect_meaningful_motion([], state, 1.0)
    assert len(state.position_history) == 0
