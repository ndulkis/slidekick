"""Create reproducible, capture-group-aware dataset partitions."""

import json
import random
from dataclasses import dataclass
from pathlib import Path

from manifest_validator import validate_manifest


@dataclass(frozen=True)
class DatasetSplit:
    """Image paths assigned to each dataset partition."""

    train: tuple[str, ...]
    validation: tuple[str, ...]
    test: tuple[str, ...]


def split_dataset(
    dataset_dir: Path,
    manifest_path: Path,
    seed: int = 42,
) -> DatasetSplit:
    """Split independent capture groups within each gesture class."""

    # Validate the manifest and referenced images first.
    validate_manifest(dataset_dir, manifest_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # gesture_id -> capture_group_id -> image paths
    groups_by_class: dict[str, dict[str, list[str]]] = {}

    for sample in manifest["samples"]:
        gesture_id = sample["gesture_id"]
        group_id = sample["capture_group_id"]
        image_path = sample["image_path"]

        class_groups = groups_by_class.setdefault(gesture_id, {})
        class_groups.setdefault(group_id, []).append(image_path)

    rng = random.Random(seed)

    train: list[str] = []
    validation: list[str] = []
    test: list[str] = []

    for gesture_id in sorted(groups_by_class):
        groups = list(groups_by_class[gesture_id].values())

        if len(groups) < 3:
            raise ValueError(
                f"Gesture '{gesture_id}' needs at least 3 independent "
                f"capture groups; found {len(groups)}"
            )

        rng.shuffle(groups)

        # Reserve at least one group for validation and testing.
        group_count = len(groups)
        validation_count = max(1, round(group_count * 0.2))
        test_count = max(1, round(group_count * 0.2))

        # Ensure at least one group remains for training.
        if validation_count + test_count >= group_count:
            validation_count = 1
            test_count = 1

        training_count = group_count - validation_count - test_count

        for group in groups[:training_count]:
            train.extend(group)

        for group in groups[training_count : training_count + validation_count]:
            validation.extend(group)

        for group in groups[training_count + validation_count :]:
            test.extend(group)

    return DatasetSplit(
        train=tuple(train),
        validation=tuple(validation),
        test=tuple(test),
    )
