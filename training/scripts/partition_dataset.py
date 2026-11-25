"""Materialize capture-group-aware splits for MediaPipe Model Maker."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from group_splitter import split_dataset


@dataclass(frozen=True)
class PartitionPaths:
    """Directories containing independent dataset partitions."""

    train: Path
    validation: Path
    test: Path


def prepare_partitions(
    dataset_dir: Path,
    manifest_path: Path,
    output_dir: Path,
    seed: int = 42,
) -> PartitionPaths:
    """Create train, validation, and test directories by capture group."""

    dataset_dir = dataset_dir.resolve()
    output_dir = output_dir.resolve()

    if output_dir.exists():
        raise ValueError(f"Partition output already exists: {output_dir}")

    if output_dir.is_relative_to(dataset_dir):
        raise ValueError("Partition output cannot be inside source dataset")

    if dataset_dir.is_relative_to(output_dir):
        raise ValueError("Source dataset cannot be inside partition output")

    # split_dataset validates the manifest and assigns complete
    # capture groups to separate partitions.
    split = split_dataset(
        dataset_dir=dataset_dir,
        manifest_path=manifest_path,
        seed=seed,
    )

    partitions = {
        "train": split.train,
        "validation": split.validation,
        "test": split.test,
    }

    source_classes = {path.name for path in dataset_dir.iterdir() if path.is_dir()}

    # Verify every partition contains every declared class.
    for partition_name, image_paths in partitions.items():
        present_classes = {Path(path).parts[0] for path in image_paths}

        if present_classes != source_classes:
            raise ValueError(f"{partition_name} partition has incomplete classes")

    # Validate all split references before creating output files.
    all_paths = [
        Path(relative_path)
        for image_paths in partitions.values()
        for relative_path in image_paths
    ]

    if len(all_paths) != len(set(all_paths)):
        raise ValueError("Images overlap between dataset partitions")

    for relative_path in all_paths:
        source = (dataset_dir / relative_path).resolve()

        if not source.is_relative_to(dataset_dir) or not source.is_file():
            raise ValueError(f"Invalid source image: {relative_path}")

    try:
        for partition_name, image_paths in partitions.items():
            partition_dir = output_dir / partition_name

            for relative_path in image_paths:
                relative = Path(relative_path)
                source = dataset_dir / relative
                destination = partition_dir / relative

                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

    except Exception:
        # Don't leave an incomplete dataset mistaken for a valid one.
        shutil.rmtree(output_dir, ignore_errors=True)
        raise

    return PartitionPaths(
        train=output_dir / "train",
        validation=output_dir / "validation",
        test=output_dir / "test",
    )
