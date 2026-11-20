"""Training job configuration for custom gesture models."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingJob:
    """Configuration required to run a custom gesture training job."""

    job_id: str
    profile_id: str
    dataset_dir: Path
    export_dir: Path

    def validate(self) -> None:
        """Validate the configuration before training begins."""

        if not self.job_id.strip():
            raise ValueError("Training job ID cannot be empty")

        if not self.profile_id.strip():
            raise ValueError("Profile ID cannot be empty")

        if not self.dataset_dir.is_dir():
            raise ValueError(
                f"Training dataset directory does not exist: {self.dataset_dir}"
            )

        if self.export_dir.exists():
            raise ValueError(
                f"Training export directory already exists: {self.export_dir}"
            )
