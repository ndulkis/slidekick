"""Recognized swipe -> real key press -> visible slide change. Local only.

Run: SLIDEKICK_E2E=1 python -m pytest tests/performance -s -k end_to_end
then start a slideshow on slide 1 during the countdown.
macOS needs Screen Recording + Accessibility for the terminal.
"""

import os
import threading
import time

import numpy as np
import pytest
from _pipeline import FIXTURE_SWIPES, FakeClock, Pipeline, report

from slidekick.presentation_adapter import KeyboardPresentationAdapter
from slidekick.recognition import camera

pytestmark = pytest.mark.skipif(
    os.environ.get("SLIDEKICK_E2E") != "1",
    reason="needs a display and a running slideshow; set SLIDEKICK_E2E=1",
)

TRIALS = int(os.environ.get("SLIDEKICK_E2E_TRIALS", "20"))
# Cold-start trials, excluded from median/p95.
WARMUP = 2
COUNTDOWN_S = int(os.environ.get("SLIDEKICK_E2E_COUNTDOWN", "5"))
CHANGE_TIMEOUT_S = 2.0
SETTLE_S = 1.0
CHANGE_FRACTION = 0.02
REGION_PX = 200


class KeyPressTimingAdapter(KeyboardPresentationAdapter):
    """Real key presses, timestamped."""

    def __init__(self):
        self.press_ns = []

    def next_slide(self) -> bool:
        self.press_ns.append(time.perf_counter_ns())
        return super().next_slide()

    def previous_slide(self) -> bool:
        self.press_ns.append(time.perf_counter_ns())
        return super().previous_slide()


class ScreenWatcher:
    """Polls the middle of the main monitor for a change."""

    def __init__(self, sct):
        self.sct = sct
        monitor = sct.monitors[1]
        self.region = {
            "left": monitor["left"] + monitor["width"] // 2 - REGION_PX // 2,
            "top": monitor["top"] + monitor["height"] // 2 - REGION_PX // 2,
            "width": REGION_PX,
            "height": REGION_PX,
        }
        self.grab_ns = []

    def grab(self):
        return np.frombuffer(self.sct.grab(self.region).raw, dtype=np.uint8)

    def watch(self):

        baseline = self.grab()
        result = {}

        def poll():
            deadline = time.perf_counter() + CHANGE_TIMEOUT_S
            while time.perf_counter() < deadline:
                before = time.perf_counter_ns()
                shot = self.grab()
                after = time.perf_counter_ns()
                self.grab_ns.append(after - before)
                if np.mean(shot != baseline) > CHANGE_FRACTION:
                    result["changed_ns"] = before
                    return

        thread = threading.Thread(target=poll)
        thread.start()
        return thread, result


def test_end_to_end_slide_latency(tmp_path, monkeypatch):
    mss = pytest.importorskip("mss")

    clock = FakeClock()
    monkeypatch.setattr(camera, "time", clock)
    adapter = KeyPressTimingAdapter()
    pipeline = Pipeline(clock, adapter)

    for remaining in range(COUNTDOWN_S, 0, -1):
        print(f"Switch to the slideshow now... {remaining}")
        time.sleep(1)

    rows = []
    with mss.mss() as sct:
        watcher = ScreenWatcher(sct)
        for i in range(TRIALS):
            command, x_positions = FIXTURE_SWIPES[i % 2]
            presses_before = len(adapter.press_ns)

            thread, result = watcher.watch()
            start = pipeline.run_swipe(x_positions)
            thread.join()

            assert len(adapter.press_ns) == presses_before + 1, (
                f"trial {i}: expected one key press"
            )
            assert "changed_ns" in result, (
                f"trial {i}: slide did not visibly change within {CHANGE_TIMEOUT_S}s "
                "(is the slideshow focused, and do slides 1 and 2 differ mid-screen?)"
            )
            press_ns = adapter.press_ns[-1]
            rows.append(
                (
                    i,
                    command,
                    i < WARMUP,
                    press_ns - start,
                    result["changed_ns"] - press_ns,
                    result["changed_ns"] - start,
                )
            )
            time.sleep(SETTLE_S)

    samples_ns = [total for *_, warmup, _, _, total in rows if not warmup]
    grab_ms = sorted(watcher.grab_ns)[len(watcher.grab_ns) // 2] / 1e6
    report(
        "end_to_end_slide_latency",
        [
            "trial",
            "command",
            "warmup",
            "recognition_to_keypress_ns",
            "keypress_to_visible_ns",
            "total_ns",
        ],
        rows,
        samples_ns,
        tmp_path,
        extra=f"warmup={WARMUP} screen_poll={grab_ms:.1f}ms ",
    )
