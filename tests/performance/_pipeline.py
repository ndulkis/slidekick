"""Shared latency-test helpers: fake swipes through the real per-frame code."""

import csv
import os
import platform
import statistics
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from slidekick.gesture_command_controller import GestureCommandController
from slidekick.recognition import camera
from slidekick.recognition.swipe_recognizer import SWIPE_COOLDOWN

FPS = 30
FIXTURE_SWIPES = [
    ("next", [0.30 + 0.03 * i for i in range(12)]),
    ("previous", [0.70 - 0.03 * i for i in range(12)]),
]


@dataclass
class FakeLandmark:
    x: float
    y: float
    z: float = 0.0


class FakeClock:
    """Replaces camera.time so swipes take fixture time, not wall time."""

    def __init__(self):
        self.now = 100.0

    def monotonic(self):
        return self.now


def fake_result(x):
    landmarks = [FakeLandmark(0.0, 0.0) for _ in range(21)]
    # The swipe recognizer tracks landmark 9.
    landmarks[9] = FakeLandmark(x, 0.50)
    return SimpleNamespace(hand_landmarks=[landmarks])


class Pipeline:
    """camera.run_camera's per-frame path. Needs camera.time patched to a FakeClock."""

    def __init__(self, clock, adapter):
        self.clock = clock
        self.controller = GestureCommandController(adapter=adapter)
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.position_history = deque(maxlen=45)
        self.last_swipe_time = 0.0
        self.missed_hand_frames = 0

    def run_swipe(self, x_positions) -> int:
        """Returns perf_counter_ns() at the start of the frame that recognized the swipe."""
        self.clock.now += SWIPE_COOLDOWN + 0.5

        for x in x_positions:
            self.clock.now += 1 / FPS
            start = time.perf_counter_ns()

            (
                gesture_event,
                landmark_event,
                self.last_swipe_time,
                self.missed_hand_frames,
            ) = camera.process_hand_detection(
                fake_result(x),
                self.frame,
                self.position_history,
                self.last_swipe_time,
                self.missed_hand_frames,
            )
            camera.emit_event(gesture_event, self.controller.handle_event)
            camera.emit_event(landmark_event, self.controller.handle_event)

            if gesture_event is not None:
                return start

        raise AssertionError("swipe was never recognized")


def report(name, header, rows, samples_ns, tmp_path, extra=""):
    """Write CSV (to SLIDEKICK_PERF_DIR or tmp_path) and print median/p95."""
    out_dir = Path(os.environ.get("SLIDEKICK_PERF_DIR") or tmp_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{name}.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    median_ms = statistics.median(samples_ns) / 1e6
    p95_ms = statistics.quantiles(samples_ns, n=100)[94] / 1e6
    print(
        f"\n{name}: n={len(samples_ns)} median={median_ms:.3f}ms p95={p95_ms:.3f}ms "
        f"min={min(samples_ns) / 1e6:.3f}ms max={max(samples_ns) / 1e6:.3f}ms {extra}"
        f"python={platform.python_version()} os={platform.platform()} raw={csv_path}"
    )
