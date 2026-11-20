from unittest.mock import Mock

from slidekick.training_job_client import TrainingJobClient


def mock_response(value):
    return Mock(raise_for_status=Mock(), json=Mock(return_value=value))


def test_training_request_id_is_reusable(monkeypatch):
    captured = []

    def post(url, json, timeout):
        captured.append((url, json, timeout))
        return mock_response({"training_job_id": "job_1", "accepted": True})

    monkeypatch.setattr("slidekick.training_job_client.requests.post", post)
    client = TrainingJobClient()
    result = client.request_training(
        "profile_1", "data/manifest.json", [], request_id="request_1"
    )
    assert result["training_job_id"] == "job_1"
    assert captured[0][1]["request_id"] == "request_1"
    assert "active_model_version" not in captured[0][1]


def test_activation_only_requests_not_automatically_persists(monkeypatch):
    captured = []

    def post(url, json, timeout):
        captured.append((url, json))
        return mock_response({"success": True, "active_model_version": "v2"})

    monkeypatch.setattr("slidekick.training_job_client.requests.post", post)
    result = TrainingJobClient().request_activation("profile_1", "v2", "models/v2.task")
    assert result["active_model_version"] == "v2"
    assert captured[0][0].endswith("/activate")


def test_malformed_service_response_is_error(monkeypatch):
    monkeypatch.setattr(
        "slidekick.training_job_client.requests.get",
        lambda url, timeout: mock_response([]),
    )
    assert TrainingJobClient().poll_status("job_1")["status"] == "error"


def test_bad_status_id_is_rejected():
    assert TrainingJobClient().poll_status("../bad")["status"] == "error"
