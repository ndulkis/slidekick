"""The dashboard in a native macOS window, so the Dock shows SlideKick's icon
instead of Chrome's. app.py runs this as its own process:

    python -m slidekick.dashboard_window URL

The process exits when the window is closed.
"""

import sys
from pathlib import Path

import webview
from AppKit import NSApplication, NSBundle, NSImage
from Foundation import NSActivityUserInitiatedAllowingIdleSystemSleep, NSProcessInfo

ICON = Path(__file__).resolve().parents[2] / "assets/app-icon/SlideKick.icns"


def main(url: str) -> None:
    # app.py normally runs this from a SlideKick.app bundle, which already
    # gives it the name and icon. These cover a Python it cannot bundle.
    info = NSBundle.mainBundle().infoDictionary()
    if info is not None:
        info["CFBundleName"] = "SlideKick"

    image = NSImage.alloc().initWithContentsOfFile_(str(ICON))
    if image is not None:
        NSApplication.sharedApplication().setApplicationIconImage_(image)

    # Keep the dashboard fully alive while it is hidden behind the slideshow
    # (no App Nap). The returned token must stay referenced.
    activity = NSProcessInfo.processInfo().beginActivityWithOptions_reason_(
        NSActivityUserInitiatedAllowingIdleSystemSleep, "SlideKick dashboard"
    )

    webview.create_window("SlideKick", url, width=1100, height=850)
    webview.start()
    del activity


if __name__ == "__main__":
    main(sys.argv[1])
