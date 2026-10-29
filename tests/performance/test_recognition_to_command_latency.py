"""Recognized swipe -> mock adapter receives command. CI-safe, no time limit yet."""

from _pipeline import (
    FIXTURE_SWIPES,
    FakeClock,
    Pipeline,
    RecordingAdapter,
    summarize,
)

from slidekick.recognition import camera

WARMUP = 20
SAMPLES = 300


def test_recognition_to_command_latency(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(camera, "time", clock)
    adapter = RecordingAdapter()
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
