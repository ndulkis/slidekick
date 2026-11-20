"""Unit tests for custom gesture training job configuration."""

from pathlib import Path

import pytest

from slidekick.recognition.training_job import TrainingJob


def test_valid_training_job(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    job = TrainingJob(
        job_id="job-001",
        profile_id="profile-001",
        dataset_dir=dataset_dir,
        export_dir=tmp_path / "output",
    )

    job.validate()


@pytest.mark.parametrize(
    ("job_id", "profile_id"),
    [
        ("", "profile-001"),
        ("job-001", ""),
        ("   ", "profile-001"),
    ],
)
def test_rejects_empty_identifiers(
    tmp_path: Path,
    job_id: str,
    profile_id: str,
) -> None:
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    job = TrainingJob(
        job_id=job_id,
        profile_id=profile_id,
        dataset_dir=dataset_dir,
        export_dir=tmp_path / "output",
    )

    with pytest.raises(ValueError):
        job.validate()


def test_rejects_missing_dataset(tmp_path: Path) -> None:
    job = TrainingJob(
        job_id="job-001",
        profile_id="profile-001",
        dataset_dir=tmp_path / "missing_dataset",
        export_dir=tmp_path / "output",
    )

    with pytest.raises(ValueError, match="dataset directory"):
        job.validate()


def test_rejects_existing_export_directory(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    export_dir = tmp_path / "output"
    export_dir.mkdir()

    job = TrainingJob(
        job_id="job-001",
        profile_id="profile-001",
        dataset_dir=dataset_dir,
        export_dir=export_dir,
    )

    with pytest.raises(ValueError, match="already exists"):
        job.validate()
