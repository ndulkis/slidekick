"""Integration tests for static gesture motion arbitration."""

from types import SimpleNamespace

from slidekick.recognition.gesture_arbitration import (
    GestureArbitrationState,
    SwipeStaticArbitrationState,
    arbitrate_static_gesture,
    detect_meaningful_motion,
)
from slidekick.recognition.static_gesture_recognizer import (
    StaticGestureState,
    update_static_gesture,
)


def make_hand(x=0.5, y=0.5):
    """Create 21 simulated MediaPipe hand landmarks."""
    return [SimpleNamespace(x=x, y=y, z=0.0) for _ in range(21)]


def process_frame(
    candidate,
    x,
    timestamp,
    motion_state,
    static_state,
):
    """Simulate one frame processed by both components."""

    moving = detect_meaningful_motion(
        make_hand(x),
        motion_state,
        timestamp,
    )

    return update_static_gesture(
        candidate,
        static_state,
        timestamp,
        motion_suppressed=moving,
    )


def test_stationary_palm_activates_once():
    motion_state = GestureArbitrationState()
    static_state = StaticGestureState()
    palm = {"gesture": "open_palm", "confidence": 0.95}

    assert process_frame(palm, 0.5, 1.0, motion_state, static_state) is None

    assert process_frame(palm, 0.5, 1.2, motion_state, static_state) is None

    assert process_frame(palm, 0.5, 1.5, motion_state, static_state) == palm

    # Continuous holding must not activate again.
    assert process_frame(palm, 0.5, 2.0, motion_state, static_state) is None


def test_moving_palm_cancels_static_hold():
    motion_state = GestureArbitrationState()
    static_state = StaticGestureState()
    palm = {"gesture": "open_palm", "confidence": 0.95}

    # Hand initially stationary.
    assert process_frame(palm, 0.40, 1.0, motion_state, static_state) is None

    # Hand moves horizontally, as during a swipe.
    assert process_frame(palm, 0.48, 1.1, motion_state, static_state) is None

    assert process_frame(palm, 0.56, 1.2, motion_state, static_state) is None

    # The original hold must have been canceled.
    assert static_state.activated is False

    # Hand settles. A new hold period is required.
    assert process_frame(palm, 0.56, 1.5, motion_state, static_state) is None

    assert process_frame(palm, 0.56, 1.7, motion_state, static_state) is None


def test_static_hold_does_not_repeat_after_motion():
    motion_state = GestureArbitrationState()
    static_state = StaticGestureState()
    pinch = {"gesture": "pinch", "confidence": 0.90}

    process_frame(pinch, 0.5, 1.0, motion_state, static_state)

    assert process_frame(pinch, 0.5, 1.5, motion_state, static_state) == pinch

    # Move the hand while continuing the same pose.
    assert process_frame(pinch, 0.6, 1.6, motion_state, static_state) is None

    # Remaining in the same pose must not retrigger.
    assert process_frame(pinch, 0.6, 2.0, motion_state, static_state) is None

    assert static_state.activated is True


def test_swipe_prevents_static_activation():
    motion = GestureArbitrationState()
    static = StaticGestureState()
    arbitration = SwipeStaticArbitrationState()

    palm = {"gesture": "open_palm", "confidence": 0.95}
    swipe = {"event_type": "gesture", "gesture": "swipe_right"}

    # User begins with an open palm.
    assert (
        arbitrate_static_gesture(
            palm,
            make_hand(0.40),
            1.0,
            motion,
            static,
            arbitration,
        )
        is None
    )

    # A swipe is recognized while the palm moves.
    assert (
        arbitrate_static_gesture(
            palm,
            make_hand(0.60),
            1.2,
            motion,
            static,
            arbitration,
            swipe_event=swipe,
        )
        is None
    )

    # The hand stops, but the same palm remains visible.
    assert (
        arbitrate_static_gesture(
            palm,
            make_hand(0.60),
            2.0,
            motion,
            static,
            arbitration,
        )
        is None
    )

    assert (
        arbitrate_static_gesture(
            palm,
            make_hand(0.60),
            3.0,
            motion,
            static,
            arbitration,
        )
        is None
    )

    # Time passing alone must not activate the palm.
    assert static.activated is False


def test_static_works_after_swipe_and_deliberate_release():
    motion = GestureArbitrationState()
    static = StaticGestureState()
    arbitration = SwipeStaticArbitrationState()

    palm = {"gesture": "open_palm", "confidence": 0.95}
    swipe = {"event_type": "gesture", "gesture": "swipe_right"}

    arbitrate_static_gesture(
        palm,
        make_hand(0.40),
        1.0,
        motion,
        static,
        arbitration,
    )

    arbitrate_static_gesture(
        palm,
        make_hand(0.60),
        1.2,
        motion,
        static,
        arbitration,
        swipe_event=swipe,
    )

    # Release the pose for longer than 250 ms.
    arbitrate_static_gesture(
        None,
        make_hand(0.60),
        1.5,
        motion,
        static,
        arbitration,
    )

    arbitrate_static_gesture(
        None,
        make_hand(0.60),
        1.8,
        motion,
        static,
        arbitration,
    )

    assert arbitration.requires_release is False

    # Wait until the post-swipe suppression expires.
    assert (
        arbitrate_static_gesture(
            palm,
            make_hand(0.60),
            2.0,
            motion,
            static,
            arbitration,
        )
        is None
    )

    # A new deliberate hold may activate.
    result = arbitrate_static_gesture(
        palm,
        make_hand(0.60),
        2.5,
        motion,
        static,
        arbitration,
    )

    assert result == palm


def test_motion_does_not_rearm_activated_static():
    motion = GestureArbitrationState()
    static = StaticGestureState()
    arbitration = SwipeStaticArbitrationState()

    pinch = {"gesture": "pinch", "confidence": 0.90}

    arbitrate_static_gesture(
        pinch,
        make_hand(0.50),
        1.0,
        motion,
        static,
        arbitration,
    )

    assert (
        arbitrate_static_gesture(
            pinch,
            make_hand(0.50),
            1.5,
            motion,
            static,
            arbitration,
        )
        == pinch
    )

    # Moving the hand does not count as releasing the pose.
    assert (
        arbitrate_static_gesture(
            pinch,
            make_hand(0.65),
            1.6,
            motion,
            static,
            arbitration,
        )
        is None
    )

    assert (
        arbitrate_static_gesture(
            pinch,
            make_hand(0.65),
            2.5,
            motion,
            static,
            arbitration,
        )
        is None
    )

    assert static.activated is True
