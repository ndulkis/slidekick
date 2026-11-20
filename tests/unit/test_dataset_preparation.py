import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image

from slidekick.recognition.dataset_preparation import prepare_training_dataset
from slidekick.recognition.training_job import TrainingJob
from slidekick.recognition.training_runner import run_wsl_training_job


@pytest.fixture
def enrollment_dataset(tmp_path: Path) -> dict:
    """Create a simulated completed gesture enrollment."""

    enrollment_root = tmp_path / "enrollment"
    gesture_dir = enrollment_root / "images" / "three_fingers"
    gesture_dir.mkdir(parents=True)

    negative_dir = tmp_path / "negatives"
    negative_dir.mkdir()

    gesture_image = gesture_dir / "sample001.jpg"
    negative_image = negative_dir / "negative001.jpg"

    Image.new("RGB", (32, 32), color="white").save(gesture_image)
    Image.new("RGB", (32, 32), color="black").save(negative_image)

    manifest = {
        "schema_version": "1.0",
        "class_manifest": {
            "gesture_id": "three_fingers",
            "class_label": "three_fingers",
        },
        "samples": [
            {
                "gesture_id": "three_fingers",
                "image_ref": str(gesture_image),
                "capture_group_id": "group_001",
                "guided_stage_id": "neutral",
            }
        ],
    }

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    return {
        "manifest_path": manifest_path,
        "enrollment_root": enrollment_root,
        "negative_dir": negative_dir,
        "output_dir": tmp_path / "prepared_dataset",
        "gesture_image": gesture_image,
        "negative_image": negative_image,
    }


def test_prepares_training_dataset(enrollment_dataset: dict) -> None:
    data = enrollment_dataset

    result = prepare_training_dataset(
        manifest_path=data["manifest_path"],
        enrollment_root=data["enrollment_root"],
        negative_dir=data["negative_dir"],
        output_dir=data["output_dir"],
    )

    gesture_output = result / "three_fingers" / "sample001.jpg"
    negative_output = result / "none" / "negative001.jpg"

    assert result == data["output_dir"]
    assert gesture_output.is_file()
    assert negative_output.is_file()

    assert gesture_output.read_bytes() == data["gesture_image"].read_bytes()
    assert negative_output.read_bytes() == data["negative_image"].read_bytes()

    # Confirm source files were not modified.
    assert data["gesture_image"].is_file()
    assert data["negative_image"].is_file()


def test_prepared_dataset_creates_valid_training_job(
    enrollment_dataset: dict,
) -> None:
    data = enrollment_dataset

    prepared_dataset = prepare_training_dataset(
        manifest_path=data["manifest_path"],
        enrollment_root=data["enrollment_root"],
        negative_dir=data["negative_dir"],
        output_dir=data["output_dir"],
    )

    job = TrainingJob(
        job_id="enrollment-integration-test",
        profile_id="demo-profile",
        dataset_dir=prepared_dataset,
        export_dir=prepared_dataset.parent / "exported_model",
    )

    job.validate()

    assert job.dataset_dir == prepared_dataset
    assert (job.dataset_dir / "three_fingers").is_dir()
    assert (job.dataset_dir / "none").is_dir()
    assert not job.export_dir.exists()


def test_prepared_dataset_passes_to_wsl_training_runner(
    enrollment_dataset: dict,
) -> None:
    data = enrollment_dataset

    prepared_dataset = prepare_training_dataset(
        manifest_path=data["manifest_path"],
        enrollment_root=data["enrollment_root"],
        negative_dir=data["negative_dir"],
        output_dir=data["output_dir"],
    )

    job = TrainingJob(
        job_id="integration-test",
        profile_id="demo-profile",
        dataset_dir=prepared_dataset,
        export_dir=prepared_dataset.parent / "exported_model",
    )

    expected_model = job.export_dir / "gesture_recognizer.task"

    def fake_training(command, **kwargs):
        job.export_dir.mkdir(parents=True)
        expected_model.write_bytes(b"mock-model")
        return SimpleNamespace(
            returncode=0,
            stdout="Training completed",
            stderr="",
        )

    with (
        patch(
            "slidekick.recognition.training_runner.windows_path_to_wsl",
            side_effect=lambda path: f"/mnt/test/{path.name}",
        ),
        patch(
            "slidekick.recognition.training_runner.subprocess.run",
            side_effect=fake_training,
        ) as mock_run,
    ):
        result = run_wsl_training_job(
            job=job,
            wsl_python="/training/.venv/bin/python",
            wsl_training_script="/training/scripts/train_prototype.py",
        )

    command = mock_run.call_args.args[0]

    assert command == [
        "wsl.exe",
        "--exec",
        "/training/.venv/bin/python",
        "/training/scripts/train_prototype.py",
        "--dataset-dir",
        "/mnt/test/prepared_dataset",
        "--export-dir",
        "/mnt/test/exported_model",
    ]

    assert result.job_id == "integration-test"
    assert result.profile_id == "demo-profile"
    assert result.model_path == expected_model
    assert result.stdout == "Training completed"


def test_rejects_existing_output_directory(enrollment_dataset: dict) -> None:
    data = enrollment_dataset
    data["output_dir"].mkdir()

    with pytest.raises(ValueError, match="already exists"):
        prepare_training_dataset(
            data["manifest_path"],
            data["enrollment_root"],
            data["negative_dir"],
            data["output_dir"],
        )


def test_rejects_incorrect_gesture_label(enrollment_dataset: dict) -> None:
    data = enrollment_dataset

    manifest = json.loads(data["manifest_path"].read_text(encoding="utf-8"))
    manifest["samples"][0]["gesture_id"] = "pinch"

    data["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="incorrect gesture label"):
        prepare_training_dataset(
            data["manifest_path"],
            data["enrollment_root"],
            data["negative_dir"],
            data["output_dir"],
        )

    assert not data["output_dir"].exists()


def test_rejects_image_outside_enrollment(enrollment_dataset: dict) -> None:
    data = enrollment_dataset

    manifest = json.loads(data["manifest_path"].read_text(encoding="utf-8"))
    manifest["samples"][0]["image_ref"] = str(data["negative_image"])

    data["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="outside its gesture directory"):
        prepare_training_dataset(
            data["manifest_path"],
            data["enrollment_root"],
            data["negative_dir"],
            data["output_dir"],
        )

    assert not data["output_dir"].exists()


def test_rejects_duplicate_sample_filenames(enrollment_dataset: dict) -> None:
    data = enrollment_dataset

    # Create a second source file with the same name in another location.
    second_dir = data["enrollment_root"] / "images" / "three_fingers" / "extra"
    second_dir.mkdir()

    duplicate = second_dir / "sample001.jpg"
    duplicate.write_bytes(b"different-image")

    manifest = json.loads(data["manifest_path"].read_text(encoding="utf-8"))

    manifest["samples"].append(
        {
            "gesture_id": "three_fingers",
            "image_ref": str(duplicate),
            "capture_group_id": "group_002",
            "guided_stage_id": "reposition",
        }
    )

    data["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate filenames"):
        prepare_training_dataset(
            data["manifest_path"],
            data["enrollment_root"],
            data["negative_dir"],
            data["output_dir"],
        )

    assert not data["output_dir"].exists()


def test_rejects_corrupted_training_image(enrollment_dataset: dict) -> None:
    data = enrollment_dataset

    data["gesture_image"].write_bytes(b"not-a-valid-jpeg")

    with pytest.raises(ValueError, match="Invalid training image"):
        prepare_training_dataset(
            data["manifest_path"],
            data["enrollment_root"],
            data["negative_dir"],
            data["output_dir"],
        )

    assert not data["output_dir"].exists()
