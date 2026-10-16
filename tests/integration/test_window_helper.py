import pytest
from unittest.mock import patch

from windows_helper import app


@pytest.mark.parametrize(
    ("endpoint", "command"),
    [
        ("/next", "next"),
        ("/previous", "previous"),
        ("/pause", "pause"),
        ("/resume", "resume"),
    ],
)
def test_helper_command_endpoint_success(endpoint, command):
    """Verify all valid endpoints successfully invoke the adapter and return 200."""
    with (
        app.test_client() as client,
        patch("windows_helper.adapter.execute_command") as mock_execute,
    ):
        mock_execute.return_value = {
            "status": "success",
            "command": command,
        }

        response = client.post(endpoint)

    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "command": command,
    }
    mock_execute.assert_called_once_with(command)


def test_helper_command_endpoint_failure():
    """Verify native execution errors are caught and return a 500 status code."""
    with (
        app.test_client() as client,
        patch("windows_helper.adapter.execute_command") as mock_execute,
    ):
        mock_execute.return_value = {
            "status": "error",
            "error": "Native Execution Error",
            "command": "next",
            "message": "Mocked failure",
        }

        response = client.post("/next")

    assert response.status_code == 500
    assert response.json == {
        "status": "error",
        "error": "Native Execution Error",
        "command": "next",
        "message": "Mocked failure",
    }
    mock_execute.assert_called_once_with("next")