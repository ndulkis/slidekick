"""Read-only, controlled directory of validated v1 gesture profiles."""

from pathlib import Path

from .gesture_profile import GestureProfile, InvalidProfileError, load_profile


class ProfileStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def list_profiles(self) -> list[GestureProfile]:
        profiles = []
        if not self.directory.is_dir():
            return profiles
        for path in sorted(self.directory.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                profile = load_profile(
                    path, known_gestures={"swipe_left", "swipe_right"}
                )
            except InvalidProfileError:
                continue  # Corrupt files cannot become active.
            if profile.name not in {entry.name for entry in profiles}:
                profiles.append(profile)
        return profiles

    def get(self, name: str) -> GestureProfile | None:
        # Only compare validated names: never derive paths from user input.
        return next((p for p in self.list_profiles() if p.name == name), None)
