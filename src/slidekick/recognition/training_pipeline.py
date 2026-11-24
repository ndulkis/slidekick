"""Coordinate custom gesture training and model activation."""

from collections.abc import Callable
from pathlib import Path

from .model_acceptance import AcceptanceCriteria, assess_candidate
from .model_activation import activate_model
from .model_inference import (
    EvaluatedCandidate,
    calculate_model_hash,
    evaluate_candidate_model,
)
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


def run_training_pipeline(
    job: TrainingJob,
    runner: Callable[[TrainingJob], TrainingRunResult],
    criteria: AcceptanceCriteria,
    new_gesture: str,
    existing_gestures: list[str],
    active_path: Path,
    backup_path: Path,
) -> Path:
    """Train, evaluate, and conditionally activate a gesture model."""

    # Step 1: Train and export a candidate model.
    result = train_candidate(
        job=job,
        runner=runner,
    )

    # Step 2: Locate the independent test partition.
    evaluation_dir = job.export_dir / "partitions" / "test"

    if not evaluation_dir.is_dir():
        raise ValueError(f"Training evaluation directory not found: {evaluation_dir}")

    labels = [*existing_gestures, new_gesture, "none"]

    # Step 3: Evaluate the exported model using the test images.
    evaluated_candidate = evaluate_candidate_model(
        model_path=result.model_path,
        evaluation_dir=evaluation_dir,
        labels=labels,
    )

    # Step 4: Apply acceptance criteria before activation.
    return activate_candidate(
        result=result,
        evaluated_candidate=evaluated_candidate,
        criteria=criteria,
        new_gesture=new_gesture,
        existing_gestures=existing_gestures,
        active_path=active_path,
        backup_path=backup_path,
    )
