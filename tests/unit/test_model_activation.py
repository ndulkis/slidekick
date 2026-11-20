"""Unit tests for custom gesture model activation and rollback."""

from pathlib import Path
from unittest.mock import patch

import pytest

from slidekick.recognition.model_activation import (
    activate_model,
    rollback_model,
)


def test_activate_model_without_previous_model(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.task"
    active = tmp_path / "models" / "custom_gesture.task"
    backup = tmp_path / "models" / "custom_gesture.backup.task"

    candidate.write_bytes(b"new-model")

    with patch("slidekick.recognition.model_activation.validate_model"):
        result = activate_model(candidate, active, backup)

    assert result == active
    assert active.read_bytes() == b"new-model"
    assert candidate.read_bytes() == b"new-model"
    assert not backup.exists()


def test_activation_preserves_previous_model(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.task"
    active = tmp_path / "custom_gesture.task"
    backup = tmp_path / "custom_gesture.backup.task"

    candidate.write_bytes(b"new-model")
    active.write_bytes(b"previous-model")

    with patch("slidekick.recognition.model_activation.validate_model"):
        activate_model(candidate, active, backup)

    assert active.read_bytes() == b"new-model"
    assert backup.read_bytes() == b"previous-model"


def test_activation_does_not_overwrite_existing_backup(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.task"
    active = tmp_path / "custom_gesture.task"
    backup = tmp_path / "custom_gesture.backup.task"

    candidate.write_bytes(b"candidate-model")
    active.write_bytes(b"working-model")
    backup.write_bytes(b"known-good-backup")

    with pytest.raises(FileExistsError, match="must be preserved"):
        activate_model(candidate, active, backup)

    assert active.read_bytes() == b"working-model"
    assert backup.read_bytes() == b"known-good-backup"
    assert candidate.read_bytes() == b"candidate-model"


def test_invalid_candidate_preserves_active_model(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.task"
    active = tmp_path / "custom_gesture.task"
    backup = tmp_path / "custom_gesture.backup.task"

    candidate.write_bytes(b"invalid-model")
    active.write_bytes(b"working-model")

    with (
        patch(
            "slidekick.recognition.model_activation.validate_model",
            side_effect=ValueError("Invalid model"),
        ),
        pytest.raises(ValueError, match="Invalid model"),
    ):
        activate_model(candidate, active, backup)

    assert active.read_bytes() == b"working-model"
    assert not backup.exists()


def test_rollback_restores_previous_model(tmp_path: Path) -> None:
    active = tmp_path / "custom_gesture.task"
    backup = tmp_path / "custom_gesture.backup.task"

    active.write_bytes(b"new-model")
    backup.write_bytes(b"previous-model")

    with patch("slidekick.recognition.model_activation.validate_model"):
        result = rollback_model(active, backup)

    assert result == active
    assert active.read_bytes() == b"previous-model"
    assert backup.read_bytes() == b"previous-model"


def test_rejects_overlapping_model_paths(tmp_path: Path) -> None:
    model = tmp_path / "model.task"
    backup = tmp_path / "backup.task"

    model.write_bytes(b"model")

    with pytest.raises(ValueError, match="must be distinct"):
        activate_model(model, model, backup)

    with pytest.raises(ValueError, match="must be distinct"):
        rollback_model(model, model)
