"""Gesture enrollment backend prototype for sample collection and storage."""

import json
import os
from datetime import datetime, timezone
from uuid import uuid4


class EnrollmentSession:
    def __init__(self, gesture_name: str, target_samples: int = 10):
        """Initialize a new gesture enrollment session."""
        self.session_id = str(uuid4())
        self.gesture_name = gesture_name
        self.target_samples = target_samples
        self.samples = []
        self.status = (
            "collecting"  # States: collecting, validating, completed, cancelled
        )
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add_sample(self, landmarks: list) -> dict:
        """Add a landmark sample to the current session."""
        if self.status != "collecting":
            return {"error": f"Cannot add sample. Session is {self.status}."}

        if not landmarks or len(landmarks) == 0:
            return {"error": "Invalid sample data."}

        self.samples.append(
            {"timestamp": datetime.now(timezone.utc).isoformat(), "landmarks": landmarks}
        )

        if len(self.samples) >= self.target_samples:
            self.status = "validating"

        return {
            "status": "success",
            "current_count": len(self.samples),
            "target": self.target_samples,
            "session_status": self.status,
        }

    def complete_session(self, storage_dir: str = "dataset") -> dict:
        """Save the collected dataset to local storage for R03's training pipeline."""
        if self.status not in ["validating", "collecting"]:
            return {"error": f"Session cannot be completed from {self.status} state."}

        if len(self.samples) == 0:
            self.status = "cancelled"
            return {"error": "No samples collected. Session cancelled."}

        self.status = "completed"
        os.makedirs(storage_dir, exist_ok=True)

        filename = f"{self.gesture_name}_{self.session_id[:8]}.json"
        filepath = os.path.join(storage_dir, filename)

        dataset = {
            "session_id": self.session_id,
            "gesture_name": self.gesture_name,
            "sample_count": len(self.samples),
            "created_at": self.created_at,
            "samples": self.samples,
        }

        with open(filepath, "w") as f:
            json.dump(dataset, f, indent=4)

        return {
            "status": "success",
            "file": filepath,
            "samples_saved": len(self.samples),
        }

    def cancel_session(self) -> dict:
        """Cancel the current session and discard all collected samples."""
        self.status = "cancelled"
        self.samples = []
        return {
            "status": "cancelled",
            "message": "Session aborted and samples cleared.",
        }
