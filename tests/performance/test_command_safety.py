"""PERF-N01: fast or failing input must not send extra or stuck commands."""

import pytest
from _pipeline import FPS, FakeClock, Pipeline, RecordingAdapter

from slidekick.recognition import camera
from slidekick.recognition.swipe_recognizer import SWIPE_COOLDOWN

RIGHT = [0.30 + 0.03 * i for i in range(12)]
LEFT = list(reversed(RIGHT))


@pytest.fixture
def clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(camera, "time", clock)
    return clock


def test_hand_waving_back_and_forth_sends_one_command(clock):
    adapter = RecordingAdapter()
    pipeline = Pipeline(clock, adapter)

    # Right, back left, right again: 36 frames at 30 fps, inside the cooldown.
    for x in RIGHT + LEFT + RIGHT:
        pipeline.feed(x)

    assert adapter.commands() == ["next"]


@pytest.mark.xfail(
    strict=True,
    reason="Known issue: 120 FPS movement is incorrectly classified as stationary",
)
def test_high_frame_rate_swipe_sends_one_command(clock):
    adapter = RecordingAdapter()
    pipeline = Pipeline(clock, adapter)

    # Same distance as RIGHT, sampled at 120 fps.
    for i in range(48):
        pipeline.feed(0.30 + 0.0075 * i, fps=120)

    assert adapter.commands() == ["next"]


def test_swipe_after_cooldown_is_accepted(clock):
    adapter = RecordingAdapter()
    pipeline = Pipeline(clock, adapter)

    # Complete the cooldown while the hand is stationary.
    stationary_frames = int((SWIPE_COOLDOWN + 0.5) * FPS)

    for x in RIGHT + LEFT:
        pipeline.feed(x)

    for _ in range(stationary_frames):
        pipeline.feed(LEFT[0])

    for x in LEFT:
        pipeline.feed(x)

    assert adapter.commands() == ["next", "previous"]


class FailOnceAdapter(RecordingAdapter):
    def __init__(self):
        super().__init__()
        self.failed = False

    def next_slide(self) -> bool:
        if not self.failed:
            self.failed = True
            raise RuntimeError("adapter failed")
        return super().next_slide()


def test_adapter_failure_is_raised_and_next_swipe_still_works(clock):
    adapter = FailOnceAdapter()
    pipeline = Pipeline(clock, adapter)

    # Raised, not swallowed. Note run_camera doesn't catch it, so the real app exits.
    with pytest.raises(RuntimeError, match="adapter failed"):
        pipeline.run_swipe(RIGHT)

    pipeline.run_swipe(RIGHT)

    assert adapter.commands() == ["next"]


class RejectingAdapter(RecordingAdapter):
    def next_slide(self) -> bool:
        self._record("next")
        return False


def test_rejected_command_does_not_block_later_commands(clock):
    adapter = RejectingAdapter()
    pipeline = Pipeline(clock, adapter)

    pipeline.run_swipe(RIGHT)
    pipeline.run_swipe(LEFT)

    assert adapter.commands() == ["next", "previous"]
