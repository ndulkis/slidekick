from dataclasses import dataclass

from slidekick.recognition.evaluation_runs import get_or_create_evaluation_run


@dataclass(frozen=True)
class FakeCase:
    name: str
    expected_gesture: str


def test_completed_evaluation_creates_new_dataset(tmp_path):
    # Create a small evaluation with one planned trial.
    sequence = [(1, FakeCase("swipe_right_test", "swipe_right"))]

    # Start the first evaluation.
    first_path, completed = get_or_create_evaluation_run(
        "test-protocol",
        sequence,
        output_directory=tmp_path,
    )

    assert completed == 0

    # Save one complete trial using the expected metadata.
    import json

    sample = {
        "sample_id": "t1-001",
        "protocol_version": "test-protocol",
        "scenario": "swipe_right_test",
        "evaluation_round": 1,
        "expected_gesture": "swipe_right",
        "sample_end_time": 101.0,
    }

    with first_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(sample) + "\n")

    # Restarting after completion should create a new dataset.
    second_path, completed = get_or_create_evaluation_run(
        "test-protocol",
        sequence,
        output_directory=tmp_path,
    )

    assert second_path != first_path
    assert completed == 0
    assert first_path.exists()
    assert second_path.exists()
