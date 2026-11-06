import json

from slidekick.recognition.sample_recorder import SampleRecorder


def read_samples(path):
    """Read saved JSONL samples into a list of dictionaries."""
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def test_no_gesture_without_predictions_is_correct(tmp_path):
    output_path = tmp_path / "samples.jsonl"
    recorder = SampleRecorder(output_path)

    recorder.start_sample("no_gesture", 100.0)
    recorder.finish_sample(104.0)

    samples = read_samples(output_path)

    assert len(samples) == 1

    sample = samples[0]
    assert sample["sample_id"] == "t1-001"
    assert sample["expected_gesture"] == "no_gesture"
    assert sample["predicted_gesture"] is None
    assert sample["prediction_count"] == 0
    assert sample["predictions"] == []
    assert sample["correct"] is True


def test_no_gesture_with_unexpected_prediction_is_incorrect(tmp_path):
    output_path = tmp_path / "samples.jsonl"
    recorder = SampleRecorder(output_path)

    recorder.start_sample("no_gesture", 100.0)

    recorder.record_prediction(
        {
            "event_type": "gesture",
            "gesture": "swipe_right",
            "confidence": 0.85,
            "timestamp": 101.0,
        }
    )

    recorder.finish_sample(104.0)

    sample = read_samples(output_path)[0]

    assert sample["expected_gesture"] == "no_gesture"
    assert sample["predicted_gesture"] == "swipe_right"
    assert sample["prediction_count"] == 1
    assert sample["correct"] is False
    assert sample["confidence"] == 0.85
    assert sample["prediction_time"] == 101.0


def test_matching_swipe_prediction_is_recorded_correctly(tmp_path):
    output_path = tmp_path / "samples.jsonl"
    recorder = SampleRecorder(output_path)

    recorder.start_sample("swipe_right", 100.0)

    recorder.record_prediction(
        {
            "event_type": "gesture",
            "gesture": "swipe_right",
            "confidence": 0.92,
            "timestamp": 101.5,
        }
    )

    recorder.finish_sample(104.0)

    sample = read_samples(output_path)[0]

    assert sample["expected_gesture"] == "swipe_right"
    assert sample["predicted_gesture"] == "swipe_right"
    assert sample["confidence"] == 0.92
    assert sample["prediction_time"] == 101.5
    assert sample["prediction_count"] == 1
    assert sample["correct"] is True


def test_multiple_predictions_preserve_original_count(tmp_path):
    output_path = tmp_path / "samples.jsonl"
    recorder = SampleRecorder(output_path)

    recorder.start_sample("swipe_left", 100.0)

    recorder.record_prediction(
        {
            "gesture": "swipe_right",
            "confidence": 0.70,
            "timestamp": 101.0,
        }
    )

    recorder.record_prediction(
        {
            "gesture": "swipe_left",
            "confidence": 0.90,
            "timestamp": 102.0,
        }
    )

    recorder.finish_sample(104.0)

    sample = read_samples(output_path)[0]

    assert sample["expected_gesture"] == "swipe_left"
    assert sample["predicted_gesture"] == "swipe_left"
    assert sample["prediction_count"] == 2
    assert len(sample["predictions"]) == 2
    assert sample["prediction_time"] == 102.0
    assert sample["correct"] is True


def test_sample_ids_progress_across_rounds(tmp_path):
    output_path = tmp_path / "samples.jsonl"
    recorder = SampleRecorder(output_path)

    expected_ids = [
        "t1-001",
        "t1-002",
        "t1-003",
        "t2-001",
        "t2-002",
        "t2-003",
    ]

    for i in range(6):
        start_time = 100.0 + i * 5.0
        recorder.start_sample("no_gesture", start_time)
        recorder.finish_sample(start_time + 4.0)

    samples = read_samples(output_path)

    assert len(samples) == 6
    assert [sample["sample_id"] for sample in samples] == expected_ids
    assert recorder.sample_count == 6
    assert recorder.next_sample_id == "t3-001"
    assert recorder.next_label_index == 0


def test_recorder_resumes_sample_numbering(tmp_path):
    output_path = tmp_path / "samples.jsonl"
    recorder = SampleRecorder(output_path)

    for i in range(4):
        start_time = 100.0 + i * 5.0
        recorder.start_sample("no_gesture", start_time)
        recorder.finish_sample(start_time + 4.0)

    # Simulate restarting the evaluation application.
    resumed_recorder = SampleRecorder(output_path)

    assert resumed_recorder.sample_count == 4
    assert resumed_recorder.next_sample_id == "t2-002"
    assert resumed_recorder.next_label_index == 1

    resumed_recorder.start_sample("no_gesture", 125.0)
    resumed_recorder.finish_sample(129.0)

    samples = read_samples(output_path)

    assert len(samples) == 5
    assert samples[-1]["sample_id"] == "t2-002"


def test_recorder_preserves_chronological_frame_timestamps(tmp_path):
    output_path = tmp_path / "samples.jsonl"
    recorder = SampleRecorder(output_path)

    recorder.start_sample("swipe_right", 100.0)

    for timestamp in [100.1, 100.2, 100.3]:
        recorder.record_landmarks(
            {
                "event_type": "landmarks",
                "timestamp": timestamp,
                "landmarks": [
                    {"id": 0, "x": 0.5, "y": 0.4, "z": 0.0},
                    {"id": 1, "x": 0.6, "y": 0.4, "z": -0.01},
                ],
            }
        )

    recorder.finish_sample(104.0)

    sample = read_samples(output_path)[0]

    timestamps = [frame["timestamp"] for frame in sample["frames"]]

    assert timestamps == [100.1, 100.2, 100.3]
    assert timestamps == sorted(timestamps)
    assert sample["sample_start_time"] == 100.0
    assert sample["sample_end_time"] == 104.0

    for frame in sample["frames"]:
        assert len(frame["landmarks"]) == 2
        assert frame["landmarks"][0]["id"] == 0
        assert frame["landmarks"][0]["x"] == 0.5


def test_known_dataset_counts_and_outcomes(tmp_path):
    """Verify sample IDs, prediction counts, and evaluation outcomes."""
    output_path = tmp_path / "known_dataset.jsonl"
    recorder = SampleRecorder(output_path)

    trials = [
        ("swipe_right", "swipe_right", True),
        ("swipe_left", "swipe_right", False),
        ("no_gesture", None, True),
    ]

    for index, (expected, predicted, _) in enumerate(trials):
        start_time = 100.0 + index * 5.0

        recorder.start_sample(expected, start_time)

        if predicted is not None:
            recorder.record_prediction(
                {
                    "gesture": predicted,
                    "confidence": 0.90,
                    "timestamp": start_time + 1.0,
                }
            )

        recorder.finish_sample(start_time + 4.0)

    samples = read_samples(output_path)

    assert len(samples) == 3

    assert [sample["sample_id"] for sample in samples] == [
        "t1-001",
        "t1-002",
        "t1-003",
    ]

    assert [sample["expected_gesture"] for sample in samples] == [
        trial[0] for trial in trials
    ]

    assert [sample["predicted_gesture"] for sample in samples] == [
        trial[1] for trial in trials
    ]

    assert [sample["correct"] for sample in samples] == [trial[2] for trial in trials]

    assert [sample["prediction_count"] for sample in samples] == [1, 1, 0]

    assert sum(sample["correct"] for sample in samples) == 2
    assert sum(sample["prediction_count"] for sample in samples) == 2

    assert recorder.sample_count == 3
    assert recorder.next_sample_id == "t2-001"
