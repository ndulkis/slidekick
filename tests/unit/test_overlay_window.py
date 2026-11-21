"""Where the overlay window goes for each corner chosen in Settings."""

import pytest

pytest.importorskip("webview")  # Installed on macOS and Windows only.

from slidekick.api_server import OVERLAY_POSITIONS
from slidekick.overlay_window import HEIGHT, MARGIN, WIDTH, corner


def test_each_position_lands_in_its_corner():
    w, h = 1920, 1080
    right, bottom = w - WIDTH - MARGIN, h - HEIGHT - MARGIN
    assert {p: corner(p, w, h) for p in OVERLAY_POSITIONS} == {
        "top-left": (MARGIN, MARGIN),
        "top-right": (right, MARGIN),
        "bottom-left": (MARGIN, bottom),
        "bottom-right": (right, bottom),
    }
    assert corner("bogus", w, h) == (right, MARGIN)
