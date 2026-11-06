"""Tests for gesture sample data integrity."""

from copy import deepcopy

import pytest

from slidekick.recognition.sample_validator import (
    SampleValidationError,
    validate_sample,
)


@pytest.fixture
def valid_sample():
    """Return a valid completed evaluation sample."""
    return {
        "sample_id": "t1-001",
        "expected_gesture": "swipe_right",
        "predicted_gesture": "swipe_right",
        "sample_start_time": 100.0,
        "sample_end_time": 104.0,
        "prediction_count": 1,
        "correct": True,
        "frames": [
            {
                "timestamp": 100.5,
                "landmarks": [
                    {"id": i, "x": 0.5, "y": 0.5, "z": 0.0} for i in range(21)
                ],
            }
        ],
        "predictions": [
            {
                "gesture": "swipe_right",
                "confidence": 0.90,
                "timestamp": 101.0,
            }
        ],
    }


def test_valid_sample_passes_validation(valid_sample):
    assert validate_sample(valid_sample) is True


def test_unsupported_gesture_label_is_rejected(valid_sample):
    sample = deepcopy(valid_sample)
    sample["expected_gesture"] = "unknown_gesture"

    with pytest.raises(SampleValidationError, match="Unsupported"):
        validate_sample(sample)


def test_out_of_order_frame_timestamps_are_rejected(valid_sample):
    sample = deepcopy(valid_sample)

    second_frame = deepcopy(sample["frames"][0])
    second_frame["timestamp"] = 100.2
    sample["frames"].append(second_frame)

    with pytest.raises(SampleValidationError, match="chronological"):
        validate_sample(sample)


def test_invalid_landmark_count_is_rejected(valid_sample):
    sample = deepcopy(valid_sample)
    sample["frames"][0]["landmarks"].pop()

    with pytest.raises(SampleValidationError, match="21 landmarks"):
        validate_sample(sample)


def test_duplicate_landmark_id_is_rejected(valid_sample):
    sample = deepcopy(valid_sample)
    sample["frames"][0]["landmarks"][1]["id"] = 0

    with pytest.raises(SampleValidationError, match="duplicate"):
        validate_sample(sample)


def test_invalid_prediction_count_is_rejected(valid_sample):
    sample = deepcopy(valid_sample)
    sample["prediction_count"] = 3

    with pytest.raises(SampleValidationError, match="count mismatch"):
        validate_sample(sample)


def test_invalid_confidence_is_rejected(valid_sample):
    sample = deepcopy(valid_sample)
    sample["predictions"][0]["confidence"] = 1.5

    with pytest.raises(SampleValidationError, match="confidence"):
        validate_sample(sample)


def test_incorrect_evaluation_result_is_rejected(valid_sample):
    sample = deepcopy(valid_sample)
    sample["correct"] = False

    with pytest.raises(SampleValidationError, match="evaluation result"):
        validate_sample(sample)


def test_valid_no_gesture_sample_passes(valid_sample):
    sample = deepcopy(valid_sample)

    sample["expected_gesture"] = "no_gesture"
    sample["predicted_gesture"] = None
    sample["predictions"] = []
    sample["prediction_count"] = 0
    sample["correct"] = True

    assert validate_sample(sample) is True
