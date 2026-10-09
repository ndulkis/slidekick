import json
import time
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp

from slidekick.recognition.camera import (
    MAX_FAILED_READS,
    convert_frame_to_mediapipe,
    create_camera_window,
    create_recognizer_options,
    draw_recognition_diagnostic,
    process_hand_detection,
    should_close_window,
)
from slidekick.recognition.sample_recorder import SampleRecorder

OUTPUT_PATH = Path("data/evaluation/s2_recognition_samples.jsonl")

PROTOCOL_VERSION = "s3-r03-t2-tracking-030-v1"

# Ten attempts per condition gives us 100 total trials.
TRIALS_PER_CASE = 3

PREP_TIME_SECONDS = 3.0

@dataclass(frozen=True)
class EvaluationCase:
    name: str
    expected_gesture: str
    instruction: str
    expected_prediction_count: int = 1


EVALUATION_CASES = [
    EvaluationCase(
        name="right_hand_swipe_right",
        expected_gesture="swipe_right",
        instruction="Using your RIGHT hand, perform one normal swipe to the RIGHT.",
    ),
    EvaluationCase(
        name="right_hand_swipe_left",
        expected_gesture="swipe_left",
        instruction="Using your RIGHT hand, perform one normal swipe to the LEFT.",
    ),
    EvaluationCase(
        name="left_hand_swipe_right",
        expected_gesture="swipe_right",
        instruction="Using your LEFT hand, perform one normal swipe to the RIGHT.",
    ),
    EvaluationCase(
        name="left_hand_swipe_left",
        expected_gesture="swipe_left",
        instruction="Using your LEFT hand, perform one normal swipe to the LEFT.",
    ),
    EvaluationCase(
        name="natural_twist_swipe_right",
        expected_gesture="swipe_right",
        instruction=(
            "Perform a natural RIGHT swipe while allowing your wrist/palm "
            "to rotate naturally during the motion."
        ),
    ),
    EvaluationCase(
        name="natural_twist_swipe_left",
        expected_gesture="swipe_left",
        instruction=(
            "Perform a natural LEFT swipe while allowing your wrist/palm "
            "to rotate naturally during the motion."
        ),
    ),
    EvaluationCase(
        name="fast_swipe_right",
        expected_gesture="swipe_right",
        instruction="Perform one very FAST swipe to the RIGHT.",
    ),
    EvaluationCase(
        name="fast_swipe_left",
        expected_gesture="swipe_left",
        instruction="Perform one very FAST swipe to the LEFT.",
    ),
    EvaluationCase(
        name="slow_swipe_right",
        expected_gesture="swipe_right",
        instruction="Perform one deliberately SLOW swipe to the RIGHT.",
    ),
    EvaluationCase(
        name="slow_swipe_left",
        expected_gesture="swipe_left",
        instruction="Perform one deliberately SLOW swipe to the LEFT.",
    ),
    EvaluationCase(
        name="casual_reposition",
        expected_gesture="no_gesture",
        instruction=(
            "Casually reposition your hand sideways without intentionally "
            "performing a swipe."
        ),
        expected_prediction_count=0,
    ),
    EvaluationCase(
        name="short_horizontal_movement",
        expected_gesture="no_gesture",
        instruction=(
            "Move your hand a short distance horizontally, then stop. "
            "Do not perform a full swipe."
        ),
        expected_prediction_count=0,
    ),
    EvaluationCase(
        name="vertical_movement",
        expected_gesture="no_gesture",
        instruction=(
            "Move your hand clearly UP and DOWN while keeping horizontal "
            "movement minimal."
        ),
        expected_prediction_count=0,
    ),
]


def count_completed_s3_trials(output_path):
    if not output_path.exists():
        return 0

    completed = 0

    with output_path.open("r", encoding="utf-8") as sample_file:
        for line in sample_file:
            try:
                sample = json.loads(line)
            except json.JSONDecodeError:
                continue

            if sample.get("protocol_version") == PROTOCOL_VERSION:
                completed += 1

    return completed


def build_evaluation_sequence():
    sequence = []

    # Interleave the conditions instead of doing all 10 repetitions of one
    # condition at once. This reduces the effect of lighting, positioning,
    # fatigue, or practice changing over time.
    for round_number in range(1, TRIALS_PER_CASE + 1):
        for evaluation_case in EVALUATION_CASES:
            sequence.append((round_number, evaluation_case))

    return sequence


def add_case_metadata(
    recorder,
    evaluation_case,
    round_number,
):
    if recorder.active_sample is None:
        return

    recorder.active_sample["scenario"] = evaluation_case.name
    recorder.active_sample["evaluation_round"] = round_number
    recorder.active_sample["instruction"] = evaluation_case.instruction
    recorder.active_sample["expected_prediction_count"] = (
        evaluation_case.expected_prediction_count
    )
    recorder.active_sample["protocol_version"] = PROTOCOL_VERSION


def print_collection_summary(output_path):
    if not output_path.exists():
        return

    samples_by_scenario = defaultdict(list)

    with output_path.open("r", encoding="utf-8") as sample_file:
        for line in sample_file:
            try:
                sample = json.loads(line)
            except json.JSONDecodeError:
                continue

            if sample.get("protocol_version") != PROTOCOL_VERSION:
                continue

            scenario = sample.get("scenario")

            if scenario is not None:
                samples_by_scenario[scenario].append(sample)

    if not samples_by_scenario:
        return

    print("\nS3-R03-T1 Recognition Evaluation Summary")
    print("-" * 72)

    for evaluation_case in EVALUATION_CASES:
        samples = samples_by_scenario.get(evaluation_case.name, [])

        if not samples:
            continue

        total = len(samples)
        correct = sum(bool(sample.get("correct")) for sample in samples)
        accuracy = correct / total

        prediction_counts = [
            int(sample.get("prediction_count", 0)) for sample in samples
        ]

        average_prediction_count = sum(prediction_counts) / total

        print(
            f"{evaluation_case.name:28} "
            f"{correct:2}/{total:<2} correct "
            f"({accuracy:6.1%}) "
            f"avg predictions={average_prediction_count:.2f}"
        )

        if evaluation_case.expected_gesture == "no_gesture":
            false_positives = sum(count > 0 for count in prediction_counts)

            print(
                f"{'':28} "
                f"false positives={false_positives}/{total} "
                f"({false_positives / total:.1%})"
            )

        if evaluation_case.expected_prediction_count > 1:
            count_successes = 0

            for sample in samples:
                matching_predictions = sum(
                    prediction.get("gesture") == evaluation_case.expected_gesture
                    for prediction in sample.get("predictions", [])
                )

                if matching_predictions >= evaluation_case.expected_prediction_count:
                    count_successes += 1

            print(
                f"{'':28} "
                f"detected both swipes={count_successes}/{total} "
                f"({count_successes / total:.1%})"
            )


def run_evaluation():
    evaluation_sequence = build_evaluation_sequence()

    recorder = SampleRecorder(OUTPUT_PATH)

    # Allows a partially completed evaluation file to resume where it stopped.
    sequence_index = count_completed_s3_trials(OUTPUT_PATH)

    if sequence_index >= len(evaluation_sequence):
        print("Evaluation dataset is already complete.")
        print_collection_summary(OUTPUT_PATH)
        return

    print("SlideKick S3-R03-T1 Recognition Evaluation")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total planned trials: {len(evaluation_sequence)}")
    print(f"Completed trials: {sequence_index}")
    print()
    print("Press SPACE to arm the next trial.")
    print("Press Q to quit.")
    print()

    window_name = create_camera_window()

    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_FPS, 30)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    options = create_recognizer_options()
    options.min_tracking_confidence = 0.30

    position_history: deque[tuple[float, float, float]] = deque(maxlen=45)

    last_swipe_time = 0.0
    missed_hand_frames = 0
    failed_reads = 0
    
    # Tracking measurements for the active evaluation trial
    total_processed_frames = 0
    hand_detected_frames = 0
    current_hand_loss_streak = 0
    longest_hand_loss_streak = 0

    pending_case = None
    pending_round = None
    pending_start_time = None
    last_countdown_value = None

    collection_complete = False

    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
        last_frame_timestamp_ms = -1
        last_gesture_name = "none"
        last_gesture_confidence = 0.0

        while True:
            if pending_start_time is not None:
                remaining = math.ceil(
                    pending_start_time - time.monotonic()
                )

                if remaining > 0 and remaining != last_countdown_value:
                    print(f"{remaining} ", end="", flush=True)
                    last_countdown_value = remaining

                elif remaining <= 0 and last_countdown_value != 0:
                    print()
                    print("GO! Waiting for hand detection...")
                    last_countdown_value = 0
        
            success, frame = camera.read()

            if not success:
                failed_reads += 1

                if failed_reads >= MAX_FAILED_READS:
                    print("Error: Could not read frame.")
                    break

                time.sleep(0.03)
                continue

            failed_reads = 0

            frame, mp_image = convert_frame_to_mediapipe(frame)

            frame_timestamp_ms = int(time.monotonic() * 1000)

            if frame_timestamp_ms <= last_frame_timestamp_ms:
                frame_timestamp_ms = last_frame_timestamp_ms + 1

            last_frame_timestamp_ms = frame_timestamp_ms

            result = recognizer.recognize_for_video(
                mp_image,
                frame_timestamp_ms,
            )

            (
                gesture_event,
                landmark_event,
                last_swipe_time,
                missed_hand_frames,
            ) = process_hand_detection(
                result,
                frame,
                position_history,
                last_swipe_time,
                missed_hand_frames,
            )

            if (
                pending_case is not None
                and recorder.active_sample is None
                and pending_start_time is not None
                and time.monotonic() >= pending_start_time
                and landmark_event is not None
            ):
                recorder.start_sample(
                    pending_case.expected_gesture,
                    landmark_event["timestamp"],
                )
                
                # Reset tracking measurements for the new trial
                total_processed_frames = 0
                hand_detected_frames = 0
                current_hand_loss_streak = 0
                longest_hand_loss_streak = 0

                add_case_metadata(
                    recorder,
                    pending_case,
                    pending_round,
                )

                print(f"Hand detected. Recording scenario: {pending_case.name}")

                pending_case = None
                pending_round = None
                pending_start_time = None
                last_countdown_value = None

            if recorder.active_sample is not None:
                # Every successfully processed frame counts
                total_processed_frames += 1

                if landmark_event is not None:
                    hand_detected_frames += 1
                    current_hand_loss_streak = 0

                    recorder.record_landmarks(landmark_event)

                else:
                    current_hand_loss_streak += 1

                    longest_hand_loss_streak = max(
                        longest_hand_loss_streak,
                        current_hand_loss_streak,
                    )

                if gesture_event is not None:
                    recorder.record_prediction(gesture_event)

                current_time = time.monotonic()

                if recorder.should_finish_sample(current_time):
                    # Calculate how often MediaPipe detected the hand
                    detection_rate = (
                        hand_detected_frames / total_processed_frames
                        if total_processed_frames > 0
                        else 0.0
                    )

                    # Save tracking measurements alongside existing sample data
                    recorder.active_sample["tracking_metrics"] = {
                        "total_processed_frames": total_processed_frames,
                        "hand_detected_frames": hand_detected_frames,
                        "detection_rate": round(detection_rate, 4),
                        "longest_hand_loss_streak": longest_hand_loss_streak,
                    }

                    recorder.finish_sample(current_time)

                    print(
                        f"Tracking: {hand_detected_frames}/"
                        f"{total_processed_frames} frames detected "
                        f"({detection_rate:.1%}) | "
                        f"Longest loss: {longest_hand_loss_streak} frames"
                    )

                    sequence_index += 1

                    if sequence_index >= len(evaluation_sequence):
                        collection_complete = True
                        break

                    print(
                        f"\nCompleted {sequence_index}/"
                        f"{len(evaluation_sequence)} trials."
                    )
                    print("Press SPACE when ready for the next trial.\n")

            if gesture_event is not None:
                last_gesture_name = gesture_event["gesture"]
                last_gesture_confidence = gesture_event["confidence"]

            draw_recognition_diagnostic(
                frame,
                last_gesture_name,
                last_gesture_confidence,
            )

            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF

            if (
                key == ord(" ")
                and recorder.active_sample is None
                and pending_case is None
            ):
                round_number, evaluation_case = evaluation_sequence[sequence_index]

                pending_case = evaluation_case
                pending_round = round_number
                pending_start_time = time.monotonic() + PREP_TIME_SECONDS
                last_countdown_value = None

                position_history.clear()
                last_swipe_time = 0.0
                missed_hand_frames = 0

                print("=" * 72)
                print(
                    f"Trial {sequence_index + 1}/"
                    f"{len(evaluation_sequence)}"
                )
                print(f"Evaluation round: {round_number}")
                print(f"Scenario: {evaluation_case.name}")
                print(f"Expected gesture: {evaluation_case.expected_gesture}")
                print(f"Instruction: {evaluation_case.instruction}")
                print()
                print("Countdown: ", end="", flush=True)

                print("=" * 72)
                print(f"Trial {sequence_index + 1}/{len(evaluation_sequence)}")
                print(f"Evaluation round: {round_number}")
                print(f"Scenario: {evaluation_case.name}")
                print(f"Expected gesture: {evaluation_case.expected_gesture}")
                print(f"Instruction: {evaluation_case.instruction}")
                print("Waiting for hand...")
                print("=" * 72)

            if should_close_window(window_name, key):
                break

    camera.release()
    cv2.destroyAllWindows()

    if collection_complete:
        print("\nEvaluation collection complete.")

    print_collection_summary(OUTPUT_PATH)


if __name__ == "__main__":
    run_evaluation()
