"""Basic validation for MediaPipe custom gesture datasets."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def validate_image(image_path: Path) -> None:
    """Verify image structure and decode its pixels."""

    try:
        # First opening: verify file structure.
        with Image.open(image_path) as image:
            image.verify()

        # Second opening: decode pixel data.
        with Image.open(image_path) as image:
            image.load()

    except (UnidentifiedImageError, OSError, ValueError, AssertionError) as error:
        raise ValueError(f"Invalid or corrupted image: {image_path}") from error


@dataclass(frozen=True)
class DatasetValidationResult:
    """Summary of a validated gesture dataset."""

    dataset_dir: Path
    class_counts: dict[str, int]
    total_samples: int


def validate_dataset(dataset_dir: Path) -> DatasetValidationResult:
    """Validate the labeled image directory structure."""

    if not dataset_dir.is_dir():
        raise ValueError(f"Dataset directory does not exist: {dataset_dir}")

    class_directories = [path for path in dataset_dir.iterdir() if path.is_dir()]

    if not class_directories:
        raise ValueError("Dataset does not contain any class directories")

    class_names = {path.name for path in class_directories}

    if "none" not in class_names:
        raise ValueError("Dataset must contain a 'none' class")

    if len(class_names - {"none"}) == 0:
        raise ValueError("Dataset must contain at least one custom gesture")

    class_counts: dict[str, int] = {}

    for class_dir in class_directories:
        image_files = [
            path
            for path in class_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not image_files:
            raise ValueError(f"Gesture class '{class_dir.name}' contains no images")

        for image_path in image_files:
            validate_image(image_path)

        class_counts[class_dir.name] = len(image_files)

    unexpected_files = [path.name for path in dataset_dir.iterdir() if path.is_file()]

    if unexpected_files:
        raise ValueError(f"Unexpected files in dataset root: {unexpected_files}")

    return DatasetValidationResult(
        dataset_dir=dataset_dir,
        class_counts=class_counts,
        total_samples=sum(class_counts.values()),
    )
