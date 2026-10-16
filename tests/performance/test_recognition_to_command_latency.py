"""Recognized swipe -> mock adapter receives command. CI-safe, no time limit yet."""

import time

from _pipeline import FIXTURE_SWIPES, FakeClock, Pipeline, summarize

from slidekick.presentation_adapter import PresentationAdapter
from slidekick.recognition import camera

WARMUP = 20
SAMPLES = 300


class TimingAdapter(PresentationAdapter):
    """Records each command and when it arrived."""

    def __init__(self):
        self.calls = []

    def _record(self, command: str) -> bool:
        self.calls.append((command, time.perf_counter_ns()))
        return True

    def next_slide(self) -> bool:
        return self._record("next")

    def previous_slide(self) -> bool:
        return self._record("previous")

    def pause_presentation(self) -> bool:
        return self._record("pause")

    def resume_presentation(self) -> bool:
        return self._record("resume")

    def end_presentation(self) -> bool:
        return self._record("end")


def test_recognition_to_command_latency(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(camera, "time", clock)
    adapter = TimingAdapter()
    pipeline = Pipeline(clock, adapter)

    samples_ns = []
    for i in range(WARMUP + SAMPLES):
        expected_command, x_positions = FIXTURE_SWIPES[i % 2]
        calls_before = len(adapter.calls)

        start = pipeline.run_swipe(x_positions)

        new_calls = adapter.calls[calls_before:]
        assert [command for command, _ in new_calls] == [expected_command]
        if i >= WARMUP:
            samples_ns.append(new_calls[0][1] - start)

    summarize("recognition_to_command_latency", samples_ns, details=f"warmup={WARMUP}")
