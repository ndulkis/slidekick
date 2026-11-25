"""Tests for capture-group-aware Model Maker dataset partitions."""

import importlib
import json
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def partition_module(monkeypatch: pytest.MonkeyPatch):
    """Load the training script module using its existing import layout."""

    scripts_dir = Path(__file__).resolve().parents[2] / "training" / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    return importlib.import_module("partition_dataset")


@pytest.fixture
def sample_dataset(tmp_path: Path) -> tuple[Path, Path]:
    """Create two gesture classes with three independent groups each."""

    dataset_dir = tmp_path / "dataset"
    manifest_path = tmp_path / "manifest.json"

    samples = []

    for gesture in ("pinch", "none"):
        for group_index in range(3):
            group_id = f"{gesture}-session-{group_index}"

            for image_index in range(2):
                filename = f"{group_id}-{image_index}.png"
                image_path = dataset_dir / gesture / filename

                image_path.parent.mkdir(parents=True, exist_ok=True)
                Image.new(
                    "RGB",
                    (16, 16),
                    color=(group_index * 40, image_index * 50, 100),
                ).save(image_path)

                samples.append(
                    {
                        "image_path": f"{gesture}/{filename}",
                        "gesture_id": gesture,
                        "capture_group_id": group_id,
                        "guided_stage_id": "stage-1",
                    }
                )

    manifest_path.write_text(
        json.dumps({"samples": samples}),
        encoding="utf-8",
    )

    return dataset_dir, manifest_path


def test_creates_three_partitions(
    partition_module,
    sample_dataset: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """Every partition should contain every gesture class."""

    dataset_dir, manifest_path = sample_dataset

    paths = partition_module.prepare_partitions(
        dataset_dir,
        manifest_path,
        tmp_path / "partitions",
    )

    for directory in (paths.train, paths.validation, paths.test):
        assert directory.is_dir()
        assert (directory / "pinch").is_dir()
        assert (directory / "none").is_dir()

    total_images = sum(
        len(list(directory.rglob("*.png")))
        for directory in (paths.train, paths.validation, paths.test)
    )

    assert total_images == 12


def test_capture_groups_never_overlap(
    partition_module,
    sample_dataset: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """Images from one capture session must stay in one partition."""

    dataset_dir, manifest_path = sample_dataset

    paths = partition_module.prepare_partitions(
        dataset_dir,
        manifest_path,
        tmp_path / "partitions",
    )

    group_locations = {}

    for name, directory in (
        ("train", paths.train),
        ("validation", paths.validation),
        ("test", paths.test),
    ):
        for image_path in directory.rglob("*.png"):
            # Filename format: gesture-session-number-image.png
            group_id = image_path.stem.rsplit("-", 1)[0]

            group_locations.setdefault(group_id, set()).add(name)

    assert group_locations
    assert all(len(locations) == 1 for locations in group_locations.values())


def test_same_seed_produces_same_split(
    partition_module,
    sample_dataset: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """The same dataset and seed should produce reproducible assignments."""

    dataset_dir, manifest_path = sample_dataset

    first = partition_module.prepare_partitions(
        dataset_dir,
        manifest_path,
        tmp_path / "first",
        seed=42,
    )

    second = partition_module.prepare_partitions(
        dataset_dir,
        manifest_path,
        tmp_path / "second",
        seed=42,
    )

    for first_dir, second_dir in (
        (first.train, second.train),
        (first.validation, second.validation),
        (first.test, second.test),
    ):
        first_files = {
            path.relative_to(first_dir).as_posix() for path in first_dir.rglob("*.png")
        }

        second_files = {
            path.relative_to(second_dir).as_posix()
            for path in second_dir.rglob("*.png")
        }

        assert first_files == second_files


def test_existing_output_directory_is_rejected(
    partition_module,
    sample_dataset: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """Previous partition artifacts must not be overwritten."""

    dataset_dir, manifest_path = sample_dataset
    output_dir = tmp_path / "partitions"
    output_dir.mkdir()

    with pytest.raises(ValueError, match="already exists"):
        partition_module.prepare_partitions(
            dataset_dir,
            manifest_path,
            output_dir,
        )


def test_output_inside_source_dataset_is_rejected(
    partition_module,
    sample_dataset: tuple[Path, Path],
) -> None:
    """Generated partitions must not contaminate the source dataset."""

    dataset_dir, manifest_path = sample_dataset

    with pytest.raises(ValueError, match="inside source dataset"):
        partition_module.prepare_partitions(
            dataset_dir,
            manifest_path,
            dataset_dir / "partitions",
        )


def test_insufficient_capture_groups_are_rejected(
    partition_module,
    sample_dataset: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """Each gesture requires independent groups for all three splits."""

    dataset_dir, manifest_path = sample_dataset

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest["samples"] = [
        sample
        for sample in manifest["samples"]
        if sample["capture_group_id"] != "pinch-session-2"
    ]

    for image_path in (dataset_dir / "pinch").glob("pinch-session-2-*.png"):
        image_path.unlink()

    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="at least 3 independent"):
        partition_module.prepare_partitions(
            dataset_dir,
            manifest_path,
            tmp_path / "partitions",
        )
