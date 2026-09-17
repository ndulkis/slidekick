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
        ("end_presentation", "esc"),
    ],
)
def test_keyboard_adapter_presses_expected_key(adapters, fake_pyautogui, command, key):
    adapter = adapters.KeyboardPresentationAdapter()

    assert getattr(adapter, command)() is True
    fake_pyautogui.press.assert_called_once_with(key)
