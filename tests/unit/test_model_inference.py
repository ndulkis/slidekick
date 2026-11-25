"""Tests for evaluating trained MediaPipe gesture models."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from PIL import Image

from slidekick.recognition import model_inference


def create_test_image(path: Path) -> None:
    """Create a small RGB image for evaluation tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 16), color=(120, 80, 200)).save(path)


def create_dataset(tmp_path: Path) -> tuple[Path, Path]:
    """Create a candidate artifact and labeled evaluation images."""
    model_path = tmp_path / "candidate.task"
    model_path.write_bytes(b"fake-model")

    evaluation_dir = tmp_path / "evaluation"

    create_test_image(evaluation_dir / "pinch" / "pinch_01.png")
    create_test_image(evaluation_dir / "pinch" / "pinch_02.png")
    create_test_image(evaluation_dir / "none" / "none_01.png")
    create_test_image(evaluation_dir / "none" / "none_02.png")

    return model_path, evaluation_dir


def mock_recognizer(
    monkeypatch: pytest.MonkeyPatch,
    predictions: list[str],
) -> MagicMock:
    """Replace model inference with a predictable sequence of predictions."""

    # Avoid loading MediaPipe's native image library during unit tests.
    monkeypatch.setattr(
        model_inference.mp,
        "Image",
        Mock(),
    )

    recognizer = MagicMock()

    results = []
    for label in predictions:
        if label == "NO_RESULT":
            results.append(SimpleNamespace(gestures=[]))
        else:
            category = SimpleNamespace(category_name=label)
            results.append(SimpleNamespace(gestures=[[category]]))

    recognizer.recognize.side_effect = results

    context = MagicMock()
    context.__enter__.return_value = recognizer

    factory = MagicMock(return_value=context)

    monkeypatch.setattr(
        model_inference.mp.tasks.vision.GestureRecognizer,
        "create_from_options",
        factory,
    )

    return recognizer


def test_perfect_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Correct predictions should yield perfect accuracy."""
    model_path, evaluation_dir = create_dataset(tmp_path)

    recognizer = mock_recognizer(
        monkeypatch,
        ["pinch", "pinch", "None", "None"],
    )

    result = model_inference.evaluate_model(
        model_path,
        evaluation_dir,
        labels=["pinch", "none"],
    )

    assert result.total_samples == 4
    assert result.correct_predictions == 4
    assert result.accuracy == pytest.approx(1.0)
    assert result.none_false_positive_rate == pytest.approx(0.0)
    assert recognizer.recognize.call_count == 4


def test_background_false_activations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A background sample predicted as pinch is a false activation."""
    model_path, evaluation_dir = create_dataset(tmp_path)

    mock_recognizer(
        monkeypatch,
        ["pinch", "pinch", "pinch", "NO_RESULT"],
    )

    result = model_inference.evaluate_model(
        model_path,
        evaluation_dir,
        labels=["pinch", "none"],
    )

    assert result.accuracy == pytest.approx(0.75)
    assert result.none_false_positive_rate == pytest.approx(0.5)
    assert result.confusion_matrix["none"]["pinch"] == 1


def test_missing_model_is_rejected(tmp_path: Path) -> None:
    """Evaluation cannot run without a candidate model."""
    evaluation_dir = tmp_path / "evaluation"
    evaluation_dir.mkdir()

    with pytest.raises(ValueError, match="Candidate model not found"):
        model_inference.evaluate_model(
            tmp_path / "missing.task",
            evaluation_dir,
            labels=["pinch", "none"],
        )


def test_missing_class_directory_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every declared evaluation class must have a directory."""
    model_path, evaluation_dir = create_dataset(tmp_path)

    mock_recognizer(monkeypatch, ["pinch", "pinch"])

    with pytest.raises(ValueError, match="Missing evaluation class"):
        model_inference.evaluate_model(
            model_path,
            evaluation_dir,
            labels=["pinch", "thumbs_up", "none"],
        )


@pytest.mark.parametrize(
    "labels",
    [
        [],
        ["pinch", "pinch"],
        ["pinch", ""],
    ],
)
def test_invalid_evaluation_labels_are_rejected(
    tmp_path: Path,
    labels: list[str],
) -> None:
    """Class labels must be valid and unique."""
    model_path, evaluation_dir = create_dataset(tmp_path)

    with pytest.raises(ValueError, match="Evaluation labels"):
        model_inference.evaluate_model(
            model_path,
            evaluation_dir,
            labels=labels,
        )


def test_unknown_prediction_is_not_silently_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unexpected model labels must not be counted as correct."""
    model_path, evaluation_dir = create_dataset(tmp_path)

    mock_recognizer(
        monkeypatch,
        ["Open_Palm", "pinch", "None", "None"],
    )

    with pytest.raises(ValueError, match="Unknown predicted label"):
        model_inference.evaluate_model(
            model_path,
            evaluation_dir,
            labels=["pinch", "none"],
        )


def test_evaluated_candidate_contains_model_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Evaluation results must identify the model that produced them."""

    model_path, evaluation_dir = create_dataset(tmp_path)

    fake_evaluation = Mock()

    monkeypatch.setattr(
        model_inference,
        "evaluate_model",
        Mock(return_value=fake_evaluation),
    )

    result = model_inference.evaluate_candidate_model(
        model_path,
        evaluation_dir,
        labels=["pinch", "none"],
    )

    assert result.model_sha256 == model_inference.calculate_model_hash(model_path)
    assert result.evaluation is fake_evaluation
    assert len(result.model_sha256) == 64


def test_model_change_during_evaluation_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Evaluation cannot approve a model that changed during inference."""

    model_path, evaluation_dir = create_dataset(tmp_path)

    def change_model(*args, **kwargs):
        model_path.write_bytes(b"modified-model")
        return Mock()

    monkeypatch.setattr(
        model_inference,
        "evaluate_model",
        change_model,
    )

    with pytest.raises(RuntimeError, match="changed during evaluation"):
        model_inference.evaluate_candidate_model(
            model_path,
            evaluation_dir,
            labels=["pinch", "none"],
        )


def test_different_model_files_have_different_hashes(
    tmp_path: Path,
) -> None:
    """Different model contents must produce different fingerprints."""

    model_a = tmp_path / "model_a.task"
    model_b = tmp_path / "model_b.task"

    model_a.write_bytes(b"model-version-a")
    model_b.write_bytes(b"model-version-b")

    assert model_inference.calculate_model_hash(
        model_a
    ) != model_inference.calculate_model_hash(model_b)
