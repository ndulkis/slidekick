import json

import pytest

from slidekick.command_policy import InvalidGestureBindingError
from slidekick.gesture_profile import default_bindings, load_bindings, save_bindings

DEFAULTS = {"swipe_right": "next", "swipe_left": "previous"}


def test_defaults_match_the_controller_defaults():
    assert default_bindings() == DEFAULTS


def test_missing_file_loads_the_defaults(tmp_path):
    assert load_bindings(tmp_path / "gesture_bindings.json") == DEFAULTS


def test_no_path_loads_the_defaults():
    assert load_bindings(None) == DEFAULTS


def test_saved_bindings_load_back(tmp_path):
    path = tmp_path / "profiles" / "gesture_bindings.json"
    swapped = {"swipe_right": "previous", "swipe_left": "next"}

    assert save_bindings(path, swapped) == swapped
    assert load_bindings(path) == swapped


def test_saved_file_records_version_and_profile(tmp_path):
    path = tmp_path / "gesture_bindings.json"
    save_bindings(path, DEFAULTS)

    saved = json.loads(path.read_text())
    assert saved["version"] == 1
    assert saved["profile_id"] == "default"
    assert saved["bindings"] == DEFAULTS


def test_rejected_bindings_are_not_saved(tmp_path):
    path = tmp_path / "gesture_bindings.json"

    with pytest.raises(InvalidGestureBindingError):
        save_bindings(path, {"swipe_right": "end"})

    assert not path.exists()


def test_rejected_save_keeps_the_previous_file(tmp_path):
    path = tmp_path / "gesture_bindings.json"
    save_bindings(path, DEFAULTS)

    with pytest.raises(InvalidGestureBindingError):
        save_bindings(path, {"swipe_right": "delete_everything"})

    assert load_bindings(path) == DEFAULTS


def test_hand_edited_unbindable_command_loads_the_defaults(tmp_path):
    path = tmp_path / "gesture_bindings.json"
    path.write_text(json.dumps({"version": 1, "bindings": {"swipe_right": "end"}}))

    assert load_bindings(path) == DEFAULTS


@pytest.mark.parametrize(
    "content",
    ["not json", "[]", json.dumps({"version": 1}), json.dumps({"bindings": "next"})],
)
def test_corrupt_file_loads_the_defaults(tmp_path, content):
    path = tmp_path / "gesture_bindings.json"
    path.write_text(content)

    assert load_bindings(path) == DEFAULTS
