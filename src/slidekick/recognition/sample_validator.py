"""Validate recorded gesture evaluation samples."""

import math

SUPPORTED_GESTURES = frozenset(
    {
        "swipe_left",
        "swipe_right",
        "no_gesture",
    }
)

LANDMARK_COUNT = 21


class SampleValidationError(ValueError):
    """Raised when a recorded sample violates data integrity rules."""


def validate_gesture_label(label, supported_labels=SUPPORTED_GESTURES):
    """Verify that a gesture label is supported."""
    if not isinstance(label, str) or label not in supported_labels:
        raise SampleValidationError(f"Unsupported gesture label: {label!r}")


def validate_timestamp(value, field_name):
    """Require a finite numeric timestamp."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise SampleValidationError(f"Invalid {field_name}: {value!r}")


def validate_landmarks(landmarks):
    """Validate the structure of one MediaPipe hand-landmark frame."""
    if not isinstance(landmarks, list) or len(landmarks) != LANDMARK_COUNT:
        raise SampleValidationError("Frame must contain exactly 21 landmarks")

    seen_ids = set()

    for landmark in landmarks:
        if not isinstance(landmark, dict):
            raise SampleValidationError("Landmark must be a dictionary")

        landmark_id = landmark.get("id")

        if (
            type(landmark_id) is not int
            or not 0 <= landmark_id < LANDMARK_COUNT
            or landmark_id in seen_ids
        ):
            raise SampleValidationError("Invalid or duplicate landmark ID")

        seen_ids.add(landmark_id)

        for coordinate in ("x", "y", "z"):
            value = landmark.get(coordinate)

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise SampleValidationError(
                    f"Invalid landmark coordinate: {coordinate}"
                )


def validate_sample(sample, supported_labels=SUPPORTED_GESTURES):
    """Validate the integrity of one completed recorded trial."""
    if not isinstance(sample, dict):
        raise SampleValidationError("Sample must be a dictionary")

    validate_gesture_label(sample.get("expected_gesture"), supported_labels)

    predicted = sample.get("predicted_gesture")
    if predicted is not None:
        validate_gesture_label(predicted, supported_labels)

    start = sample.get("sample_start_time")
    end = sample.get("sample_end_time")

    validate_timestamp(start, "sample_start_time")
    validate_timestamp(end, "sample_end_time")

    if end < start:
        raise SampleValidationError("Sample end precedes sample start")

    frames = sample.get("frames")
    predictions = sample.get("predictions")

    if not isinstance(frames, list):
        raise SampleValidationError("Frames must be a list")

    if not isinstance(predictions, list):
        raise SampleValidationError("Predictions must be a list")

    previous_time = start

    for frame in frames:
        if not isinstance(frame, dict):
            raise SampleValidationError("Frame must be a dictionary")

        timestamp = frame.get("timestamp")
        validate_timestamp(timestamp, "frame timestamp")

        if not previous_time <= timestamp <= end:
            raise SampleValidationError("Frame timestamps are not chronological")

        validate_landmarks(frame.get("landmarks"))
        previous_time = timestamp

    previous_time = start

    for prediction in predictions:
        if not isinstance(prediction, dict):
            raise SampleValidationError("Prediction must be a dictionary")

        validate_gesture_label(prediction.get("gesture"), supported_labels)

        timestamp = prediction.get("timestamp")
        validate_timestamp(timestamp, "prediction timestamp")

        if not previous_time <= timestamp <= end:
            raise SampleValidationError("Prediction timestamps are not chronological")

        confidence = prediction.get("confidence")

        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 1
        ):
            raise SampleValidationError("Invalid prediction confidence")

        previous_time = timestamp

    count = sample.get("prediction_count")

    if type(count) is not int or count != len(predictions):
        raise SampleValidationError("Prediction count mismatch")

    if predictions:
        if predicted not in [p["gesture"] for p in predictions]:
            raise SampleValidationError("Representative prediction mismatch")
    elif predicted is not None:
        raise SampleValidationError("Prediction exists without an event")

    expected = sample["expected_gesture"]

    if expected == "no_gesture":
        expected_correct = not predictions
    else:
        expected_correct = any(
            prediction["gesture"] == expected for prediction in predictions
        )

    if sample.get("correct") is not expected_correct:
        raise SampleValidationError("Incorrect trial evaluation result")

    return True
