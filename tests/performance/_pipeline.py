"""Shared latency-test helpers: fake swipes through the real per-frame code."""

import csv
import os
import platform
import statistics
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from slidekick.gesture_command_controller import GestureCommandController
from slidekick.presentation_adapter import PresentationAdapter
from slidekick.recognition import camera
from slidekick.recognition.swipe_recognizer import (
    SWIPE_COOLDOWN,
    GestureRecognitionState,
)

RESULTS_DIR = Path(__file__).resolve().parents[2] / "perf-results"
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
    if x is None:
        return SimpleNamespace(hand_landmarks=[])
    landmarks = [FakeLandmark(0.0, 0.0) for _ in range(21)]
    # The swipe recognizer tracks landmark 9.
    landmarks[9] = FakeLandmark(x, 0.50)
    return SimpleNamespace(hand_landmarks=[landmarks])


class RecordingAdapter(PresentationAdapter):
    """Records each command and when it arrived."""

    def __init__(self):
        self.calls = []

    def commands(self):
        return [command for command, _ in self.calls]

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


class Pipeline:
    """camera.run_camera's per-frame path. Needs camera.time patched to a FakeClock."""

    def __init__(self, clock, adapter):
        self.clock = clock
        self.controller = GestureCommandController(adapter=adapter)
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.position_history = deque(maxlen=45)
        self.gesture_state = GestureRecognitionState()
        self.missed_hand_frames = 0

    def feed(self, x, fps=FPS):
        """Process one frame with the hand at x (None: no hand). Returns any gesture event."""
        self.clock.now += 1 / fps
        (
            gesture_event,
            landmark_event,
            self.missed_hand_frames,
        ) = camera.process_hand_detection(
            fake_result(x),
            self.frame,
            self.position_history,
            self.gesture_state,
            self.missed_hand_frames,
        )
        camera.emit_event(gesture_event, self.controller.handle_event)
        camera.emit_event(landmark_event, self.controller.handle_event)
        return gesture_event

    def run_swipe(self, x_positions) -> int:
        """Run a swipe after satisfying recognition re-arming conditions."""

        # Allow the cooldown to finish.
        self.clock.now += SWIPE_COOLDOWN + 0.5

        # Keep the hand stationary before starting another gesture.
        stationary_frames = int(0.5 * FPS) + 1

        for _ in range(stationary_frames):
            self.feed(x_positions[0])

        # Measure only the actual swipe-processing frames.
        for x in x_positions:
            start = time.perf_counter_ns()

            if self.feed(x) is not None:
                return start

        raise AssertionError("swipe was never recognized")


def summarize(name, samples_ns, details=""):
    """Print and return median/p95 and run context."""
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    ms = [ns / 1e6 for ns in samples_ns]
    summary = {
        "timestamp": datetime.now().astimezone().strftime("%Y-%m-%d_%H%M%S"),
        "test": name,
        "n": len(ms),
        "median_ms": round(statistics.median(ms), 3),
        "p95_ms": round(statistics.quantiles(ms, n=100, method="inclusive")[94], 3),
        "min_ms": round(min(ms), 3),
        "max_ms": round(max(ms), 3),
        "details": details,
        "note": os.environ.get("SLIDEKICK_PERF_NOTE", ""),
        "commit": commit or "unknown",
        "python": platform.python_version(),
        "os": platform.platform(),
    }
    print("\n" + " ".join(f"{k}={v}" for k, v in summary.items()))

    # Shows on the GitHub Actions run page.
    if step_summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(step_summary, "a") as f:
            f.write(
                f"**{name}**: median {summary['median_ms']} ms, "
                f"p95 {summary['p95_ms']} ms (n={summary['n']}, {details})\n"
            )
    return summary


def save(summary, header, rows):
    """Write raw rows to perf-results/<timestamp>_<test>.csv and append to summary.csv."""
    RESULTS_DIR.mkdir(exist_ok=True)
    csv_path = RESULTS_DIR / f"{summary['timestamp']}_{summary['test']}.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    summary = {**summary, "raw_csv": csv_path.name}
    summary_path = RESULTS_DIR / "summary.csv"
    new_file = not summary_path.exists()
    with summary_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary))
        if new_file:
            writer.writeheader()
        writer.writerow(summary)
    print(f"saved {csv_path}")
