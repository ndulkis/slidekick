"""R04 HTTP adapter for the *proposed* R03 training interface.

Endpoint names are provisional until R03/R04 agree on the transport contract.
This client does not execute Model Maker or mark a candidate model active.
"""

from __future__ import annotations

from uuid import uuid4

import requests


class TrainingJobClient:
    def __init__(self, ml_service_url: str = "http://127.0.0.1:5005"):
        self.ml_service_url = ml_service_url.rstrip("/")

    def _request(
        self, method: str, path: str, *, payload: dict | None = None, timeout: int = 10
    ) -> dict:
        try:
            if method == "POST":
                response = requests.post(
                    f"{self.ml_service_url}{path}", json=payload, timeout=timeout
                )
            else:
                response = requests.get(f"{self.ml_service_url}{path}", timeout=timeout)
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict):
                return {
                    "status": "error",
                    "message": "ML service returned a non-object response",
                }
            return result
        except (requests.RequestException, ValueError) as exc:
            return {"status": "error", "message": f"ML service request failed: {exc}"}

    def request_training(
        self,
        profile_id: str,
        dataset_ref: str,
        class_manifest: list[dict],
        dataset_version: str = "1.0",
        *,
        request_id: str | None = None,
        active_model_version: str | None = None,
    ) -> dict:
        """Submit a candidate dataset; request_id can be reused for safe retries.

        R03 must implement request-id idempotency. Reusing an ID does not by
        itself prevent duplicate jobs on an uncooperative service.
        """
        payload = {
            "request_id": request_id or str(uuid4()),
            "profile_id": profile_id,
            "dataset_ref": dataset_ref,
            "dataset_version": dataset_version,
            "class_manifest": class_manifest,
        }
        if active_model_version is not None:
            payload["active_model_version"] = active_model_version
        return self._request("POST", "/train", payload=payload)

    def poll_status(self, training_job_id: str) -> dict:
        """Fetch R03's reported stage; never fabricate progress percentages."""
        if not training_job_id or "/" in training_job_id or "?" in training_job_id:
            return {"status": "error", "message": "Invalid training_job_id"}
        return self._request("GET", f"/status/{training_job_id}", timeout=5)

    def cancel_training(self, request_id: str, training_job_id: str) -> dict:
        return self._request(
            "POST",
            "/cancel",
            payload={
                "request_id": request_id,
                "training_job_id": training_job_id,
                "action": "cancel",
            },
        )

    def request_activation(
        self,
        profile_id: str,
        model_version: str,
        artifact_ref: str,
        *,
        request_id: str | None = None,
    ) -> dict:
        """Request R03 load verification via proposed /activate endpoint.

        Caller must persist the new active model/profile ONLY after verifying
        R03's success response and active_model_version.
        """
        return self._request(
            "POST",
            "/activate",
            payload={
                "request_id": request_id or str(uuid4()),
                "profile_id": profile_id,
                "model_version": model_version,
                "artifact_ref": artifact_ref,
            },
        )
