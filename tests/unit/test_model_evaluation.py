"""Tests for custom gesture model evaluation metrics."""

import pytest

from slidekick.recognition.model_evaluation import (
    PredictionSample,
    evaluate_predictions,
)


def test_perfect_predictions() -> None:
    """A perfect model should report perfect classification metrics."""

    samples = [
        PredictionSample("pinch", "pinch"),
        PredictionSample("pinch", "pinch"),
        PredictionSample("thumbs_up", "thumbs_up"),
        PredictionSample("thumbs_up", "thumbs_up"),
        PredictionSample("none", "none"),
        PredictionSample("none", "none"),
    ]

    result = evaluate_predictions(
        samples,
        labels=["pinch", "thumbs_up", "none"],
    )

    assert result.total_samples == 6
    assert result.correct_predictions == 6
    assert result.accuracy == pytest.approx(1.0)
    assert result.none_false_positive_rate == pytest.approx(0.0)

    for metrics in result.class_metrics.values():
        assert metrics.precision == pytest.approx(1.0)
        assert metrics.recall == pytest.approx(1.0)
        assert metrics.false_positives == 0
        assert metrics.false_negatives == 0


def test_confusion_matrix_and_class_metrics() -> None:
    """Confused predictions must be counted against the correct classes."""

    samples = (
        [PredictionSample("pinch", "pinch")] * 8
        + [PredictionSample("pinch", "thumbs_up")] * 2
        + [PredictionSample("thumbs_up", "pinch")]
        + [PredictionSample("thumbs_up", "thumbs_up")] * 9
        + [PredictionSample("none", "pinch")] * 2
        + [PredictionSample("none", "none")] * 8
    )

    result = evaluate_predictions(
        samples,
        labels=["pinch", "thumbs_up", "none"],
    )

    assert result.total_samples == 30
    assert result.correct_predictions == 25
    assert result.accuracy == pytest.approx(25 / 30)

    assert result.confusion_matrix["pinch"] == {
        "pinch": 8,
        "thumbs_up": 2,
        "none": 0,
    }

    assert result.confusion_matrix["thumbs_up"] == {
        "pinch": 1,
        "thumbs_up": 9,
        "none": 0,
    }

    assert result.confusion_matrix["none"] == {
        "pinch": 2,
        "thumbs_up": 0,
        "none": 8,
    }

    pinch = result.class_metrics["pinch"]

    assert pinch.support == 10
    assert pinch.true_positives == 8
    assert pinch.false_positives == 3
    assert pinch.false_negatives == 2
    assert pinch.precision == pytest.approx(8 / 11)
    assert pinch.recall == pytest.approx(0.8)

    assert result.class_metrics["thumbs_up"].recall == pytest.approx(0.9)
    assert result.none_false_positive_rate == pytest.approx(0.2)


def test_missing_none_samples_reports_unknown_false_positive_rate() -> None:
    """No evaluated negatives must not be mistaken for zero false positives."""

    samples = [
        PredictionSample("pinch", "pinch"),
        PredictionSample("thumbs_up", "thumbs_up"),
    ]

    result = evaluate_predictions(
        samples,
        labels=["pinch", "thumbs_up", "none"],
    )

    assert result.none_false_positive_rate is None
    assert result.class_metrics["none"].support == 0


def test_unknown_predicted_label_is_rejected() -> None:
    """Predicted labels must belong to the declared classification space."""

    samples = [PredictionSample("pinch", "unknown")]

    with pytest.raises(ValueError, match="Unknown predicted label"):
        evaluate_predictions(samples, labels=["pinch", "none"])


def test_unknown_expected_label_is_rejected() -> None:
    """Ground-truth labels must belong to the declared classification space."""

    samples = [PredictionSample("unknown", "pinch")]

    with pytest.raises(ValueError, match="Unknown expected label"):
        evaluate_predictions(samples, labels=["pinch", "none"])


@pytest.mark.parametrize(
    "labels",
    [
        [],
        ["pinch", "pinch"],
        ["pinch", ""],
    ],
)
def test_invalid_label_configuration_is_rejected(labels: list[str]) -> None:
    """Reject missing, duplicate, or empty class names."""

    samples = [PredictionSample("pinch", "pinch")]

    with pytest.raises(ValueError, match="Labels"):
        evaluate_predictions(samples, labels)


def test_empty_evaluation_is_rejected() -> None:
    """An empty evaluation must not produce misleading accuracy metrics."""

    with pytest.raises(ValueError, match="at least one sample"):
        evaluate_predictions([], labels=["pinch", "none"])


def test_false_positives_are_distinct_from_false_negatives() -> None:
    """Misclassifying a gesture as none is not a false activation."""

    samples = [
        PredictionSample("pinch", "none"),
        PredictionSample("pinch", "pinch"),
        PredictionSample("none", "none"),
        PredictionSample("none", "none"),
    ]

    result = evaluate_predictions(samples, labels=["pinch", "none"])

    assert result.accuracy == pytest.approx(0.75)
    assert result.class_metrics["pinch"].false_negatives == 1
    assert result.class_metrics["pinch"].false_positives == 0
    assert result.none_false_positive_rate == pytest.approx(0.0)
