"""Unit tests for custom gesture model acceptance decisions."""

import pytest

from slidekick.recognition.model_acceptance import (
    AcceptanceCriteria,
    assess_candidate,
)
from slidekick.recognition.model_evaluation import (
    PredictionSample,
    evaluate_predictions,
)


@pytest.fixture
def criteria() -> AcceptanceCriteria:
    """Illustrative thresholds used only for deterministic unit tests."""

    return AcceptanceCriteria(
        min_samples_per_class=10,
        min_precision=0.80,
        min_recall=0.80,
        max_none_false_positive_rate=0.10,
        max_gesture_confusion_rate=0.10,
    )


def evaluate(
    samples: list[PredictionSample],
):
    """Evaluate samples for the two-gesture acceptance scenario."""

    return evaluate_predictions(
        samples,
        labels=["pinch", "thumbs_up", "none"],
    )


def perfect_samples() -> list[PredictionSample]:
    """Return a perfectly classified dataset with 10 samples per class."""

    return (
        [PredictionSample("pinch", "pinch")] * 10
        + [PredictionSample("thumbs_up", "thumbs_up")] * 10
        + [PredictionSample("none", "none")] * 10
    )


def test_accepts_reliable_candidate(criteria: AcceptanceCriteria) -> None:
    evaluation = evaluate(perfect_samples())

    result = assess_candidate(
        evaluation,
        criteria,
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
    )

    assert result.accepted is True
    assert result.reasons == ()


def test_rejects_low_recall(criteria: AcceptanceCriteria) -> None:
    samples = perfect_samples()

    # Three thumbs-up samples become false negatives.
    samples[10:13] = [PredictionSample("thumbs_up", "none")] * 3

    result = assess_candidate(
        evaluate(samples),
        criteria,
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
    )

    assert result.accepted is False
    assert any("thumbs_up: recall" in reason for reason in result.reasons)


def test_rejects_high_background_false_positive_rate(
    criteria: AcceptanceCriteria,
) -> None:
    samples = perfect_samples()

    # Two background frames incorrectly trigger the pinch gesture.
    samples[20:22] = [PredictionSample("none", "pinch")] * 2

    result = assess_candidate(
        evaluate(samples),
        criteria,
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
    )

    assert result.accepted is False
    assert any("Background false-positive rate" in reason for reason in result.reasons)


@pytest.mark.parametrize(
    ("actual", "predicted"),
    [
        ("thumbs_up", "pinch"),
        ("pinch", "thumbs_up"),
    ],
)
def test_rejects_confusion_in_both_directions(
    criteria: AcceptanceCriteria,
    actual: str,
    predicted: str,
) -> None:
    samples = perfect_samples()

    start = 0 if actual == "pinch" else 10
    samples[start : start + 2] = [PredictionSample(actual, predicted)] * 2

    result = assess_candidate(
        evaluate(samples),
        criteria,
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
    )

    assert result.accepted is False
    assert any(
        f"Gesture confusion: {actual} predicted as {predicted}" in reason
        for reason in result.reasons
    )


def test_rejects_insufficient_evaluation_samples(
    criteria: AcceptanceCriteria,
) -> None:
    samples = (
        [PredictionSample("pinch", "pinch")] * 10
        + [PredictionSample("thumbs_up", "thumbs_up")] * 5
        + [PredictionSample("none", "none")] * 10
    )

    result = assess_candidate(
        evaluate(samples),
        criteria,
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
    )

    assert result.accepted is False
    assert any("insufficient evaluation samples" in reason for reason in result.reasons)


def test_rejects_missing_background_measurements(
    criteria: AcceptanceCriteria,
) -> None:
    samples = [PredictionSample("pinch", "pinch")] * 10 + [
        PredictionSample("thumbs_up", "thumbs_up")
    ] * 10

    result = assess_candidate(
        evaluate(samples),
        criteria,
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
    )

    assert result.accepted is False
    assert any(
        "Background false-positive rate was not measured" in reason
        for reason in result.reasons
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"min_samples_per_class": 0},
        {"min_precision": -0.1},
        {"min_recall": 1.1},
        {"max_none_false_positive_rate": 1.5},
        {"max_gesture_confusion_rate": -0.1},
        {"min_precision": float("nan")},
    ],
)
def test_rejects_invalid_thresholds(overrides: dict) -> None:
    values = {
        "min_samples_per_class": 10,
        "min_precision": 0.8,
        "min_recall": 0.8,
        "max_none_false_positive_rate": 0.1,
        "max_gesture_confusion_rate": 0.1,
    }
    values.update(overrides)

    criteria = AcceptanceCriteria(**values)

    with pytest.raises(ValueError):
        criteria.validate()


@pytest.mark.parametrize(
    ("new_gesture", "existing_gestures"),
    [
        ("none", ["pinch"]),
        ("", ["pinch"]),
        ("pinch", ["pinch"]),
        ("thumbs_up", ["pinch", "pinch"]),
        ("thumbs_up", ["none"]),
    ],
)
def test_rejects_invalid_gesture_configuration(
    criteria: AcceptanceCriteria,
    new_gesture: str,
    existing_gestures: list[str],
) -> None:
    with pytest.raises(ValueError):
        assess_candidate(
            evaluate(perfect_samples()),
            criteria,
            new_gesture=new_gesture,
            existing_gestures=existing_gestures,
        )


def test_rejects_mismatched_evaluation_classes(
    criteria: AcceptanceCriteria,
) -> None:
    evaluation = evaluate(perfect_samples())

    with pytest.raises(ValueError, match="Evaluation classes must match"):
        assess_candidate(
            evaluation,
            criteria,
            new_gesture="wave",
            existing_gestures=["pinch"],
        )
