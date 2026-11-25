"""Test grouped Model Maker training without importing the real Model Maker."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def training_module(monkeypatch: pytest.MonkeyPatch):
    """Load the training script with a lightweight fake Model Maker."""

    scripts_dir = Path(__file__).resolve().parents[2] / "training" / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    fake_maker = ModuleType("mediapipe_model_maker")
    fake_recognizer = SimpleNamespace(
        Dataset=SimpleNamespace(from_folder=Mock()),
        HandDataPreprocessingParams=Mock(),
        HParams=Mock(side_effect=lambda **kwargs: SimpleNamespace(**kwargs)),
        GestureRecognizerOptions=Mock(
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs)
        ),
        GestureRecognizer=SimpleNamespace(create=Mock()),
    )

    fake_maker.gesture_recognizer = fake_recognizer
    monkeypatch.setitem(sys.modules, "mediapipe_model_maker", fake_maker)

    module_path = scripts_dir / "train_prototype.py"
    spec = importlib.util.spec_from_file_location(
        "slidekick_grouped_training_test",
        module_path,
    )
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)

    return module, fake_recognizer


@pytest.fixture
def grouped_setup(training_module, monkeypatch, tmp_path):
    """Configure three fake datasets and one successful model export."""

    module, recognizer = training_module

    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    manifest_path = tmp_path / "capture_groups.json"
    manifest_path.write_text('{"samples": []}', encoding="utf-8")

    export_dir = tmp_path / "export"

    partitions = SimpleNamespace(
        train=tmp_path / "partitions" / "train",
        validation=tmp_path / "partitions" / "validation",
        test=tmp_path / "partitions" / "test",
    )

    prepare = Mock(return_value=partitions)
    monkeypatch.setattr(module, "prepare_partitions", prepare)

    monkeypatch.setattr(
        module,
        "validate_dataset",
        Mock(
            return_value=SimpleNamespace(
                class_counts={"pinch": 10, "none": 10},
                total_samples=20,
            )
        ),
    )

    labels = ["none", "pinch"]

    datasets = [
        SimpleNamespace(label_names=labels, __len__=lambda: 6),
        SimpleNamespace(label_names=labels, __len__=lambda: 2),
        SimpleNamespace(label_names=labels, __len__=lambda: 2),
    ]

    # Use a real class for __len__, which Python looks up on the type.
    class FakeDataset:
        def __init__(self, count, label_names):
            self.count = count
            self.label_names = label_names

        def __len__(self):
            return self.count

        def split(self, _fraction):
            raise AssertionError("Grouped training must not randomly split images")

    datasets = [
        FakeDataset(6, labels),
        FakeDataset(2, labels),
        FakeDataset(2, labels),
    ]

    recognizer.Dataset.from_folder.side_effect = datasets

    fake_model = SimpleNamespace(
        evaluate=Mock(return_value=(0.1, 0.9)),
    )

    def export_model():
        export_dir.mkdir(parents=True, exist_ok=True)
        (export_dir / "gesture_recognizer.task").write_bytes(b"test-model")

    fake_model.export_model = Mock(side_effect=export_model)
    recognizer.GestureRecognizer.create.return_value = fake_model

    return SimpleNamespace(
        module=module,
        recognizer=recognizer,
        dataset_dir=dataset_dir,
        manifest_path=manifest_path,
        export_dir=export_dir,
        partitions=partitions,
        prepare=prepare,
        fake_model=fake_model,
    )


def test_grouped_training_uses_independent_partitions(grouped_setup):
    setup = grouped_setup

    result = setup.module.train_model(
        dataset_dir=setup.dataset_dir,
        export_dir=setup.export_dir,
        config=setup.module.TrainingConfig(),
        manifest_path=setup.manifest_path,
    )

    setup.prepare.assert_called_once_with(
        dataset_dir=setup.dataset_dir,
        manifest_path=setup.manifest_path,
        output_dir=setup.export_dir / "partitions",
    )

    loaded = [
        Path(call.kwargs["dirname"])
        for call in setup.recognizer.Dataset.from_folder.call_args_list
    ]

    assert loaded == [
        setup.partitions.train,
        setup.partitions.validation,
        setup.partitions.test,
    ]

    assert result.training_samples == 6
    assert result.validation_samples == 2
    assert result.test_samples == 2
    assert result.model_path.is_file()


def test_grouped_training_uses_validation_for_training_and_test_for_evaluation(
    grouped_setup,
):
    setup = grouped_setup

    setup.module.train_model(
        dataset_dir=setup.dataset_dir,
        export_dir=setup.export_dir,
        config=setup.module.TrainingConfig(),
        manifest_path=setup.manifest_path,
    )

    created = setup.recognizer.GestureRecognizer.create.call_args.kwargs

    assert created["train_data"].count == 6
    assert created["validation_data"].count == 2

    evaluated = setup.fake_model.evaluate.call_args.args[0]
    assert evaluated.count == 2


def test_rejects_inconsistent_partition_labels(grouped_setup):
    setup = grouped_setup

    class FakeDataset:
        def __init__(self, labels):
            self.label_names = labels

        def __len__(self):
            return 5

    setup.recognizer.Dataset.from_folder.side_effect = [
        FakeDataset(["none", "pinch"]),
        FakeDataset(["pinch", "none"]),
        FakeDataset(["none", "pinch"]),
    ]

    with pytest.raises(ValueError, match="inconsistent label mappings"):
        setup.module.train_model(
            dataset_dir=setup.dataset_dir,
            export_dir=setup.export_dir,
            config=setup.module.TrainingConfig(),
            manifest_path=setup.manifest_path,
        )

    setup.recognizer.GestureRecognizer.create.assert_not_called()


def test_rejects_empty_partition_after_preprocessing(grouped_setup):
    setup = grouped_setup

    class FakeDataset:
        def __init__(self, count):
            self.count = count
            self.label_names = ["none", "pinch"]

        def __len__(self):
            return self.count

    setup.recognizer.Dataset.from_folder.side_effect = [
        FakeDataset(6),
        FakeDataset(0),
        FakeDataset(2),
    ]

    with pytest.raises(ValueError, match="Dataset too small"):
        setup.module.train_model(
            dataset_dir=setup.dataset_dir,
            export_dir=setup.export_dir,
            config=setup.module.TrainingConfig(),
            manifest_path=setup.manifest_path,
        )

    setup.recognizer.GestureRecognizer.create.assert_not_called()
