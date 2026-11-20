"""Unit tests for the custom gesture training runner."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from slidekick.recognition.training_job import TrainingJob
from slidekick.recognition.training_runner import run_training_job


def make_job(tmp_path: Path) -> TrainingJob:
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    return TrainingJob(
        job_id="job-001",
        profile_id="profile-001",
        dataset_dir=dataset_dir,
        export_dir=tmp_path / "export",
    )


def test_successful_training_job(tmp_path: Path) -> None:
    job = make_job(tmp_path)

    training_script = tmp_path / "train.py"
    training_script.write_text("# Test script")

    def fake_training(command, **kwargs):
        job.export_dir.mkdir()
        (job.export_dir / "gesture_recognizer.task").write_bytes(b"model")

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Training completed",
            stderr="",
        )

    with patch(
        "slidekick.recognition.training_runner.subprocess.run",
        side_effect=fake_training,
    ) as mock_run:
        result = run_training_job(
            job=job,
            python_executable=Path("python3"),
            training_script=training_script,
        )

    assert result.job_id == "job-001"
    assert result.profile_id == "profile-001"
    assert result.model_path.is_file()
    assert result.stdout == "Training completed"

    command = mock_run.call_args.args[0]
    assert command[-4:] == [
        "--dataset-dir",
        str(job.dataset_dir),
        "--export-dir",
        str(job.export_dir),
    ]


def test_training_process_failure(tmp_path: Path) -> None:
    job = make_job(tmp_path)

    training_script = tmp_path / "train.py"
    training_script.write_text("# Test script")

    failed_process = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="",
        stderr="Training failed",
    )

    with (
        patch(
            "slidekick.recognition.training_runner.subprocess.run",
            return_value=failed_process,
        ),
        pytest.raises(RuntimeError, match="Training failed"),
    ):
        run_training_job(job, Path("python3"), training_script)


def test_rejects_missing_exported_model(tmp_path: Path) -> None:
    job = make_job(tmp_path)

    training_script = tmp_path / "train.py"
    training_script.write_text("# Test script")

    successful_process = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="Training completed",
        stderr="",
    )

    with (
        patch(
            "slidekick.recognition.training_runner.subprocess.run",
            return_value=successful_process,
        ),
        pytest.raises(RuntimeError, match="without exporting"),
    ):
        run_training_job(job, Path("python3"), training_script)


def test_rejects_missing_training_script(tmp_path: Path) -> None:
    job = make_job(tmp_path)

    with pytest.raises(ValueError, match="Training script does not exist"):
        run_training_job(
            job,
            Path("python3"),
            tmp_path / "missing.py",
        )
