"""Launch custom gesture training using an external Python environment."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .training_job import TrainingJob


@dataclass(frozen=True)
class TrainingRunResult:
    """Result of a successfully completed training subprocess."""

    job_id: str
    profile_id: str
    model_path: Path
    stdout: str


def run_training_job(
    job: TrainingJob,
    python_executable: Path,
    training_script: Path,
) -> TrainingRunResult:
    """Execute Model Maker training and verify the exported artifact."""

    job.validate()

    if not training_script.is_file():
        raise ValueError(f"Training script does not exist: {training_script}")

    command = [
        str(python_executable),
        str(training_script),
        "--dataset-dir",
        str(job.dataset_dir),
        "--export-dir",
        str(job.export_dir),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            f"Training job '{job.job_id}' failed "
            f"with exit code {completed.returncode}:\n"
            f"{completed.stderr[-2000:]}"
        )

    model_path = job.export_dir / "gesture_recognizer.task"

    if not model_path.is_file():
        raise RuntimeError(
            f"Training job '{job.job_id}' completed without "
            f"exporting a model: {model_path}"
        )

    return TrainingRunResult(
        job_id=job.job_id,
        profile_id=job.profile_id,
        model_path=model_path,
        stdout=completed.stdout,
    )
