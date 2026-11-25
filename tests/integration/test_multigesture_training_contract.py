"""Verify R04 enrollment output is compatible with R03 training preparation."""

import base64
import importlib
import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from slidekick.gesture_enrollment import EnrollmentSession


def make_jpeg(color: tuple[int, int, int]) -> bytes:
    """Create a valid JPEG without depending on external datasets."""
    buffer = BytesIO()
    Image.new("RGB", (40, 40), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def complete_enrollment(
    root: Path,
    gesture: str,
    enrollment_id: str,
    color: tuple[int, int, int],
    previous_manifest: Path | None = None,
) -> Path:
    """Exercise the real R04 enrollment and manifest export functions."""
    session = EnrollmentSession(
        profile_id="test_profile",
        enrollment_id=enrollment_id,
        gesture_name=gesture,
        target_per_stage=1,
    )

    encoded_image = base64.b64encode(make_jpeg(color)).decode("ascii")

    for index in range(len(session.STAGES)):
        response = session.add_sample(
            base64_image=encoded_image,
            guided_stage_id=session.current_stage,
            capture_group_id=f"{gesture}_group_{index:02d}",
            output_dir=root,
        )

        assert response["status"] == "success", response

    result = session.complete_session(
        storage_dir=root,
        previous_manifest=previous_manifest,
    )

    assert result["status"] == "success", result

    return Path(result["manifest_file"])


def test_multigesture_enrollment_training_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve old gestures and create disjoint training capture groups."""

    scripts_dir = Path(__file__).resolve().parents[2] / "training" / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    preparation = importlib.import_module("prepare_grouped_dataset")
    manifest_validator = importlib.import_module("manifest_validator")
    group_splitter = importlib.import_module("group_splitter")

    # First enrollment: the existing gesture.
    first_root = tmp_path / "first_enrollment"

    first_manifest = complete_enrollment(
        root=first_root,
        gesture="pinch",
        enrollment_id="first_enrollment",
        color=(255, 0, 0),
    )

    # Second enrollment: preserve the previous gesture's data.
    second_root = tmp_path / "second_enrollment"

    combined_manifest = complete_enrollment(
        root=second_root,
        gesture="thumbs_up",
        enrollment_id="second_enrollment",
        color=(0, 255, 0),
        previous_manifest=first_manifest,
    )

    combined = json.loads(combined_manifest.read_text(encoding="utf-8"))

    assert {entry["gesture_id"] for entry in combined["class_manifest"]} == {
        "pinch",
        "thumbs_up",
    }
    assert len(combined["samples"]) == 16

    # Create grouped background examples.
    negative_dir = tmp_path / "negatives"
    negative_dir.mkdir()

    negative_samples = []

    for index in range(6):
        filename = f"negative_{index:02d}.jpg"
        (negative_dir / filename).write_bytes(make_jpeg((0, 0, 0)))

        negative_samples.append(
            {
                "gesture_id": "none",
                "image_ref": filename,
                "capture_group_id": f"none_group_{index // 2:02d}",
                "guided_stage_id": "background",
            }
        )

    negative_manifest = tmp_path / "negative_manifest.json"
    negative_manifest.write_text(
        json.dumps({"samples": negative_samples}),
        encoding="utf-8",
    )

    # Exercise the actual R03 dataset preparation.
    prepared_dir, grouped_manifest = preparation.prepare_grouped_dataset(
        enrollment_manifest_path=combined_manifest,
        enrollment_root=second_root,
        negative_manifest_path=negative_manifest,
        negative_dir=negative_dir,
        output_dir=tmp_path / "prepared",
    )

    validation = manifest_validator.validate_manifest(
        prepared_dir,
        grouped_manifest,
    )

    assert validation.class_counts == {
        "pinch": 8,
        "thumbs_up": 8,
        "none": 6,
    }
    assert validation.total_samples == 22
    assert validation.total_capture_groups == 19

    # Confirm that images of both gestures survived the second enrollment.
    assert len(list((prepared_dir / "pinch").glob("*.jpg"))) == 8
    assert len(list((prepared_dir / "thumbs_up").glob("*.jpg"))) == 8

    # Verify that complete capture groups stay in one partition.
    split = group_splitter.split_dataset(
        prepared_dir,
        grouped_manifest,
    )

    partitions = (set(split.train), set(split.validation), set(split.test))

    assert all(partition for partition in partitions)
    assert partitions[0].isdisjoint(partitions[1])
    assert partitions[0].isdisjoint(partitions[2])
    assert partitions[1].isdisjoint(partitions[2])

    manifest_data = json.loads(grouped_manifest.read_text(encoding="utf-8"))

    for partition in partitions:
        groups_in_partition = {
            sample["capture_group_id"]
            for sample in manifest_data["samples"]
            if sample["image_path"] in partition
        }

        for group_id in groups_in_partition:
            group_images = {
                sample["image_path"]
                for sample in manifest_data["samples"]
                if sample["capture_group_id"] == group_id
            }

            assert group_images.issubset(partition)

    # All samples must have been assigned to exactly one partition.
    assert len(set.union(*partitions)) == validation.total_samples
