"""Decide whether a custom gesture model meets acceptance requirements."""

from dataclasses import dataclass

from .model_evaluation import EvaluationResult


@dataclass(frozen=True)
class AcceptanceCriteria:
    """Thresholds selected by the benchmark protocol."""

    min_samples_per_class: int
    min_precision: float
    min_recall: float
    max_none_false_positive_rate: float
    max_gesture_confusion_rate: float

    def validate(self) -> None:
        if self.min_samples_per_class < 1:
            raise ValueError("Minimum samples per class must be positive")

        thresholds = (
            self.min_precision,
            self.min_recall,
            self.max_none_false_positive_rate,
            self.max_gesture_confusion_rate,
        )

        if any(not 0.0 <= value <= 1.0 for value in thresholds):
            raise ValueError("Acceptance thresholds must be between 0 and 1")


@dataclass(frozen=True)
class AcceptanceResult:
    """Acceptance decision and reasons for rejection."""

    accepted: bool
    reasons: tuple[str, ...]


def assess_candidate(
    evaluation: EvaluationResult,
    criteria: AcceptanceCriteria,
    new_gesture: str,
    existing_gestures: list[str],
) -> AcceptanceResult:
    """Assess candidate performance, including confusion with existing gestures."""

    criteria.validate()

    if not new_gesture or new_gesture == "none":
        raise ValueError("New gesture must be a valid gesture class")

    if len(existing_gestures) != len(set(existing_gestures)):
        raise ValueError("Existing gestures must be unique")

    if new_gesture in existing_gestures:
        raise ValueError("New gesture already exists")

    if "none" in existing_gestures:
        raise ValueError("'none' cannot be an existing gesture")

    required_labels = {"none", new_gesture, *existing_gestures}
    actual_labels = set(evaluation.class_metrics)

    if actual_labels != required_labels:
        raise ValueError(
            "Evaluation classes must match the new gesture, existing gestures, and none"
        )

    reasons: list[str] = []

    # Every class must have enough independent evaluation samples.
    for label, metrics in evaluation.class_metrics.items():
        if metrics.support < criteria.min_samples_per_class:
            reasons.append(
                f"{label}: insufficient evaluation samples "
                f"({metrics.support} < {criteria.min_samples_per_class})"
            )

        if metrics.precision < criteria.min_precision:
            reasons.append(
                f"{label}: precision {metrics.precision:.3f} "
                f"is below {criteria.min_precision:.3f}"
            )

        if metrics.recall < criteria.min_recall:
            reasons.append(
                f"{label}: recall {metrics.recall:.3f} "
                f"is below {criteria.min_recall:.3f}"
            )

    # An unmeasured background false-positive rate cannot pass.
    none_rate = evaluation.none_false_positive_rate

    if none_rate is None:
        reasons.append("Background false-positive rate was not measured")
    elif none_rate > criteria.max_none_false_positive_rate:
        reasons.append(
            f"Background false-positive rate {none_rate:.3f} "
            f"exceeds {criteria.max_none_false_positive_rate:.3f}"
        )

    # Check whether the new class is confused with existing classes
    # in either direction.
    for existing in existing_gestures:
        for actual, predicted in (
            (new_gesture, existing),
            (existing, new_gesture),
        ):
            support = evaluation.class_metrics[actual].support

            if support == 0:
                continue

            confusion_count = evaluation.confusion_matrix[actual][predicted]
            confusion_rate = confusion_count / support

            if confusion_rate > criteria.max_gesture_confusion_rate:
                reasons.append(
                    f"Gesture confusion: {actual} predicted as "
                    f"{predicted} at rate {confusion_rate:.3f}"
                )

    return AcceptanceResult(
        accepted=not reasons,
        reasons=tuple(reasons),
    )
