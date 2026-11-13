"""Client for communicating with the R03 ML Training Environment."""

import requests
from uuid import uuid4


class TrainingJobClient:
    def __init__(self, ml_service_url="http://127.0.0.1:5005"):
        # The URL where Diego's separate Flask/FastAPI training server is running
        self.ml_service_url = ml_service_url

    def request_training(
        self, profile_id, dataset_ref, class_manifest, dataset_version="1.0"
    ):
        """Contract: Train request -> R03"""
        request_id = str(uuid4())
        payload = {
            "request_id": request_id,
            "profile_id": profile_id,
            "dataset_ref": dataset_ref,
            "dataset_version": dataset_version,
            "class_manifest": class_manifest,
        }

        try:
            # POST the dataset manifest to Diego's environment to start training
            response = requests.post(
                f"{self.ml_service_url}/train", json=payload, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"status": "error", "message": f"Failed to contact ML service: {e}"}

    def poll_status(self, training_job_id):
        """Contract: Progress/status -> R04 (queued -> validating -> preparing -> training -> ready)"""
        try:
            # GET request to check how far along the MediaPipe training is
            response = requests.get(
                f"{self.ml_service_url}/status/{training_job_id}", timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"status": "error", "message": f"Failed to get training status: {e}"}

    def cancel_training(self, request_id, training_job_id):
        """Contract: Activate / cancel -> R03"""
        payload = {
            "request_id": request_id,
            "training_job_id": training_job_id,
            "action": "cancel",
        }

        try:
            # POST request to abort a stuck or unwanted training job
            response = requests.post(
                f"{self.ml_service_url}/cancel", json=payload, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"status": "error", "message": f"Failed to cancel training job: {e}"}
