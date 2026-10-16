"""Manage uniquely named evaluation datasets and locate previous runs."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ============================================================
# 1. EVALUATION DATASET CONFIGURATION
# ============================================================

# Directory containing recorded recognition evaluation datasets.
EVALUATION_DIRECTORY = Path("data/evaluation")


# ============================================================
# 2. DATASET FILENAME GENERATION
# ============================================================


def create_evaluation_path(
    protocol_version: str,
    sprint: str = "S3",
    role: str = "R03",
    output_directory: Path = EVALUATION_DIRECTORY,
) -> Path:
    """Create a unique path for a new recognition evaluation run."""

    # Ensure the output directory exists before creating datasets.
    output_directory.mkdir(parents=True, exist_ok=True)

    # Preserve the protocol identifier in the filename.
    # Replace unsupported characters with underscores.
    safe_protocol = "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in protocol_version
    )

    # Add a UTC timestamp with microseconds to uniquely identify each run.
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")

    # Construct the dataset filename using sprint, role, and protocol.
    filename = f"{sprint}-{role}_{safe_protocol}_{timestamp}.jsonl"

    output_path = output_directory / filename

    # Create the file exclusively so an existing dataset is never overwritten.
    # If a rare filename collision occurs, generate another timestamp.
    while True:
        try:
            with output_path.open("x", encoding="utf-8"):
                pass
            return output_path

        except FileExistsError:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{sprint}-{role}_{safe_protocol}_{timestamp}.jsonl"
            output_path = output_directory / filename


# ============================================================
# 3. FIND PREVIOUS EVALUATION RUNS
# ============================================================


def find_evaluation_runs(
    protocol_version: str,
    sprint: str = "S3",
    role: str = "R03",
    output_directory: Path = EVALUATION_DIRECTORY,
) -> list[Path]:
    """Return matching evaluation datasets, newest first."""

    # A missing directory means no evaluation runs exist yet.
    if not output_directory.exists():
        return []

    # Build a filename prefix for this sprint, role, and protocol.
    prefix = f"{sprint}-{role}_{protocol_version}_"

    # Find only JSONL files associated with this protocol.
    matching_runs = [
        path
        for path in output_directory.glob("*.jsonl")
        if path.name.startswith(prefix)
    ]

    # Sort by filename because filenames include sortable timestamps.
    return sorted(matching_runs, key=lambda path: path.name, reverse=True)


def count_valid_completed_trials(
    output_path: Path,
    evaluation_sequence: list[tuple[int, Any]],
    protocol_version: str,
) -> int:
    """Validate recorded trials and return the number completed.

    Each saved trial must match the expected evaluation sequence.
    Invalid or out-of-order records raise ValueError rather than
    silently skipping evaluation cases.
    """

    # An empty or nonexistent dataset has no completed trials.
    if not output_path.exists():
        return 0

    completed = 0

    with output_path.open("r", encoding="utf-8") as sample_file:
        for line_number, line in enumerate(sample_file, start=1):
            # Reject corrupted or incomplete JSON lines.
            try:
                sample = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {output_path.name}, line {line_number}."
                ) from error

            # Prevent additional records beyond the planned sequence.
            if completed >= len(evaluation_sequence):
                raise ValueError(
                    f"Dataset contains more trials than expected: {output_path.name}"
                )

            # Check that the saved protocol matches this evaluation.
            if sample.get("protocol_version") != protocol_version:
                raise ValueError(f"Protocol mismatch at line {line_number}.")

            # Check that the trial finished recording.
            if sample.get("sample_end_time") is None:
                raise ValueError(f"Incomplete saved trial at line {line_number}.")

            # SampleRecorder assigns three sample IDs per round.
            # Verify IDs are consecutive so resuming cannot skip trials.
            sample_number = completed + 1

            sample_round = ((sample_number - 1) // 3) + 1
            sample_trial = ((sample_number - 1) % 3) + 1

            expected_sample_id = f"t{sample_round}-{sample_trial:03d}"

            if sample.get("sample_id") != expected_sample_id:
                raise ValueError(
                    f"Unexpected sample ID at line {line_number}: "
                    f"expected {expected_sample_id}, "
                    f"found {sample.get('sample_id')!r}."
                )

            # Get the expected evaluation case for this position.
            expected_round, expected_case = evaluation_sequence[completed]

            # Confirm the scenario and expected gesture match.
            if sample.get("scenario") != expected_case.name:
                raise ValueError(f"Unexpected scenario at line {line_number}.")

            if sample.get("expected_gesture") != expected_case.expected_gesture:
                raise ValueError(f"Unexpected gesture label at line {line_number}.")

            # Ensure the sample's evaluation round matches the planned round.
            if sample.get("evaluation_round") != expected_round:
                raise ValueError(f"Unexpected evaluation round at line {line_number}.")

            completed += 1

    return completed


def get_or_create_evaluation_run(
    protocol_version: str,
    evaluation_sequence: list[tuple[int, Any]],
    sprint: str = "S3",
    role: str = "R03",
    output_directory: Path = EVALUATION_DIRECTORY,
) -> tuple[Path, int]:
    """Resume the latest incomplete evaluation or create a new dataset.

    Returns:
        A tuple containing the selected dataset path and the number
        of completed trials.
    """

    # Find existing datasets matching the sprint, role, and protocol.
    existing_runs = find_evaluation_runs(
        protocol_version=protocol_version,
        sprint=sprint,
        role=role,
        output_directory=output_directory,
    )

    # Check whether the most recent matching evaluation is incomplete.
    if existing_runs:
        latest_run = existing_runs[0]

        # Validate the saved trials before attempting to resume.
        completed_trials = count_valid_completed_trials(
            latest_run,
            evaluation_sequence,
            protocol_version,
        )

        # Resume the existing dataset if it is not yet complete.
        if completed_trials < len(evaluation_sequence):
            print(f"Resuming evaluation: {latest_run.name}")
            print(f"Completed trials: {completed_trials}/{len(evaluation_sequence)}")

            return latest_run, completed_trials

    # If no matching run exists, or the latest run is complete,
    # create a new uniquely named dataset.
    new_run = create_evaluation_path(
        protocol_version=protocol_version,
        sprint=sprint,
        role=role,
        output_directory=output_directory,
    )

    print(f"Created new evaluation dataset: {new_run.name}")

    return new_run, 0
