"""Evaluate custom gesture recognition predictions against labeled samples."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionSample:
    """A prediction and the corresponding ground-truth gesture."""

    expected: str
    predicted: str


@dataclass(frozen=True)
class ClassMetrics:
    """Recognition performance for one gesture class."""

    label: str
    support: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float


@dataclass(frozen=True)
class EvaluationResult:
    """Summary of candidate-model evaluation."""

    total_samples: int
    correct_predictions: int
    accuracy: float
    class_metrics: dict[str, ClassMetrics]
    confusion_matrix: dict[str, dict[str, int]]
    none_false_positive_rate: float | None


def evaluate_predictions(
    samples: list[PredictionSample],
    labels: list[str],
) -> EvaluationResult:
    """Calculate classification metrics from labeled predictions."""

    if not samples:
        raise ValueError("Evaluation requires at least one sample")

    if not labels or len(labels) != len(set(labels)):
        raise ValueError("Labels must be nonempty and unique")

    if any(not label for label in labels):
        raise ValueError("Labels cannot be empty strings")

    known_labels = set(labels)

    for sample in samples:
        if sample.expected not in known_labels:
            raise ValueError(f"Unknown expected label: {sample.expected}")

        if sample.predicted not in known_labels:
            raise ValueError(f"Unknown predicted label: {sample.predicted}")

    # Confusion matrix: actual label -> predicted label -> count.
    confusion = {actual: {predicted: 0 for predicted in labels} for actual in labels}

    for sample in samples:
        confusion[sample.expected][sample.predicted] += 1

    correct = sum(confusion[label][label] for label in labels)
    accuracy = correct / len(samples)

    metrics = {}

    for label in labels:
        true_positives = confusion[label][label]

        false_positives = sum(
            confusion[actual][label] for actual in labels if actual != label
        )

        false_negatives = sum(
            confusion[label][predicted] for predicted in labels if predicted != label
        )

        support = sum(confusion[label].values())

        precision_denominator = true_positives + false_positives
        recall_denominator = true_positives + false_negatives

        precision = (
            true_positives / precision_denominator if precision_denominator else 0.0
        )

        recall = true_positives / recall_denominator if recall_denominator else 0.0

        metrics[label] = ClassMetrics(
            label=label,
            support=support,
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
        )

    # False-positive rate specifically for background/no-gesture samples.
    none_false_positive_rate = None

    if "none" in known_labels:
        none_support = sum(confusion["none"].values())

        if none_support:
            false_activations = none_support - confusion["none"]["none"]

            none_false_positive_rate = false_activations / none_support

    return EvaluationResult(
        total_samples=len(samples),
        correct_predictions=correct,
        accuracy=accuracy,
        class_metrics=metrics,
        confusion_matrix=confusion,
        none_false_positive_rate=none_false_positive_rate,
    )
