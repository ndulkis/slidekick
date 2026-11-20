"""Launch custom gesture training using an external Python environment."""

import subprocess  # nosec B404 - Required for external training execution.
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

    completed = subprocess.run(  # nosec B603 - Trusted interpreter and script paths.
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


def windows_path_to_wsl(path: Path) -> str:
    """Convert an absolute Windows path to its WSL equivalent."""

    completed = subprocess.run(  # nosec B603, B607 - Trusted WSL utilities; no shell.
        ["wsl.exe", "--exec", "wslpath", "-a", "-u", str(path.resolve())],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if completed.returncode != 0 or not completed.stdout.strip():
        raise RuntimeError(
            f"Could not convert Windows path to WSL: {path}\n{completed.stderr}"
        )

    return completed.stdout.strip()


def run_wsl_training_job(
    job: TrainingJob,
    wsl_python: str,
    wsl_training_script: str,
) -> TrainingRunResult:
    """Launch a training job inside WSL from the Windows application."""

    job.validate()

    dataset_dir = windows_path_to_wsl(job.dataset_dir)
    export_dir = windows_path_to_wsl(job.export_dir)

    command = [
        "wsl.exe",
        "--exec",
        wsl_python,
        wsl_training_script,
        "--dataset-dir",
        dataset_dir,
        "--export-dir",
        export_dir,
    ]

    completed = subprocess.run(  # nosec B603 - Trusted WSL training configuration.
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            f"WSL training job '{job.job_id}' failed "
            f"with exit code {completed.returncode}:\n"
            f"{completed.stderr[-2000:]}"
        )

    model_path = job.export_dir / "gesture_recognizer.task"

    if not model_path.is_file() or model_path.stat().st_size == 0:
        raise RuntimeError(
            f"WSL training job '{job.job_id}' did not export "
            f"a valid model artifact: {model_path}"
        )

    return TrainingRunResult(
        job_id=job.job_id,
        profile_id=job.profile_id,
        model_path=model_path,
        stdout=completed.stdout,
    )
