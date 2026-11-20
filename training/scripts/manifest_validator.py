"""Validate capture-group metadata for custom gesture datasets."""

import json
from dataclasses import dataclass
from pathlib import Path

from dataset_validator import validate_dataset


@dataclass(frozen=True)
class ManifestValidationResult:
    """Summary of a validated enrollment manifest."""

    total_samples: int
    total_capture_groups: int
    class_counts: dict[str, int]


def validate_manifest(
    dataset_dir: Path,
    manifest_path: Path,
) -> ManifestValidationResult:
    """Validate image references, labels, and capture groups."""

    validate_dataset(dataset_dir)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read manifest: {manifest_path}") from error

    if not isinstance(manifest, dict):
        raise TypeError("Manifest must be a JSON object")

    samples = manifest.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("Manifest must contain a nonempty samples list")

    expected_images = {
        path.relative_to(dataset_dir).as_posix()
        for class_dir in dataset_dir.iterdir()
        if class_dir.is_dir()
        for path in class_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    }

    seen_images: set[str] = set()
    capture_groups: dict[str, tuple[str, str]] = {}
    class_counts: dict[str, int] = {}

    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise TypeError(f"Sample {index} must be an object")

        required = (
            "image_path",
            "gesture_id",
            "capture_group_id",
            "guided_stage_id",
        )

        for field in required:
            value = sample.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Sample {index} has invalid {field}")

        image_path = sample["image_path"]
        gesture_id = sample["gesture_id"]
        group_id = sample["capture_group_id"]
        stage_id = sample["guided_stage_id"]

        relative_path = Path(image_path)

        if (
            relative_path.is_absolute()
            or len(relative_path.parts) != 2
            or any(part in {".", ".."} for part in image_path.split("/"))
            or "\\" in image_path
        ):
            raise ValueError(f"Invalid image path: {image_path}")

        if relative_path.parts[0] != gesture_id:
            raise ValueError(f"Gesture label mismatch: {image_path}")

        if image_path not in expected_images:
            raise ValueError(f"Image not found in dataset: {image_path}")

        if image_path in seen_images:
            raise ValueError(f"Duplicate image reference: {image_path}")

        seen_images.add(image_path)

        group_identity = (gesture_id, stage_id)
        if group_id in capture_groups:
            if capture_groups[group_id] != group_identity:
                raise ValueError(f"Inconsistent capture group: {group_id}")
        else:
            capture_groups[group_id] = group_identity

        class_counts[gesture_id] = class_counts.get(gesture_id, 0) + 1

    missing_images = expected_images - seen_images
    if missing_images:
        raise ValueError(f"Images missing from manifest: {sorted(missing_images)}")

    return ManifestValidationResult(
        total_samples=len(samples),
        total_capture_groups=len(capture_groups),
        class_counts=class_counts,
    )
