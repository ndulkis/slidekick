import json
import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from slidekick.command_policy import GESTURE_ID_PATTERN


def validate_image(image_path: Path) -> None:
    """Reject corrupted or unreadable training images."""

    try:
        with Image.open(image_path) as image:
            image.verify()

        # Reopen the image to confirm its pixels can be decoded.
        with Image.open(image_path) as image:
            image.load()

    except (OSError, ValueError, UnidentifiedImageError) as exc:
        raise ValueError(f"Invalid training image: {image_path}") from exc


def prepare_training_dataset(
    manifest_path: Path,
    enrollment_root: Path,
    negative_dir: Path,
    output_dir: Path,
) -> Path:
    """Prepare a Model Maker dataset from a completed enrollment."""

    # Validate input paths
    if not manifest_path.is_file():
        raise ValueError(f"Enrollment manifest does not exist: {manifest_path}")

    if output_dir.exists():
        raise ValueError(f"Training output directory already exists: {output_dir}")

    # Read and validate the manifest
    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if not isinstance(manifest, dict):
        raise TypeError("Enrollment manifest must be a JSON object")

    if not isinstance(manifest.get("class_manifest"), dict):
        raise TypeError("Missing or invalid class_manifest")

    if not isinstance(manifest.get("samples"), list):
        raise TypeError("Missing or invalid samples list")

    # Extract and validate the gesture identifier
    gesture_id = manifest["class_manifest"].get("gesture_id")

    if not isinstance(gesture_id, str):
        raise TypeError("Gesture ID must be a string")

    if not GESTURE_ID_PATTERN.fullmatch(gesture_id):
        raise ValueError(f"Invalid gesture identifier: {gesture_id}")

    if gesture_id == "none":
        raise ValueError("'none' is reserved for the negative gesture class")

    class_label = manifest["class_manifest"].get("class_label")

    if class_label != gesture_id:
        raise ValueError("Class label must match the gesture ID")

    # Prepare gesture and negative samples
    if not negative_dir.is_dir():
        raise ValueError(f"Negative dataset directory does not exist: {negative_dir}")

    negative_images = [
        path
        for path in negative_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]

    if not negative_images:
        raise ValueError("Negative dataset contains no supported images")

    samples = manifest["samples"]

    if not samples:
        raise ValueError("Enrollment contains no gesture samples")

    enrollment_root = enrollment_root.resolve()

    if not enrollment_root.is_dir():
        raise ValueError(f"Enrollment directory does not exist: {enrollment_root}")

    gesture_source_dir = (enrollment_root / "images" / gesture_id).resolve()

    sample_paths = []
    seen_paths = set()

    for sample in samples:
        if not isinstance(sample, dict):
            raise TypeError("Each enrollment sample must be an object")

        if sample.get("gesture_id") != gesture_id:
            raise ValueError("Enrollment sample has an incorrect gesture label")

        image_ref = sample.get("image_ref")

        if not isinstance(image_ref, str) or not image_ref.strip():
            raise ValueError("Enrollment sample is missing image_ref")

        image_path = Path(image_ref)

        if not image_path.is_absolute():
            image_path = enrollment_root / image_path

        image_path = image_path.resolve()

        if not image_path.is_relative_to(gesture_source_dir):
            raise ValueError("Enrollment image is outside its gesture directory")

        if not image_path.is_file():
            raise ValueError(f"Enrollment image does not exist: {image_path}")

        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            raise ValueError(f"Unsupported image format: {image_path}")

        if image_path in seen_paths:
            raise ValueError(f"Duplicate enrollment image: {image_path}")

        seen_paths.add(image_path)
        sample_paths.append(image_path)

    # Prevent different sample files from overwriting each other.
    sample_names = [path.name for path in sample_paths]

    if len(sample_names) != len(set(sample_names)):
        raise ValueError("Enrollment samples contain duplicate filenames")

    # Verify image integrity before creating the output dataset.
    for image_path in [*sample_paths, *negative_images]:
        validate_image(image_path)

    resolved_output = output_dir.resolve()

    if resolved_output.is_relative_to(enrollment_root):
        raise ValueError("Training output cannot be inside enrollment directory")

    if resolved_output.is_relative_to(negative_dir.resolve()):
        raise ValueError("Training output cannot be inside negative dataset")

    # Prepare the destination directories.
    output_dir.mkdir(parents=True, exist_ok=False)

    gesture_output_dir = output_dir / gesture_id
    negative_output_dir = output_dir / "none"

    gesture_output_dir.mkdir()
    negative_output_dir.mkdir()

    # Copy the validated enrollment samples.
    for image_path in sample_paths:
        destination = gesture_output_dir / image_path.name
        shutil.copy2(image_path, destination)

    # Copy the negative samples.
    for image_path in negative_images:
        destination = negative_output_dir / image_path.name
        shutil.copy2(image_path, destination)

    return output_dir
