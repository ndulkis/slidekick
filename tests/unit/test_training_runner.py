"""Unit tests for the custom gesture training runner."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from slidekick.recognition.training_job import TrainingJob
from slidekick.recognition.training_runner import (
    run_training_job,
    run_wsl_training_job,
)


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


def test_native_runner_forwards_manifest(tmp_path: Path) -> None:
    """Native training forwards capture-group metadata to the script."""

    job = make_job(tmp_path)
    training_script = tmp_path / "train.py"
    training_script.write_text("# Test script", encoding="utf-8")

    manifest_path = tmp_path / "capture_groups.json"
    manifest_path.write_text('{"samples": []}', encoding="utf-8")

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
        run_training_job(
            job=job,
            python_executable=Path("python3"),
            training_script=training_script,
            manifest_path=manifest_path,
        )

    command = mock_run.call_args.args[0]

    assert command[-2:] == [
        "--manifest-path",
        str(manifest_path),
    ]


def test_wsl_runner_forwards_manifest(tmp_path: Path) -> None:
    """WSL training converts and forwards the manifest path."""

    job = make_job(tmp_path)

    manifest_path = tmp_path / "capture_groups.json"
    manifest_path.write_text('{"samples": []}', encoding="utf-8")

    expected_model = job.export_dir / "gesture_recognizer.task"

    def fake_training(command, **kwargs):
        job.export_dir.mkdir()
        expected_model.write_bytes(b"model")

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Training completed",
            stderr="",
        )

    with (
        patch(
            "slidekick.recognition.training_runner.windows_path_to_wsl",
            side_effect=lambda path: f"/mnt/test/{path.name}",
        ),
        patch(
            "slidekick.recognition.training_runner.subprocess.run",
            side_effect=fake_training,
        ) as mock_run,
    ):
        result = run_wsl_training_job(
            job=job,
            wsl_python="/training/.venv/bin/python",
            wsl_training_script="/training/scripts/train_prototype.py",
            manifest_path=manifest_path,
        )

    command = mock_run.call_args.args[0]

    assert command == [
        "wsl.exe",
        "--exec",
        "/training/.venv/bin/python",
        "/training/scripts/train_prototype.py",
        "--dataset-dir",
        "/mnt/test/dataset",
        "--export-dir",
        "/mnt/test/export",
        "--manifest-path",
        "/mnt/test/capture_groups.json",
    ]

    assert result.model_path == expected_model


def test_wsl_runner_rejects_missing_manifest(tmp_path: Path) -> None:
    """A missing manifest must prevent the training process from starting."""

    job = make_job(tmp_path)
    missing_manifest = tmp_path / "missing.json"

    with (
        patch(
            "slidekick.recognition.training_runner.windows_path_to_wsl",
            side_effect=lambda path: f"/mnt/test/{path.name}",
        ),
        patch(
            "slidekick.recognition.training_runner.subprocess.run",
        ) as mock_run,
        pytest.raises(ValueError, match="Training manifest does not exist"),
    ):
        run_wsl_training_job(
            job=job,
            wsl_python="/training/.venv/bin/python",
            wsl_training_script="/training/scripts/train_prototype.py",
            manifest_path=missing_manifest,
        )

    mock_run.assert_not_called()


def test_repo_runner_uses_repository_training_environment(
    tmp_path: Path,
) -> None:
    """Repository runner must discover its own interpreter and script."""

    from unittest.mock import Mock

    from slidekick.recognition import training_runner

    job = make_job(tmp_path)

    repository_root = Path(training_runner.__file__).resolve().parents[3]

    expected_python = repository_root / "training" / ".venv" / "bin" / "python"
    expected_script = repository_root / "training" / "scripts" / "train_prototype.py"

    expected_result = Mock()

    with (
        patch(
            "slidekick.recognition.training_runner.windows_path_to_wsl",
            side_effect=lambda path: f"/converted/{path.name}",
        ) as convert_path,
        patch(
            "slidekick.recognition.training_runner.run_wsl_training_job",
            return_value=expected_result,
        ) as run_job,
    ):
        result = training_runner.run_repo_wsl_training_job(job)

    assert convert_path.call_count == 2

    assert convert_path.call_args_list[0].args[0] == expected_python
    assert convert_path.call_args_list[1].args[0] == expected_script

    run_job.assert_called_once_with(
        job=job,
        wsl_python="/converted/python",
        wsl_training_script="/converted/train_prototype.py",
        manifest_path=None,
    )

    assert result is expected_result


def test_repo_runner_forwards_capture_group_manifest(
    tmp_path: Path,
) -> None:
    """The repository runner must preserve grouped-training metadata."""

    from slidekick.recognition import training_runner

    job = make_job(tmp_path)

    manifest_path = tmp_path / "capture_groups.json"
    manifest_path.write_text('{"samples": []}', encoding="utf-8")

    with (
        patch(
            "slidekick.recognition.training_runner.windows_path_to_wsl",
            side_effect=lambda path: f"/converted/{path.name}",
        ),
        patch(
            "slidekick.recognition.training_runner.run_wsl_training_job",
        ) as run_job,
    ):
        training_runner.run_repo_wsl_training_job(
            job=job,
            manifest_path=manifest_path,
        )

    assert run_job.call_args.kwargs["manifest_path"] == manifest_path
