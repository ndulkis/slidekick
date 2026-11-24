"""Coordinate custom gesture training and model activation."""

from collections.abc import Callable
from pathlib import Path

from .model_acceptance import AcceptanceCriteria, assess_candidate
from .model_activation import activate_model
from .model_inference import EvaluatedCandidate, calculate_model_hash
from .training_job import TrainingJob
from .training_runner import TrainingRunResult


def train_candidate(
    job: TrainingJob,
    runner: Callable[[TrainingJob], TrainingRunResult],
) -> TrainingRunResult:
    """Train a candidate model without activating it."""

    return runner(job)


def activate_candidate(
    result: TrainingRunResult,
    evaluated_candidate: EvaluatedCandidate,
    criteria: AcceptanceCriteria,
    new_gesture: str,
    existing_gestures: list[str],
    active_path: Path,
    backup_path: Path,
) -> Path:
    """Activate only the exact candidate model that passed evaluation."""

    # Verify that the model selected for activation is the one evaluated.
    current_hash = calculate_model_hash(result.model_path)

    if current_hash != evaluated_candidate.model_sha256:
        raise ValueError(
            "Candidate model hash mismatch: the model has changed since evaluation"
        )

    # Check recognition quality before allowing activation.
    decision = assess_candidate(
        evaluation=evaluated_candidate.evaluation,
        criteria=criteria,
        new_gesture=new_gesture,
        existing_gestures=existing_gestures,
    )

    if not decision.accepted:
        reasons = "; ".join(decision.reasons)
        raise ValueError(f"Candidate model rejected: {reasons}")

    # The existing component handles MediaPipe validation,
    # backup creation, and model replacement.
    return activate_model(
        candidate_path=result.model_path,
        active_path=active_path,
        backup_path=backup_path,
    )
