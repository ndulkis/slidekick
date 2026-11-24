"""Unit tests for custom gesture training and activation orchestration."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from slidekick.recognition.model_acceptance import AcceptanceCriteria
from slidekick.recognition.model_evaluation import (
    PredictionSample,
    evaluate_predictions,
)
from slidekick.recognition.model_inference import (
    EvaluatedCandidate,
    calculate_model_hash,
)
from slidekick.recognition.training_job import TrainingJob
from slidekick.recognition.training_pipeline import (
    activate_candidate,
    run_training_pipeline,
    train_candidate,
)
from slidekick.recognition.training_runner import TrainingRunResult


@pytest.fixture
def training_job(tmp_path: Path) -> TrainingJob:
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    return TrainingJob(
        job_id="test-job",
        profile_id="test-profile",
        dataset_dir=dataset_dir,
        export_dir=tmp_path / "exports",
    )


def acceptance_criteria() -> AcceptanceCriteria:
    return AcceptanceCriteria(
        min_samples_per_class=10,
        min_precision=0.8,
        min_recall=0.8,
        max_none_false_positive_rate=0.1,
        max_gesture_confusion_rate=0.1,
    )


def candidate_evaluation(*, accepted: bool = True):
    samples = (
        [PredictionSample("pinch", "pinch")] * 10
        + [PredictionSample("thumbs_up", "thumbs_up")] * 10
        + [PredictionSample("none", "none")] * 10
    )

    if not accepted:
        samples[10:15] = [PredictionSample("thumbs_up", "pinch")] * 5

    return evaluate_predictions(
        samples,
        labels=["pinch", "thumbs_up", "none"],
    )


def evaluated_candidate(
    model_path: Path,
    *,
    accepted: bool = True,
) -> EvaluatedCandidate:
    """Create an evaluated candidate associated with a real test artifact."""

    return EvaluatedCandidate(
        model_sha256=calculate_model_hash(model_path),
        evaluation=candidate_evaluation(accepted=accepted),
    )


def test_training_returns_candidate_without_activation(
    training_job: TrainingJob,
    tmp_path: Path,
) -> None:
    active_path = tmp_path / "active.task"
    active_path.write_bytes(b"existing-model")

    expected = TrainingRunResult(
        job_id=training_job.job_id,
        profile_id=training_job.profile_id,
        model_path=training_job.export_dir / "gesture_recognizer.task",
        stdout="Training completed",
    )

    runner = Mock(return_value=expected)

    result = train_candidate(training_job, runner)

    runner.assert_called_once_with(training_job)
    assert result == expected
    assert active_path.read_bytes() == b"existing-model"


def test_training_failure_preserves_active_model(
    training_job: TrainingJob,
    tmp_path: Path,
) -> None:
    active_path = tmp_path / "active.task"
    active_path.write_bytes(b"existing-model")

    runner = Mock(side_effect=RuntimeError("Training failed"))

    with pytest.raises(RuntimeError, match="Training failed"):
        train_candidate(training_job, runner)

    runner.assert_called_once_with(training_job)
    assert active_path.read_bytes() == b"existing-model"


def test_activation_passes_candidate_to_activation_component(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from slidekick.recognition import training_pipeline

    candidate_path = tmp_path / "candidate.task"
    active_path = tmp_path / "active.task"
    backup_path = tmp_path / "backup.task"

    result = TrainingRunResult(
        job_id="test-job",
        profile_id="test-profile",
        model_path=candidate_path,
        stdout="Training completed",
    )

    candidate_path.write_bytes(b"candidate-model")

    activation = Mock(return_value=active_path)
    monkeypatch.setattr(training_pipeline, "activate_model", activation)

    activated_path = activate_candidate(
        result=result,
        evaluated_candidate=evaluated_candidate(candidate_path),
        criteria=acceptance_criteria(),
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
        active_path=active_path,
        backup_path=backup_path,
    )

    activation.assert_called_once_with(
        candidate_path=candidate_path,
        active_path=active_path,
        backup_path=backup_path,
    )
    assert activated_path == active_path


def test_activation_failure_propagates_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from slidekick.recognition import training_pipeline

    active_path = tmp_path / "active.task"
    active_path.write_bytes(b"existing-model")

    result = TrainingRunResult(
        job_id="test-job",
        profile_id="test-profile",
        model_path=tmp_path / "invalid.task",
        stdout="Training completed",
    )

    result.model_path.write_bytes(b"candidate-model")

    activation = Mock(side_effect=ValueError("Invalid candidate model"))
    monkeypatch.setattr(training_pipeline, "activate_model", activation)

    with pytest.raises(ValueError, match="Invalid candidate model"):
        activate_candidate(
            result=result,
            evaluated_candidate=evaluated_candidate(result.model_path),
            criteria=acceptance_criteria(),
            new_gesture="thumbs_up",
            existing_gestures=["pinch"],
            active_path=active_path,
            backup_path=tmp_path / "backup.task",
        )

    assert active_path.read_bytes() == b"existing-model"


def test_rejected_candidate_never_reaches_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject unreliable models without touching the active model."""

    from slidekick.recognition import training_pipeline

    active_path = tmp_path / "active.task"
    active_path.write_bytes(b"existing-model")

    result = TrainingRunResult(
        job_id="test-job",
        profile_id="test-profile",
        model_path=tmp_path / "candidate.task",
        stdout="Training completed",
    )

    result.model_path.write_bytes(b"candidate-model")

    activation = Mock()
    monkeypatch.setattr(training_pipeline, "activate_model", activation)

    with pytest.raises(ValueError, match="Candidate model rejected"):
        activate_candidate(
            result=result,
            evaluated_candidate=evaluated_candidate(
                result.model_path,
                accepted=False,
            ),
            criteria=acceptance_criteria(),
            new_gesture="thumbs_up",
            existing_gestures=["pinch"],
            active_path=active_path,
            backup_path=tmp_path / "backup.task",
        )

    activation.assert_not_called()
    assert active_path.read_bytes() == b"existing-model"


def test_changed_candidate_cannot_be_activated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model modified after evaluation must never reach activation."""

    from slidekick.recognition import training_pipeline

    candidate_path = tmp_path / "candidate.task"
    active_path = tmp_path / "active.task"
    backup_path = tmp_path / "backup.task"

    candidate_path.write_bytes(b"original-candidate")
    active_path.write_bytes(b"existing-working-model")

    result = TrainingRunResult(
        job_id="test-job",
        profile_id="test-profile",
        model_path=candidate_path,
        stdout="Training completed",
    )

    # Record the fingerprint of the original candidate.
    evaluated = evaluated_candidate(candidate_path)

    # Simulate accidental replacement after evaluation.
    candidate_path.write_bytes(b"different-candidate")

    activation = Mock()
    monkeypatch.setattr(training_pipeline, "activate_model", activation)

    with pytest.raises(ValueError, match="hash mismatch"):
        activate_candidate(
            result=result,
            evaluated_candidate=evaluated,
            criteria=acceptance_criteria(),
            new_gesture="thumbs_up",
            existing_gestures=["pinch"],
            active_path=active_path,
            backup_path=backup_path,
        )

    activation.assert_not_called()
    assert active_path.read_bytes() == b"existing-working-model"
    assert not backup_path.exists()


def test_pipeline_trains_evaluates_and_activates(
    training_job: TrainingJob,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A passing candidate moves through the complete workflow."""

    from slidekick.recognition import training_pipeline

    candidate_path = training_job.export_dir / "gesture_recognizer.task"
    evaluation_dir = training_job.export_dir / "partitions" / "test"

    active_path = tmp_path / "active.task"
    backup_path = tmp_path / "backup.task"

    expected_result = TrainingRunResult(
        job_id=training_job.job_id,
        profile_id=training_job.profile_id,
        model_path=candidate_path,
        stdout="Training completed",
    )

    def fake_runner(job):
        evaluation_dir.mkdir(parents=True)
        candidate_path.write_bytes(b"trained-model")
        return expected_result

    runner = Mock(side_effect=fake_runner)

    evaluated = EvaluatedCandidate(
        model_sha256="test-fingerprint",
        evaluation=candidate_evaluation(),
    )

    evaluation = Mock(return_value=evaluated)
    activation = Mock(return_value=active_path)

    monkeypatch.setattr(
        training_pipeline,
        "evaluate_candidate_model",
        evaluation,
    )
    monkeypatch.setattr(
        training_pipeline,
        "activate_candidate",
        activation,
    )

    result = run_training_pipeline(
        job=training_job,
        runner=runner,
        criteria=acceptance_criteria(),
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
        active_path=active_path,
        backup_path=backup_path,
    )

    runner.assert_called_once_with(training_job)

    evaluation.assert_called_once_with(
        model_path=candidate_path,
        evaluation_dir=evaluation_dir,
        labels=["pinch", "thumbs_up", "none"],
    )

    activation.assert_called_once_with(
        result=expected_result,
        evaluated_candidate=evaluated,
        criteria=acceptance_criteria(),
        new_gesture="thumbs_up",
        existing_gestures=["pinch"],
        active_path=active_path,
        backup_path=backup_path,
    )

    assert result == active_path


def test_pipeline_rejects_missing_test_partition(
    training_job: TrainingJob,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Training without grouped test data must not activate a model."""

    from slidekick.recognition import training_pipeline

    candidate_path = training_job.export_dir / "gesture_recognizer.task"

    def fake_runner(job):
        job.export_dir.mkdir()
        candidate_path.write_bytes(b"trained-model")

        return TrainingRunResult(
            job_id=job.job_id,
            profile_id=job.profile_id,
            model_path=candidate_path,
            stdout="Training completed",
        )

    evaluation = Mock()
    activation = Mock()

    monkeypatch.setattr(
        training_pipeline,
        "evaluate_candidate_model",
        evaluation,
    )
    monkeypatch.setattr(
        training_pipeline,
        "activate_candidate",
        activation,
    )

    with pytest.raises(ValueError, match="evaluation directory not found"):
        run_training_pipeline(
            job=training_job,
            runner=fake_runner,
            criteria=acceptance_criteria(),
            new_gesture="thumbs_up",
            existing_gestures=["pinch"],
            active_path=tmp_path / "active.task",
            backup_path=tmp_path / "backup.task",
        )

    evaluation.assert_not_called()
    activation.assert_not_called()


def test_pipeline_evaluation_failure_prevents_activation(
    training_job: TrainingJob,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed evaluation must leave the active model untouched."""

    from slidekick.recognition import training_pipeline

    evaluation_dir = training_job.export_dir / "partitions" / "test"
    active_path = tmp_path / "active.task"
    active_path.write_bytes(b"existing-working-model")

    def fake_runner(job):
        evaluation_dir.mkdir(parents=True)

        model_path = job.export_dir / "gesture_recognizer.task"
        model_path.write_bytes(b"candidate-model")

        return TrainingRunResult(
            job_id=job.job_id,
            profile_id=job.profile_id,
            model_path=model_path,
            stdout="Training completed",
        )

    evaluation = Mock(side_effect=RuntimeError("Evaluation failed"))
    activation = Mock()

    monkeypatch.setattr(
        training_pipeline,
        "evaluate_candidate_model",
        evaluation,
    )
    monkeypatch.setattr(
        training_pipeline,
        "activate_candidate",
        activation,
    )

    with pytest.raises(RuntimeError, match="Evaluation failed"):
        run_training_pipeline(
            job=training_job,
            runner=fake_runner,
            criteria=acceptance_criteria(),
            new_gesture="thumbs_up",
            existing_gestures=["pinch"],
            active_path=active_path,
            backup_path=tmp_path / "backup.task",
        )

    activation.assert_not_called()
    assert active_path.read_bytes() == b"existing-working-model"
