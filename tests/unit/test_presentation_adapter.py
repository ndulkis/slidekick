from unittest import mock
import pytest


def test_base_adapter_cannot_be_instantiated(adapters):
    with pytest.raises(TypeError):
        adapters.PresentationAdapter()


def test_adapter_missing_a_command_cannot_be_instantiated(adapters):
    class Incomplete(adapters.PresentationAdapter):
        def next_slide(self) -> bool:
            return True

    with pytest.raises(TypeError):
        Incomplete()


@pytest.mark.parametrize(
    ("command", "key"),
    [
        ("next_slide", "right"),
        ("previous_slide", "left"),
        ("pause_presentation", "b"),
        ("resume_presentation", "b"),
        ("end_presentation", "esc"),
    ],
)
def test_keyboard_adapter_presses_expected_key(adapters, fake_pyautogui, command, key):
    """S4-TEST1: Verify all supported adapter methods generate intended keyboard commands."""
    adapter = adapters.KeyboardPresentationAdapter()

    assert getattr(adapter, command)() is True
    fake_pyautogui.press.assert_called_once_with(key)


@pytest.mark.parametrize(
    ("command_str", "expected_method"),
    [
        ("next", "next_slide"),
        ("previous", "previous_slide"),
        ("pause", "pause_presentation"),
        ("resume", "resume_presentation"),
    ],
)
def test_execute_command_success_routing(adapters, fake_pyautogui, command_str, expected_method):
    """S4-TEST1: Verify execute_command successfully routes standard string commands."""
    adapter = adapters.KeyboardPresentationAdapter()
    
    with mock.patch.object(adapter, expected_method, return_value=True) as mock_method:
        result = adapter.execute_command(command_str)
        
        mock_method.assert_called_once()
        assert result == {"status": "success", "command": command_str}


@pytest.mark.parametrize(
    "invalid_command",
    ["jump", "", None, "   ", 123],
)
def test_execute_command_invalid_input(adapters, fake_pyautogui, invalid_command):
    """S4-TEST2: Validate error behavior when helper receives invalid/unsupported requests."""
    adapter = adapters.KeyboardPresentationAdapter()
    result = adapter.execute_command(invalid_command)
    
    assert result["status"] == "error"
    assert result["error"] == "Invalid Command"
    assert result["command"] == invalid_command


def test_execute_command_native_execution_error(adapters, fake_pyautogui):
    """S4-TEST2: Validate error behavior when native OS execution fails (e.g., pyautogui crashes)."""
    adapter = adapters.KeyboardPresentationAdapter()
    
    # Mock the underlying method to simulate a native execution crash
    with mock.patch.object(adapter, "next_slide", side_effect=Exception("OS keyboard access denied")):
        result = adapter.execute_command("next")
        
        assert result["status"] == "error"
        assert result["error"] == "Native Execution Error"
        assert result["command"] == "next"
        assert result["message"] == "OS keyboard access denied"