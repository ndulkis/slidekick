"""S4-R01-T2: gesture profile loading and validation, with no session or keyboard."""

import json
from pathlib import Path

import pytest

from slidekick.gesture_command_controller import DEFAULT_GESTURE_BINDINGS
from slidekick.gesture_profile import (
    MAX_PROFILE_BYTES,
    GestureProfile,
    InvalidProfileError,
    default_profile,
    load_profile,
    profile_from_mapping,
)

DEFAULT_PROFILE_FILE = Path(__file__).resolve().parents[2] / "profiles" / "default.json"

GOOD = {
    "version": 1,
    "name": "presenter",
    "bindings": {"swipe_right": "next", "swipe_left": "previous", "fist": "pause"},
}


def good(**changes):
    data = json.loads(json.dumps(GOOD))
    data.update(changes)
    return data


def write(tmp_path, text, name="profile.json"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Valid profiles
# ---------------------------------------------------------------------------


def test_default_file_matches_built_in_defaults():
    profile = load_profile(DEFAULT_PROFILE_FILE)

    assert profile.name == "default"
    assert dict(profile.bindings) == dict(DEFAULT_GESTURE_BINDINGS)
    assert profile == default_profile()


def test_valid_mapping_builds_a_profile():
    profile = profile_from_mapping(GOOD)

    assert profile.name == "presenter"
    assert dict(profile.bindings) == GOOD["bindings"]


def test_empty_bindings_are_valid_and_bind_nothing():
    assert dict(profile_from_mapping(good(bindings={})).bindings) == {}


def test_profile_bindings_are_read_only():
    profile = profile_from_mapping(GOOD)

    with pytest.raises(TypeError):
        profile.bindings["fist"] = "end"
    with pytest.raises(AttributeError):
        profile.name = "other"
    with pytest.raises(AttributeError):
        profile.bindings = {}


def test_profile_does_not_follow_later_edits_to_its_source():
    source = {"swipe_right": "next"}
    profile = GestureProfile(name="copy", bindings=source)
    source["swipe_right"] = "end"

    assert profile.bindings["swipe_right"] == "next"


@pytest.mark.parametrize("name", ["a", "Presenter 2", "my_profile-1.0", "x" * 64])
def test_valid_profile_names(name):
    assert profile_from_mapping(good(name=name)).name == name


# ---------------------------------------------------------------------------
# Rejected profiles
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("data", [None, [], "profile", 5, True, [("version", 1)]])
def test_non_mapping_profile_is_rejected(data):
    with pytest.raises(InvalidProfileError, match="must be a mapping"):
        profile_from_mapping(data)


@pytest.mark.parametrize("field", ["version", "name", "bindings"])
def test_missing_field_is_rejected(field):
    data = good()
    del data[field]

    with pytest.raises(InvalidProfileError, match=f"missing field '{field}'"):
        profile_from_mapping(data)


@pytest.mark.parametrize("version", [0, 2, -1, "1", 1.0, True, None, [1]])
def test_wrong_version_is_rejected(version):
    with pytest.raises(InvalidProfileError, match="version must be"):
        profile_from_mapping(good(version=version))


@pytest.mark.parametrize("extra", [{"shell": "ls"}, {"Name": "x"}, {1: "x"}, {"": 1}])
def test_unknown_fields_are_rejected(extra):
    with pytest.raises(InvalidProfileError, match="unknown fields"):
        profile_from_mapping({**GOOD, **extra})


@pytest.mark.parametrize(
    "name",
    [
        "",
        " lead",
        "_lead",
        "-lead",
        "a\nb",
        "a\tb",
        "x" * 65,
        "snow\u2603",
        None,
        5,
        ["a"],
    ],
)
def test_bad_profile_name_is_rejected(name):
    with pytest.raises(InvalidProfileError, match="not a valid profile name"):
        profile_from_mapping(good(name=name))


@pytest.mark.parametrize(
    "bindings", [None, [], "swipe_right=next", 5, [("swipe_right", "next")]]
)
def test_bindings_must_be_a_mapping(bindings):
    with pytest.raises(InvalidProfileError, match="bindings rejected"):
        profile_from_mapping(good(bindings=bindings))


@pytest.mark.parametrize(
    "bindings",
    [
        {"swipe_right": "end"},
        {"swipe_right": "esc"},
        {"swipe_right": "ctrl+w"},
        {"swipe_right": "Next"},
        {"swipe_right": ["next"]},
        {"swipe_right": None},
        {"Swipe Right": "next"},
        {"swipe-right": "next"},
        {"": "next"},
        {5: "next"},
    ],
    ids=repr,
)
def test_bad_bindings_are_rejected_before_use(bindings):
    with pytest.raises(InvalidProfileError, match="bindings rejected"):
        profile_from_mapping(good(bindings=bindings))


def test_directly_built_profile_is_validated_too():
    with pytest.raises(InvalidProfileError):
        GestureProfile(name="bad", bindings={"swipe_right": "end"})
    with pytest.raises(InvalidProfileError):
        GestureProfile(name="", bindings={"swipe_right": "next"})


def test_one_bad_entry_rejects_the_whole_profile_and_every_problem_is_reported():
    data = good(name="", bindings={"swipe_right": "next", "swipe_left": "ctrl+w"})
    data["extra"] = 1

    with pytest.raises(InvalidProfileError) as caught:
        profile_from_mapping(data)

    message = str(caught.value)
    assert "unknown fields" in message
    assert "not a valid profile name" in message
    assert "swipe_left" in message


def test_error_text_stays_short_for_huge_values():
    with pytest.raises(InvalidProfileError) as caught:
        profile_from_mapping(
            good(name="x" * 5000, bindings={"swipe_right": "y" * 5000})
        )

    assert len(str(caught.value)) < 500


# ---------------------------------------------------------------------------
# Recognition seam: known gestures
# ---------------------------------------------------------------------------


def test_known_gestures_accepts_a_profile_inside_the_set():
    profile = profile_from_mapping(
        GOOD, known_gestures={"swipe_right", "swipe_left", "fist"}
    )

    assert profile.name == "presenter"


def test_known_gestures_rejects_a_gesture_the_recognizer_does_not_emit():
    with pytest.raises(InvalidProfileError, match="does not emit"):
        profile_from_mapping(GOOD, known_gestures=["swipe_right", "swipe_left"])


def test_known_gestures_accepts_any_collection_type():
    for known in (
        ("swipe_right",),
        ["swipe_right"],
        {"swipe_right"},
        frozenset({"swipe_right"}),
    ):
        data = good(bindings={"swipe_right": "next"})
        assert profile_from_mapping(data, known_gestures=known).name == "presenter"


@pytest.mark.parametrize("known", ["swipe_right", b"swipe_right"])
def test_known_gestures_given_as_a_string_is_a_programming_error(known):
    with pytest.raises(TypeError):
        profile_from_mapping(GOOD, known_gestures=known)


def test_empty_known_gestures_rejects_every_binding():
    with pytest.raises(InvalidProfileError, match="does not emit"):
        profile_from_mapping(GOOD, known_gestures=set())


# ---------------------------------------------------------------------------
# Loading from a file
# ---------------------------------------------------------------------------


def test_load_valid_file_from_a_path_or_a_string(tmp_path):
    path = write(tmp_path, json.dumps(GOOD))

    assert load_profile(path).name == "presenter"
    assert load_profile(str(path)).name == "presenter"


def test_load_passes_known_gestures_through(tmp_path):
    path = write(tmp_path, json.dumps(GOOD))

    with pytest.raises(InvalidProfileError, match="does not emit"):
        load_profile(path, known_gestures={"swipe_right"})


def test_missing_file_is_rejected(tmp_path):
    with pytest.raises(InvalidProfileError, match="cannot read"):
        load_profile(tmp_path / "nope.json")


def test_directory_is_rejected(tmp_path):
    with pytest.raises(InvalidProfileError, match="cannot read"):
        load_profile(tmp_path)


def test_path_with_a_null_byte_is_rejected():
    with pytest.raises(InvalidProfileError, match="cannot read"):
        load_profile("bad\x00name.json")


@pytest.mark.parametrize(
    "text", ["", "   ", "{", "not json", "{'version': 1}", '{"version": 1,}']
)
def test_invalid_json_is_rejected(tmp_path, text):
    with pytest.raises(InvalidProfileError, match="not valid JSON"):
        load_profile(write(tmp_path, text))


@pytest.mark.parametrize("text", ["[]", "null", "5", '"profile"', "true"])
def test_valid_json_that_is_not_an_object_is_rejected(tmp_path, text):
    with pytest.raises(InvalidProfileError, match="must be a mapping"):
        load_profile(write(tmp_path, text))


def test_non_utf8_file_is_rejected(tmp_path):
    path = tmp_path / "latin.json"
    path.write_bytes(b'{"version": 1, "name": "caf\xe9", "bindings": {}}')

    with pytest.raises(InvalidProfileError, match="not valid UTF-8"):
        load_profile(path)


def test_file_over_the_size_limit_is_rejected(tmp_path):
    padding = " " * MAX_PROFILE_BYTES
    path = write(tmp_path, json.dumps(GOOD) + padding)

    with pytest.raises(InvalidProfileError, match="larger than"):
        load_profile(path)


def test_file_at_the_size_limit_is_read(tmp_path):
    text = json.dumps(GOOD)
    path = write(tmp_path, text + " " * (MAX_PROFILE_BYTES - len(text)))

    assert path.stat().st_size == MAX_PROFILE_BYTES
    assert load_profile(path).name == "presenter"


def test_repeated_key_is_rejected_so_a_binding_cannot_hide(tmp_path):
    text = (
        '{"version": 1, "name": "dup", "bindings": '
        '{"swipe_right": "next", "swipe_right": "previous"}}'
    )

    with pytest.raises(InvalidProfileError, match="repeats a key"):
        load_profile(write(tmp_path, text))


def test_repeated_top_level_key_is_rejected(tmp_path):
    text = '{"version": 1, "name": "a", "name": "b", "bindings": {}}'

    with pytest.raises(InvalidProfileError, match="repeats a key"):
        load_profile(write(tmp_path, text))


def test_deeply_nested_file_is_rejected_without_crashing(tmp_path):
    path = write(tmp_path, "[" * 30000 + "]" * 30000)

    with pytest.raises(InvalidProfileError):
        load_profile(path)


def test_file_with_a_dangerous_binding_is_rejected(tmp_path):
    data = good(bindings={"swipe_right": "end"})

    with pytest.raises(InvalidProfileError, match="bindings rejected"):
        load_profile(write(tmp_path, json.dumps(data)))


def test_error_text_quotes_only_a_short_piece_of_a_rejected_value(tmp_path):
    long_value = "SECRET-" + "x" * 200
    data = {"version": 1, "name": "ok", "bindings": {long_value: "next"}}

    with pytest.raises(InvalidProfileError) as caught:
        load_profile(write(tmp_path, json.dumps(data)))

    message = str(caught.value)
    assert "SECRET-" in message
    assert long_value not in message
    assert len(message) < 200
