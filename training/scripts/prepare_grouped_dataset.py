"""Prepare combined enrollment datasets for capture-group-aware training."""

import json
import shutil
from pathlib import Path, PurePosixPath

from enrollment_manifest_adapter import normalize_enrollment_manifest
from manifest_validator import validate_manifest
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _validate_and_copy(source: Path, destination: Path) -> None:
    """Verify an image before copying it to the prepared dataset."""

    if not source.is_file():
        raise ValueError(f"Source image not found: {source}")

    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported image format: {source}")

    try:
        with Image.open(source) as image:
            image.verify()

        with Image.open(source) as image:
            image.load()
    except (OSError, ValueError) as exc:
        raise ValueError(f"Invalid training image: {source}") from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def prepare_grouped_dataset(
    enrollment_manifest_path: Path,
    enrollment_root: Path,
    negative_manifest_path: Path,
    negative_dir: Path,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Prepare all gesture classes and a grouped negative dataset."""

    enrollment_root = enrollment_root.resolve()
    negative_dir = negative_dir.resolve()
    output_dir = output_dir.resolve()

    if output_dir.exists():
        raise ValueError(f"Training output already exists: {output_dir}")

    if (
        output_dir.is_relative_to(enrollment_root)
        or output_dir.is_relative_to(negative_dir)
        or enrollment_root.is_relative_to(output_dir)
        or negative_dir.is_relative_to(output_dir)
    ):
        raise ValueError("Training output must be separate from source datasets")

    if not enrollment_root.is_dir() or not negative_dir.is_dir():
        raise ValueError("Enrollment and negative directories must exist")

    enrollment = json.loads(enrollment_manifest_path.read_text(encoding="utf-8"))
    negatives = json.loads(negative_manifest_path.read_text(encoding="utf-8"))

    normalized = normalize_enrollment_manifest(enrollment)

    if not isinstance(negatives, dict):
        raise TypeError("Negative manifest must be an object")

    negative_samples = negatives.get("samples")

    if not isinstance(negative_samples, list) or not negative_samples:
        raise TypeError("Negative sample must be an object")

    copy_jobs = []
    all_samples = list(normalized["samples"])

    # Resolve R04 enrollment images.
    for sample in normalized["samples"]:
        relative = PurePosixPath(sample["image_path"])

        source = (
            enrollment_root / "images" / relative.parts[0] / relative.parts[1]
        ).resolve()

        if not source.is_relative_to(enrollment_root):
            raise ValueError("Enrollment image escaped its source root")

        copy_jobs.append((source, output_dir / relative.as_posix()))

    # Normalize negative samples, preserving their capture groups.
    for sample in negative_samples:
        if not isinstance(sample, dict):
            raise TypeError("Negative sample must be an object")

        if sample.get("gesture_id") != "none":
            raise ValueError("Negative sample must have gesture_id 'none'")

        image_ref = sample.get("image_ref")
        group_id = sample.get("capture_group_id")
        stage_id = sample.get("guided_stage_id")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (image_ref, group_id, stage_id)
        ):
            raise ValueError("Negative sample has missing metadata")

        relative = PurePosixPath(image_ref)

        if (
            relative.is_absolute()
            or len(relative.parts) != 1
            or relative.name in {".", ".."}
            or "\\" in image_ref
            or ":" in image_ref
        ):
            raise ValueError("Invalid negative image reference")

        source = (negative_dir / relative.name).resolve()

        if not source.is_relative_to(negative_dir):
            raise ValueError("Negative image escaped its source root")

        destination_relative = f"none/{relative.name}"

        all_samples.append(
            {
                "gesture_id": "none",
                "image_path": destination_relative,
                "capture_group_id": group_id,
                "guided_stage_id": stage_id,
            }
        )

        copy_jobs.append((source, output_dir / destination_relative))

    # Reject duplicate destinations before writing any files.
    destinations = [destination for _, destination in copy_jobs]

    if len(destinations) != len(set(destinations)):
        raise ValueError("Duplicate destination image paths")

    manifest_path = output_dir.parent / f"{output_dir.name}_capture_groups.json"

    if manifest_path.exists():
        raise ValueError(f"Training manifest already exists: {manifest_path}")

    try:
        for source, destination in copy_jobs:
            _validate_and_copy(source, destination)

        manifest_path.write_text(
            json.dumps({"samples": all_samples}, indent=2),
            encoding="utf-8",
        )

        # Verify that all prepared files and metadata agree.
        validate_manifest(output_dir, manifest_path)

    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        manifest_path.unlink(missing_ok=True)
        raise

    return output_dir, manifest_path
