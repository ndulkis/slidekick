from unittest.mock import patch

from windows_helper import app


def test_next_endpoint():
    with app.test_client() as client:
        with patch(
            "windows_helper.adapter.execute_command"
        ) as mock_execute:
            mock_execute.return_value = {
                "status": "success",
                "command": "next",
            }

            response = client.post("/next")

    assert response.status_code == 200
    assert response.json == {
        "status": "success",
        "command": "next",
    }
    mock_execute.assert_called_once_with("next")