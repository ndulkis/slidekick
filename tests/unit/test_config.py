import pytest

from slidekick.config import ROOT, ConfigError, detect_platform, load_settings


def load(environ=None, env_file=None, platform="darwin"):
    return load_settings(
        environ=environ or {},
        env_file=env_file or ROOT / "does-not-exist.env",
        platform=platform,
    )


@pytest.mark.parametrize(
    ("platform", "expected"),
    [("darwin", "macos"), ("win32", "windows"), ("linux", "linux")],
)
def test_detect_platform(platform, expected):
    assert detect_platform(platform) == expected


@pytest.mark.parametrize(
    ("platform", "backend"),
    [("darwin", "avfoundation"), ("win32", "msmf"), ("linux", "v4l2")],
)
def test_camera_backend_defaults_to_the_os_backend(platform, backend):
    assert load(platform=platform).camera_backend == backend


def test_defaults():
    settings = load()
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.camera_index == 0
    assert settings.model_path == ROOT / "models" / "gesture_recognizer.task"


def test_env_file_overrides_defaults(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\n\nSLIDEKICK_CAMERA_INDEX=2\nSLIDEKICK_LOG_LEVEL='DEBUG'\n"
    )
    settings = load(env_file=env_file)
    assert settings.camera_index == 2
    assert settings.log_level == "DEBUG"


def test_environment_variables_override_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SLIDEKICK_CAMERA_INDEX=2\n")
    settings = load({"SLIDEKICK_CAMERA_INDEX": "1"}, env_file=env_file)
    assert settings.camera_index == 1


def test_windows_accepts_dshow():
    assert (
        load({"SLIDEKICK_CAMERA_BACKEND": "dshow"}, platform="win32").camera_backend
        == "dshow"
    )


def test_backend_from_another_os_is_rejected():
    with pytest.raises(ConfigError, match="SLIDEKICK_CAMERA_BACKEND"):
        load({"SLIDEKICK_CAMERA_BACKEND": "avfoundation"}, platform="win32")


def test_every_invalid_setting_is_reported_at_once():
    with pytest.raises(ConfigError) as error:
        load({"SLIDEKICK_LOG_LEVEL": "LOUD", "SLIDEKICK_CAMERA_INDEX": "front"})
    assert "SLIDEKICK_LOG_LEVEL" in str(error.value)
    assert "SLIDEKICK_CAMERA_INDEX" in str(error.value)
