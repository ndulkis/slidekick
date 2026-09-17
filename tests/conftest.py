import importlib
import sys
from unittest import mock

import pytest

ADAPTER_MODULE = "slidekick.presentation_adapter"


@pytest.fixture
def fake_pyautogui():
    """Stand in for pyautogui so adapter code runs without a display.

    pyautogui needs a real display to import, which neither Lando nor CI has.
    Tests assert on the keys pressed instead of pressing them.
    """
    fake = mock.MagicMock(name="pyautogui")
    saved = sys.modules.get("pyautogui")
    sys.modules["pyautogui"] = fake
    sys.modules.pop(ADAPTER_MODULE, None)
    yield fake
    sys.modules.pop(ADAPTER_MODULE, None)
    if saved is None:
        sys.modules.pop("pyautogui", None)
    else:
        sys.modules["pyautogui"] = saved


@pytest.fixture
def adapters(fake_pyautogui):
    """The presentation_adapter module, imported against the fake pyautogui."""
    return importlib.import_module(ADAPTER_MODULE)
