"""Validate and activate custom MediaPipe gesture models."""

import os
import shutil
from pathlib import Path
from uuid import uuid4

import mediapipe as mp


def validate_model(model_path: Path) -> None:
    """Confirm that MediaPipe can initialize the candidate model."""

    if not model_path.is_file() or model_path.stat().st_size == 0:
        raise ValueError(f"Missing or empty model: {model_path}")

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path.resolve())),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
    )

    with mp.tasks.vision.GestureRecognizer.create_from_options(options):
        pass


def validate_model_paths(*paths: Path) -> None:
    """Prevent candidate, active, and backup paths from overlapping."""

    resolved_paths = [path.resolve() for path in paths]

    if len(resolved_paths) != len(set(resolved_paths)):
        raise ValueError("Model paths must be distinct")


def activate_model(
    candidate_path: Path,
    active_path: Path,
    backup_path: Path,
) -> Path:
    """Activate a validated model while preserving the previous model."""

    validate_model_paths(candidate_path, active_path, backup_path)

    if active_path.is_file() and backup_path.exists():
        raise FileExistsError(f"Existing model backup must be preserved: {backup_path}")

    validate_model(candidate_path)

    if not active_path.parent.is_dir():
        active_path.parent.mkdir(parents=True, exist_ok=True)

    backup_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = active_path.with_name(f".{active_path.name}.{uuid4().hex}.tmp")

    try:
        # Prepare the replacement without modifying the active model.
        shutil.copy2(candidate_path, temporary_path)

        # Preserve the previous working model before replacement.
        if active_path.is_file():
            shutil.copy2(active_path, backup_path)

        # Atomically replace the active file.
        os.replace(temporary_path, active_path)

    finally:
        temporary_path.unlink(missing_ok=True)

    return active_path


def rollback_model(active_path: Path, backup_path: Path) -> Path:
    """Restore the previously active model."""

    validate_model_paths(active_path, backup_path)

    validate_model(backup_path)

    temporary_path = active_path.with_name(f".{active_path.name}.{uuid4().hex}.tmp")

    try:
        shutil.copy2(backup_path, temporary_path)
        os.replace(temporary_path, active_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return active_path
