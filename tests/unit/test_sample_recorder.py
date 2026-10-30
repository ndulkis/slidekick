
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

    recorder.record_prediction({
        "event_type": "gesture",
        "gesture": "swipe_right",
        "confidence": 0.85,
        "timestamp": 101.0,
    })

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

    recorder.record_prediction({
        "event_type": "gesture",
        "gesture": "swipe_right",
        "confidence": 0.92,
        "timestamp": 101.5,
    })

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

    recorder.record_prediction({
        "gesture": "swipe_right",
        "confidence": 0.70,
        "timestamp": 101.0,
    })

    recorder.record_prediction({
        "gesture": "swipe_left",
        "confidence": 0.90,
        "timestamp": 102.0,
    })

    recorder.finish_sample(104.0)

    sample = read_samples(output_path)[0]

    assert sample["expected_gesture"] == "swipe_left"
    assert sample["predicted_gesture"] == "swipe_left"
    assert sample["prediction_count"] == 2
    assert len(sample["predictions"]) == 2
    assert sample["prediction_time"] == 102.0
    assert sample["correct"] is True
