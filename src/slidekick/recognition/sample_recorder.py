import json
import re
from pathlib import Path
from typing import Any

SAMPLE_DURATION = 4.0
SAMPLES_PER_ROUND = 3

SAMPLE_ID_PATTERN = re.compile(r"^t(\d+)-(\d{3})$")


class SampleRecorder:
    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)
        self.active_sample: dict[str, Any] | None = None

        # Continue numbering from previously recorded trial rounds.
        self.sample_count = self._load_sample_count()

    def _load_sample_count(self) -> int:
        if not self.output_path.exists():
            return 0

        highest_sample_number = 0

        with self.output_path.open("r", encoding="utf-8") as sample_file:
            for line in sample_file:
                try:
                    sample = json.loads(line)
                except json.JSONDecodeError:
                    continue

                sample_id = sample.get("sample_id")

                if not isinstance(sample_id, str):
                    continue

                match = SAMPLE_ID_PATTERN.fullmatch(sample_id)

                if match is None:
                    continue

                round_number = int(match.group(1))
                trial_number = int(match.group(2))

                if not 1 <= trial_number <= SAMPLES_PER_ROUND:
                    continue

                sample_number = (round_number - 1) * SAMPLES_PER_ROUND + trial_number

                highest_sample_number = max(
                    highest_sample_number,
                    sample_number,
                )

        return highest_sample_number

    def _create_sample_id(self, sample_number: int) -> str:
        round_number = ((sample_number - 1) // SAMPLES_PER_ROUND) + 1

        trial_number = ((sample_number - 1) % SAMPLES_PER_ROUND) + 1

        return f"t{round_number}-{trial_number:03d}"

    @property
    def next_sample_id(self) -> str:
        return self._create_sample_id(self.sample_count + 1)

    @property
    def next_label_index(self) -> int:
        return self.sample_count % SAMPLES_PER_ROUND

    def start_sample(
        self,
        expected_gesture: str,
        start_time: float,
    ) -> None:
        if self.active_sample is not None:
            return

        sample_id = self.next_sample_id

        self.active_sample = {
            "sample_id": sample_id,
            "expected_gesture": expected_gesture,
            "predicted_gesture": None,
            "confidence": None,
            "sample_start_time": start_time,
            "sample_end_time": None,
            "prediction_time": None,
            "prediction_count": 0,
            "correct": False,
            "predictions": [],
            "frames": [],
        }

    def record_landmarks(
        self,
        landmark_event: dict[str, Any],
    ) -> None:
        if self.active_sample is None:
            return

        self.active_sample["frames"].append(
            {
                "timestamp": landmark_event["timestamp"],
                "landmarks": landmark_event["landmarks"],
            }
        )

    def record_prediction(
        self,
        gesture_event: dict[str, Any],
    ) -> None:
        if self.active_sample is None:
            return

        prediction = {
            "gesture": gesture_event["gesture"],
            "confidence": gesture_event["confidence"],
            "timestamp": gesture_event["timestamp"],
        }

        self.active_sample["predictions"].append(prediction)

    def should_finish_sample(self, current_time: float) -> bool:
        if self.active_sample is None:
            return False

        start_time = float(self.active_sample["sample_start_time"])
        elapsed_time = current_time - start_time

        return elapsed_time >= SAMPLE_DURATION

    def finish_sample(self, end_time: float) -> None:
        if self.active_sample is None:
            return

        self.active_sample["sample_end_time"] = end_time

        expected = self.active_sample["expected_gesture"]
        predictions = self.active_sample["predictions"]

        self.active_sample["prediction_count"] = len(predictions)

        representative_prediction = None

        if expected == "no_gesture":
            self.active_sample["correct"] = len(predictions) == 0

            if predictions:
                representative_prediction = predictions[0]

        else:
            matching_prediction = next(
                (
                    prediction
                    for prediction in predictions
                    if prediction["gesture"] == expected
                ),
                None,
            )

            self.active_sample["correct"] = matching_prediction is not None

            if matching_prediction is not None:
                representative_prediction = matching_prediction
            elif predictions:
                representative_prediction = predictions[0]

        if representative_prediction is not None:
            self.active_sample["predicted_gesture"] = representative_prediction[
                "gesture"
            ]
            self.active_sample["confidence"] = representative_prediction["confidence"]
            self.active_sample["prediction_time"] = representative_prediction[
                "timestamp"
            ]

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.output_path.open(
            "a",
            encoding="utf-8",
        ) as sample_file:
            sample_file.write(json.dumps(self.active_sample) + "\n")

        print(
            f"Saved {self.active_sample['sample_id']}: "
            f"expected={expected}, "
            f"predicted="
            f"{self.active_sample['predicted_gesture']}, "
            f"predictions={len(predictions)}, "
            f"correct={self.active_sample['correct']}"
        )

        self.sample_count += 1
        self.active_sample = None
