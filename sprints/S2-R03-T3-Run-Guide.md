# SlideKick Gesture Recognition Evaluation Test Guide

# Purpose
This guide defines a repeatable procedure for collecting baseline gesture-recognition samples for SlideKick. The goal is to measure recognition behavior without changing thresholds or recognition logic during the same dataset.

The current evaluation format uses a 4-second recording window and groups samples into trial rounds. One round contains exactly three trials:

Trial ID	Expected condition
tN-001	swipe_right
tN-002	swipe_left
tN-003	no_gesture


For example, round 4 consists of t4-001, t4-002, and t4-003.

# Before Testing
Keep the camera position, lighting, recognizer configuration, confidence threshold, and swipe thresholds unchanged for the entire dataset. If recognition logic is changed, start a new evaluation dataset so that results from different configurations are not mixed.

Run the quick project checks before collecting data:

uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src
uv run pytest tests/recognition tests/integration tests/unit/test_recognition_events.py -q

If Ruff reports formatting differences, run:

uv run ruff format src tests

For a new official evaluation run, use an empty JSONL output file. The recorder will recreate the file when the first sample is saved. Keep old datasets as separate archived files rather than mixing debug runs and official runs.

Launch the recognition camera from the repository root:

$env:PYTHONPATH="$PWD\src"
uv run python -m slidekick.recognition.camera

# Trial Procedure
1. Confirm that no trial is currently recording.
2. Press Space to arm the next sample. The console should display the next sample ID and expected condition.
3. Bring the hand into the camera in the intended starting position.
4. Wait for the console message indicating that the hand was detected and recording started.
5. For swipe_right, perform one deliberate right swipe during the 4-second window.
6. For swipe_left, perform one deliberate left swipe during the 4-second window.
7. For no_gesture, do not perform a valid horizontal swipe. Negative trials should include realistic non-swipe behavior rather than only a perfectly still hand.
8. Wait for the recorder to save the sample before pressing Space again.
9. Complete all three trials in the round before moving to the next round.

Do not repeat a sample simply because the recognizer missed it or produced a false positive. Recognition errors are valid evaluation data. Repeat or discard a trial only when the test protocol itself was performed incorrectly, such as performing the wrong gesture, an accidental interruption, or a camera failure that makes the sample unusable.

# Recommended no_gesture Variation

Across rounds, vary the negative condition to test false positives more realistically. Useful examples include a still hand, small repositioning, mostly vertical movement, diagonal movement, casual presenter-like hand movement, or moving the hand into and out of view without completing a horizontal swipe.

If future datasets need stronger analysis, add a field such as negative_scenario so each no_gesture trial records which type of negative motion was performed.

# Hand Consistency

For a clean direction comparison, use the same hand for both swipe directions, or explicitly record and balance the hand used across trials. Using one hand only for right swipes and another only for left swipes can couple hand identity with gesture direction and make later analysis harder.

# What Each Sample Should Record

Each JSONL sample should preserve:
- sample_id
- expected_gesture
- representative predicted_gesture
- confidence
- sample_start_time and sample_end_time
- prediction_time
- prediction_count
- correct
- complete predictions list
- per-frame hand landmarks

The complete predictions list is important because future tests may produce more than one recognition event within a trial.

# Data Quality Check After Collection

Verify that IDs are continuous and follow the three-sample round pattern. Confirm that each sample contains landmark frames when a hand was visible. At approximately 30 camera frames per second, a continuously tracked 4-second trial can contain roughly 120 landmark frames, although processing and hand-tracking losses can reduce that number.

Do not delete failed recognition samples. A missed swipe or false positive is exactly the type of evidence the baseline evaluation is intended to capture.

# Metrics to Report

Use the saved dataset to report:

## Metric	Meaning

Overall accuracy	Correct trials divided by all trials

Per-gesture recall	Correct detections of a gesture divided by trials where that gesture was expected

Per-gesture precision	Correct detections of a gesture divided by all times that gesture was predicted

False-positive rate	no_gesture trials that produced a gesture divided by all no_gesture trials

Confidence	Confidence distribution for true and false predictions

Detection delay	Prediction timestamp relative to a defined start point

Tracking coverage	Number of saved landmark frames per trial


For latency, prediction_time - sample_start_time should be described as sample-to-prediction delay, not pure algorithm latency, because it includes the tester's reaction time before beginning the gesture. A better algorithm-latency measurement uses a detected movement-onset timestamp or explicit instrumentation inside the recognizer.

# Reproducibility Notes

Record the recognizer configuration used for the dataset and avoid tuning it until the baseline run is complete. After tuning, repeat the same protocol with a new file so before/after results can be compared directly.