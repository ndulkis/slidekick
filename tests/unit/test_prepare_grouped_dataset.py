"""Tests for multi-gesture dataset preparation."""

import importlib
import json
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def preparation(monkeypatch: pytest.MonkeyPatch):
    scripts_dir = Path(__file__).resolve().parents[2] / "training" / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    return importlib.import_module("prepare_grouped_dataset")


@pytest.fixture
def source_data(tmp_path: Path) -> dict:
    enrollment_root = tmp_path / "enrollment"
    negative_dir = tmp_path / "negatives"
    negative_dir.mkdir()

    samples = []

    for gesture in ("pinch", "thumbs_up"):
        image_path = enrollment_root / "images" / gesture / f"{gesture}_001.jpg"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (32, 32), "white").save(image_path)

        samples.append(
            {
                "gesture_id": gesture,
                "image_ref": f"images/{gesture}/{gesture}_001.jpg",
                "capture_group_id": f"{gesture}_take_01",
                "guided_stage_id": "neutral",
            }
        )

    enrollment_manifest = {
        "class_manifest": [
            {"gesture_id": gesture, "class_label": gesture}
            for gesture in ("pinch", "thumbs_up")
        ],
        "samples": samples,
    }

    enrollment_manifest_path = tmp_path / "enrollment.json"
    enrollment_manifest_path.write_text(
        json.dumps(enrollment_manifest),
        encoding="utf-8",
    )

    Image.new("RGB", (32, 32), "black").save(negative_dir / "negative_001.jpg")

    negative_manifest_path = tmp_path / "negatives.json"
    negative_manifest_path.write_text(
        json.dumps(
            {
                "samples": [
                    {
                        "gesture_id": "none",
                        "image_ref": "negative_001.jpg",
                        "capture_group_id": "background_take_01",
                        "guided_stage_id": "background",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    return {
        "enrollment_root": enrollment_root,
        "negative_dir": negative_dir,
        "enrollment_manifest_path": enrollment_manifest_path,
        "negative_manifest_path": negative_manifest_path,
        "output_dir": tmp_path / "prepared",
    }


def test_prepares_all_gesture_classes(preparation, source_data):
    data = source_data

    dataset_dir, manifest_path = preparation.prepare_grouped_dataset(
        enrollment_manifest_path=data["enrollment_manifest_path"],
        enrollment_root=data["enrollment_root"],
        negative_manifest_path=data["negative_manifest_path"],
        negative_dir=data["negative_dir"],
        output_dir=data["output_dir"],
    )

    assert (dataset_dir / "pinch" / "pinch_001.jpg").is_file()
    assert (dataset_dir / "thumbs_up" / "thumbs_up_001.jpg").is_file()
    assert (dataset_dir / "none" / "negative_001.jpg").is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert len(manifest["samples"]) == 3

    assert {sample["gesture_id"] for sample in manifest["samples"]} == {
        "pinch",
        "thumbs_up",
        "none",
    }


def test_preserves_capture_group_metadata(preparation, source_data):
    data = source_data

    _, manifest_path = preparation.prepare_grouped_dataset(
        data["enrollment_manifest_path"],
        data["enrollment_root"],
        data["negative_manifest_path"],
        data["negative_dir"],
        data["output_dir"],
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    groups = {
        sample["gesture_id"]: sample["capture_group_id"]
        for sample in manifest["samples"]
    }

    assert groups == {
        "pinch": "pinch_take_01",
        "thumbs_up": "thumbs_up_take_01",
        "none": "background_take_01",
    }


def test_rejects_duplicate_negative_reference(preparation, source_data):
    data = source_data

    manifest = json.loads(data["negative_manifest_path"].read_text(encoding="utf-8"))
    manifest["samples"].append(manifest["samples"][0].copy())

    data["negative_manifest_path"].write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate destination"):
        preparation.prepare_grouped_dataset(
            data["enrollment_manifest_path"],
            data["enrollment_root"],
            data["negative_manifest_path"],
            data["negative_dir"],
            data["output_dir"],
        )

    assert not data["output_dir"].exists()
